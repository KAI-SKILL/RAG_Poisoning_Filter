#!/usr/bin/env python3
"""Derived precision/F1 counts only; does not change frozen model results."""
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent.parent/'output'/'improved_experiment'
def main():
    s=json.loads((OUT/'results.json').read_text());out={}
    for suite,settings in s.items():
        out[suite]={}
        for setting,methods in settings.items():
            out[suite][setting]={}
            for method,m in methods.items():
                tp,fp=m['tp'],m['fp'];fn=m['malicious_n']-tp
                out[suite][setting][method]={'precision':tp/(tp+fp)if tp+fp else None,'precision_denominator_alerts':tp+fp,'recall_denominator_retrieved_attacks':m['malicious_n'],'f1':2*tp/(2*tp+fp+fn)if m['malicious_n']else None,'attack_prevalence':m['malicious_n']/m['n']}
    d={'scope':'Pure arithmetic from frozen confusion counts; no model/threshold/prediction changes. Precision is undefined with no alerts; F1 is not reported for all-benign conditions. Precision and AUPRC depend on the authored attack prevalence.','metrics':out}
    (OUT/'precision_metrics.json').write_text(json.dumps(d,indent=2));print('Derivedprecision/F1saved;frozenresultsunchanged.')
if __name__=='__main__':main()
