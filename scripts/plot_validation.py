#!/usr/bin/env python3
"""Reproduce an aggregate validation figure without loading reference coordinates."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[1]
report = json.loads((ROOT / 'docs/validation_summary.json').read_text())
rows = [r for r in report['metrics'] if r['universe'] == 'comparable_geology']
styles = {
    'geology': ('Geology', '#777777', 'o'),
    'terrain': ('Terrain', '#b39b2e', 's'),
    'landscape_v001': ('Landscape v001', '#388e5a', '^'),
    'morphology': ('Surface morphology', '#be5d34', 'D'),
    'combined_v002': ('Combined v002', '#356aab', 'P'),
}
fig, axes = plt.subplots(1, 2, figsize=(12, 6))
fig.subplots_adjust(top=.85, bottom=.28, left=.07, right=.98, wspace=.17)
for key, (label, color, marker) in styles.items():
    model = [r for r in rows if r['model'] == key]
    x = [r['actual_area_fraction'] for r in model]
    for ax, metric in zip(axes, ['central_reference_fraction_selected',
                               'mean_uncertainty_region_coverage']):
        ax.plot(x, [r[metric] for r in model], label=label,
                color=color, marker=marker, linewidth=1.8)
for ax, title in zip(axes, [f"Public map points selected (n = {report['reference_count']})",
                           'Mean coverage of assumed 100 m regions']):
    ax.set(title=title, xlabel='Fraction of comparable geological area selected',
           xlim=(0, .21), ylim=(-.03, 1.03))
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.grid(alpha=.2)
axes[0].set_ylabel('Exploratory coverage')
fig.suptitle('Frozen blind predictions: public-reference comparison', fontsize=15, y=.96)
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(.5, .12), ncol=5, frameon=False)
area = rows[0]['universe_area_km2']
fig.text(.5, .045, 'Unknown reference accuracy • one mapper • 100 m is a scenario, not a confidence interval\n'
         f'10 m geological support: {area:.4f} km² • No established entrance-localization skill',
         fontsize=10, ha='center', va='bottom')
out = ROOT / 'docs/validation/coverage.png'
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=180)
plt.close(fig)
print(out.relative_to(ROOT))
