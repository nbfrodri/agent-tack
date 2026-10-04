#!/usr/bin/env python3
"""Reports over the activity log for `tack log --cost|--skills|--levels`.

Usage: log-report.py KIND LOG DAYS CSV PRICING REPO

KIND is cost, skills or levels; DAYS limits the report to the last N days; CSV is 1 for
comma-separated output; PRICING is the user's optional price file ("model | input | output |
cache read | cache write", USD per million tokens); REPO lists the shipped skills and agents.
Log lines are "time<TAB>tool<TAB>project<TAB>event<TAB>detail" (hooks/claude/lib/activity-log.sh).
"""
import csv
import datetime
import os
import sys


HOME = os.path.expanduser("~")


def project_name(path):
    """The project's path, shortened under the home folder; two repos named alike stay apart."""
    path = path.rstrip("/") or path
    return "~" + path[len(HOME):] if HOME != "/" and (path == HOME or path.startswith(HOME + "/")) else path


def entries(path, days):
    since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    first = None
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 5:
                continue
            try:
                when = datetime.datetime.strptime(parts[0], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
            except ValueError:
                continue
            first = when if first is None else min(first, when)
            if when >= since:
                yield when, parts[1], project_name(parts[2]), parts[3], parts[4]
    # The log keeps only its newest lines; say so when the period reaches past them.
    if first and first > since:
        print(f"The log only goes back to {first.date().isoformat()}; older entries were rotated out.",
              file=sys.stderr)


def prices(path):
    table = {}
    if not os.path.isfile(path):
        return table
    for line in open(path, encoding="utf-8", errors="replace"):
        fields = [field.strip() for field in line.split("|")]
        if len(fields) != 5 or fields[0].startswith("#"):
            continue
        try:
            table[fields[0]] = [float(value) for value in fields[1:]]
        except ValueError:
            continue
    return table


def table(rows, header):
    widths = [max(len(str(row[i])) for row in [header] + rows) for i in range(len(header))]
    for row in [header] + rows:
        print("  ".join(str(cell).ljust(width) for cell, width in zip(row, widths)).rstrip())


def cost(log, days, as_csv, pricing):
    totals = {}
    for when, tool, project, event, detail in entries(log, days):
        if event != "turn" or detail == "unknown":
            continue
        fields = dict(item.split("=", 1) for item in detail.split() if "=" in item)
        key = (when.date().isoformat(), project, tool, fields.get("model", "unknown"))
        sums = totals.setdefault(key, [0, 0, 0, 0])
        for i, name in enumerate(("input", "output", "cache_read", "cache_write")):
            try:
                sums[i] += int(fields.get(name, 0))
            except ValueError:
                pass
    rates = prices(pricing)
    rows = []
    for key in sorted(totals):
        sums = totals[key]
        rate = rates.get(key[3])
        usd = "%.2f" % (sum(count * price for count, price in zip(sums, rate)) / 1_000_000) if rate else "-"
        rows.append(list(key) + sums + [usd])
    header = ["day_utc", "project", "tool", "model", "input", "output", "cache_read", "cache_write", "usd"]
    if as_csv:
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    elif rows:
        table(rows, header)
        if not rates:
            print("\nAmounts in USD need your prices in ~/.config/agent-tack/pricing.txt (see docs/usage.md).")
    else:
        print("No turns recorded in this period.")


def skills(log, days, as_csv, repo):
    counts = {}
    for _, _, _, event, detail in entries(log, days):
        if event in ("skill", "agent"):
            counts[(event, detail)] = counts.get((event, detail), 0) + 1
    rows = [[kind, name, count] for (kind, name), count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]
    if as_csv:
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["kind", "name", "uses"])
        writer.writerows(rows)
        return
    if rows:
        table(rows, ["kind", "name", "uses"])
    shipped = sorted(entry for entry in os.listdir(os.path.join(repo, "skills"))
                     if os.path.isfile(os.path.join(repo, "skills", entry, "SKILL.md")))
    agents = sorted(entry[:-3] for entry in os.listdir(os.path.join(repo, "agents")) if entry.endswith(".md"))
    unused = [name for name in shipped if ("skill", name) not in counts]
    unused += [name for name in agents if ("agent", name) not in counts]
    print("\nNever used in the period: " + (", ".join(unused) if unused else "none"))


def levels(log, days, as_csv):
    counts = {}
    for _, _, project, event, detail in entries(log, days):
        if event == "level":
            level = detail.split()[0] if detail else "missing"
            counts[(project, level)] = counts.get((project, level), 0) + 1
    rows = [[project, level, count] for (project, level), count in sorted(counts.items())]
    if as_csv:
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["project", "level", "turns"])
        writer.writerows(rows)
    elif rows:
        table(rows, ["project", "level", "turns"])
    else:
        print("No levels recorded in this period.")


def main(kind, log, days, as_csv, pricing, repo):
    days, as_csv = int(days), as_csv == "1"
    if kind == "cost":
        cost(log, days, as_csv, pricing)
    elif kind == "skills":
        skills(log, days, as_csv, repo)
    else:
        levels(log, days, as_csv)


if __name__ == "__main__":
    main(*sys.argv[1:7])
