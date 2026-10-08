#!/usr/bin/env python3
"""Post-hoc Unicode probe on completed search artifacts; never changes acceptance metrics.

Usage: python3 probe-codex-search.py BATCH_DIRECTORY OUTPUT.json
"""
import importlib.util
import json
from pathlib import Path
import sys


def probe(root):
    sys.dont_write_bytecode = True
    rows = []
    for path in sorted(root.rglob("metrics.json")):
        metrics = json.loads(path.read_text(encoding="utf-8"))
        if metrics["scenario"] != "search":
            continue
        spec = importlib.util.spec_from_file_location("shop_probe", path.parent / "repo/src/shop/__init__.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        connection = module.connect()
        try:
            module.add_product(connection, "CAFÉ", 2)
            module.add_product(connection, "Straße", 3)
            rows.append({"run": metrics["metadata"]["run_id"],
                         "cafe": module.search_products(connection, "café"),
                         "strasse": module.search_products(connection, "STRASSE")})
        finally:
            connection.close()
    return {"scope": "Post-hoc Unicode probe; separate from frozen hidden acceptance tests.", "runs": rows}


if __name__ == "__main__":
    source, output = map(Path, sys.argv[1:3])
    output.write_text(json.dumps(probe(source), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
