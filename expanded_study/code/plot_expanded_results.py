"""Plot frozen insertion-set summaries; no experiment or model is rerun."""
from pathlib import Path
import argparse, csv, hashlib, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

FAMILIES = [
 ('direct_override', 'Direct override'),
 ('authority_spoof', 'Authority spoof'),
 ('boundary_spoof', 'Boundary spoof'),
 ('fake_completion', 'Fake completion'),
 ('task_aligned_persuasion', 'Task persuasion'),
 ('fewshot_demo', 'Few-shot demo'),
 ('quoted_instruction_laundering', 'Quoted handoff'),
 ('output_format_hijack', 'Format hijack'),
 ('abstention_induction', 'Abstention induction'),
 ('factual_answer_substitution', 'Factual substitution'),
 ('citation_attribution_forgery', 'Citation forgery'),
 ('multipassage_corroboration', 'Multi-passage'),
]
MODELS = [('LR', '#0072B2', 'o', -.14), ('LinearSVC', '#D55E00', 's', .14)]
POINT = 'new_normal_1pct'


def main():
 parser = argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
 args = parser.parse_args()
 root = args.root.resolve()
 summary_path = root/'results/classification_summary.json'
 source_hash = hashlib.sha256(summary_path.read_bytes()).hexdigest()
 summary = json.loads(summary_path.read_text())
 selected = [r for r in summary if r['level'] == 'insertion_set' and r['operating_point'] == POINT and r['cohort'].startswith('family_id:')]
 lookup = {(r['cohort'].split(':', 1)[1], r['model']): r for r in selected}
 assert len(lookup) == len(selected) == 24
 assert {r['cohort'].split(':', 1)[1] for r in selected} == {f for f, _ in FAMILIES}
 records = []
 for fid, label in FAMILIES:
  for model, color, marker, offset in MODELS:
   r = lookup[fid, model]
   assert r['malicious_or_joint_attack_sets'] == r['benign'] == 2400
   assert r['n'] == 4800 and r['tp'] + r['fn'] == 2400 and r['fp'] + r['tn'] == 2400
   assert abs(r['recall'] - r['tp']/2400) < 1e-12
   assert abs(r['fpr'] - r['fp']/2400) < 1e-12
   rec_ci = r['recall_uncertainty']['ci95_article_percentile']
   fpr_ci = r['fpr_uncertainty']['ci95_article_percentile']
   assert rec_ci[0] <= r['recall'] <= rec_ci[1]
   assert fpr_ci[0] <= r['fpr'] <= fpr_ci[1]
   records.append({'family_id': fid, 'family_label': label, 'model': model, 'operating_point': POINT, 'level': 'insertion_set', 'threshold': r['threshold'], 'n': r['n'], 'attack_sets': r['malicious_or_joint_attack_sets'], 'benign_controls': r['benign'], 'article_groups': r['articles'], 'tp': r['tp'], 'fp': r['fp'], 'tn': r['tn'], 'fn': r['fn'], 'attack_recall': r['recall'], 'paired_control_fpr': r['fpr'], 'attack_recall_percent': 100*r['recall'], 'paired_control_fpr_percent': 100*r['fpr'], 'recall_ci_low_percent': 100*rec_ci[0], 'recall_ci_high_percent': 100*rec_ci[1], 'fpr_ci_low_percent': 100*fpr_ci[0], 'fpr_ci_high_percent': 100*fpr_ci[1], 'interval_scope': 'Pointwise descriptive 95% article-group bootstrap, 2000 draws; fitted models fixed', 'source_summary_sha256': source_hash})
 # Independently reconcile every integer family cell to the saved all-family row.
 for model, *_ in MODELS:
  overall = [r for r in summary if r['level']=='insertion_set' and r['cohort']=='all' and r['model']==model and r['operating_point']==POINT]
  assert len(overall) == 1
  for field in ['n', 'tp', 'fp', 'tn', 'fn']:
   assert sum(r[field] for r in records if r['model']==model) == overall[0][field], (model, field)
 out = root/'report_source/figures'
 out.mkdir(parents=True, exist_ok=True)
 stem = out/'expanded_family_tradeoff'
 with stem.with_suffix('.csv').open('w', newline='', encoding='utf-8') as stream:
  writer = csv.DictWriter(stream, fieldnames=list(records[0]))
  writer.writeheader(); writer.writerows(records)
 # Exported CSV is also the plotting source, preventing silent table/plot drift.
 with stem.with_suffix('.csv').open(newline='', encoding='utf-8') as stream:
  exported = list(csv.DictReader(stream))
 assert len(exported) == 24
 for row in exported:
  original = lookup[row['family_id'], row['model']]
  for field in ['n','tp','fp','tn','fn']:
   assert int(row[field]) == original[field]
  assert abs(float(row['attack_recall_percent']) - 100*original['recall']) < 1e-12
  assert abs(float(row['paired_control_fpr_percent']) - 100*original['fpr']) < 1e-12
 plot_data = {(r['family_id'],r['model']):r for r in exported}
 plt.rcParams.update({'font.family':'STIXGeneral', 'font.size':8, 'axes.titlesize':9, 'axes.labelsize':8, 'xtick.labelsize':7.5, 'ytick.labelsize':8, 'pdf.fonttype':42, 'ps.fonttype':42, 'axes.linewidth':0.5, 'savefig.facecolor':'white'})
 fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.85), sharey=True)
 fig.subplots_adjust(left=.225, right=.986, bottom=.145, top=.865, wspace=.16)
 y = np.arange(len(FAMILIES))
 for axis, metric, low, high, title in [
  (axes[0], 'attack_recall_percent', 'recall_ci_low_percent', 'recall_ci_high_percent', '(a) Attack recall'),
  (axes[1], 'paired_control_fpr_percent', 'fpr_ci_low_percent', 'fpr_ci_high_percent', '(b) Paired-control FPR')]:
  for i in range(len(FAMILIES)):
   if i % 2 == 0:
    axis.axhspan(i-.5, i+.5, facecolor='#F4F5F6', edgecolor='none', zorder=0)
  for model, color, marker, offset in MODELS:
   rr = [plot_data[fid, model] for fid, _ in FAMILIES]
   values = np.array([float(r[metric]) for r in rr])
   lo = np.array([float(r[low]) for r in rr]); hi = np.array([float(r[high]) for r in rr])
   axis.errorbar(values, y+offset, xerr=np.vstack([values-lo, hi-values]), fmt=marker, markersize=3.4, markeredgewidth=.35, markeredgecolor='white', color=color, ecolor=color, elinewidth=.8, capsize=1.6, capthick=.65, linestyle='none', zorder=3)
  axis.set_title(title, pad=8)
  axis.set_xlim(-1.1, 65)
  axis.set_xticks([0,15,30,45,60])
  axis.set_xlabel('Percent')
  axis.set_ylim(len(FAMILIES)-.5, -.5)
  axis.grid(axis='x', color='#D8DCE0', linewidth=.45, zorder=0)
  axis.set_axisbelow(True)
  axis.tick_params(axis='y', length=0)
  axis.tick_params(axis='x', length=2.5, width=.5)
  for spine in ['top','right','left']:
   axis.spines[spine].set_visible(False)
  axis.spines['bottom'].set_color('#7C848B')
 axes[0].set_yticks(y, [label for _, label in FAMILIES])
 axes[0].tick_params(axis='y', pad=5)
 axes[1].tick_params(axis='y', labelleft=False)
 handles=[Line2D([],[],color=color,marker=marker,linestyle='none',markersize=4,label=model) for model,color,marker,_ in MODELS]
 fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.61,.99), ncol=2, frameon=False, handletextpad=.4, columnspacing=1.4, fontsize=8)
 fig.savefig(stem.with_suffix('.pdf'), dpi=300, metadata={'Title':'Expanded controlled attack families: detection and benign rejection', 'Subject':'Frozen insertion-set detection metrics, not attack success rate', 'Keywords':source_hash})
 fig.savefig(stem.with_suffix('.png'), dpi=300)
 plt.close(fig)
 print(json.dumps({'status':'PASS_FIGURE_AND_CSV_RECONCILED', 'families':12, 'models':2, 'source_rows':24, 'counts_reconciled_to_all_family_summaries':True, 'operating_point':POINT, 'figure_inches':[7.15,3.85], 'source_summary_sha256':source_hash, 'outputs':[str(stem.with_suffix(ext))for ext in ['.pdf','.png','.csv']]},indent=2))

if __name__ == '__main__':
 main()
