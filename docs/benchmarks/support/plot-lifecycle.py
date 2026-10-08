"""Render the published lifecycle facts; optional reporting dependency: matplotlib."""
import argparse
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('facts', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    facts = json.loads(args.facts.read_text(encoding='utf-8'))
    colors = {'plain': '#64748b', 'project': '#2563eb', 'tack': '#0d9488'}
    labels = {'plain': 'Plain', 'project': 'Short guide', 'tack': 'Tack'}
    groups = [(model, condition) for model in ('gpt-6-luna', 'gpt-6.1-sol')
              for condition in ('plain', 'project', 'tack')]
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.6), sharey=True)
    fig.patch.set_facecolor('#ffffff')
    for index, (model, condition) in enumerate(groups):
        rows = [r for r in facts['journeys'] if (r['model'], r['condition']) == (model, condition)]
        assert len(rows) == 4
        ids = {r['id'] for r in rows}
        times = [r['seconds'] / 60 for r in rows]
        scores = [r['weighted'] for r in facts['reviews']
                  if r['case'] in ids and r['phase'] == 'final' and not r['reversed']]
        assert len(scores) == 4
        for axis, values in zip(axes, (times, scores)):
            mean = statistics.mean(values)
            axis.barh(index, mean, color=colors[condition], height=0.57, alpha=0.85)
            axis.scatter(values, [index - 0.18 + i * 0.12 for i in range(4)],
                         color='#0f172a', edgecolors='white', linewidths=0.6, s=28, zorder=3)
            axis.text(11.1, index, f'{mean:.2f}', va='center', ha='right', fontsize=9)
    for axis in axes:
        axis.set_axisbelow(True)
        axis.grid(axis='x', color='#e2e8f0', linewidth=0.7)
        axis.axhline(2.5, color='#cbd5e1', linewidth=0.8)
        for spine in axis.spines.values():
            spine.set_visible(False)
        axis.tick_params(axis='both', length=0, labelsize=9)
        axis.set_xlim(0, 11.2)
    axes[0].set_yticks(range(6), [f'{"Luna" if "luna" in m else "Sol"} / {labels[c]}' for m, c in groups])
    axes[0].invert_yaxis()
    axes[0].set_title('Mean journey time, minutes', loc='left', fontsize=12, pad=15)
    axes[0].set_xlabel('Includes setup, changes, review and repairs; lower is better', fontsize=9)
    axes[1].set_title('Mean final code-quality score, out of 10', loc='left', fontsize=12, pad=15)
    axes[1].set_xticks([0, 2, 4, 6, 8, 10])
    axes[1].set_xlabel('Independent primary reviews; higher is better', fontsize=9)
    fig.suptitle('More time, no consistent quality gain over a short guide',
                 fontsize=15, fontweight='bold', x=0.04, ha='left')
    fig.text(0.04, 0.06, 'Bars: means. Dots: all four journeys per model/condition. Failed attempts remain included.\n'
             'Final acceptance: plain 7/8, guide 8/8, tack 8/8. Supplemental defects remain; small synthetic sample.',
             fontsize=9, color='#475569')
    fig.subplots_adjust(left=0.16, right=0.97, top=0.82, bottom=0.21, wspace=0.18)
    fig.savefig(args.output, dpi=170, facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    main()
