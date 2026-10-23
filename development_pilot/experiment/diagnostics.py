#!/usr/bin/env python3
"""Post-hoc descriptive diagnostics; primary thresholds are never changed.

These were requested after observing the primary held-out result. A fixed .5
cutoff is a reference point, not a replacement operating point selected on test.
Feature ablation holds the trained fusion model and threshold fixed.
"""
import json
import numpy as np
from scipy.special import expit,logit
from sklearn.metrics import roc_curve,roc_auc_score
from benchmark import HERE,OUT,metrics

def main():
    summary=json.loads((OUT/'results.json').read_text());rows=[json.loads(x) for x in (OUT/'predictions.jsonl').read_text().splitlines()]
    train=[r for r in rows if r['split']=='train'];mean_neural=float(np.mean([r['scores']['neural'] for r in train]));b=summary['fusion']['intercept'];w=summary['fusion']['weights'];t=summary['thresholds']['combined']
    out={'scope':'Post-hoc descriptive diagnostics after primary held-out results were observed. Original thresholds/model/data remain unchanged; no test-selected operating point.','fixed_reference_threshold':.5,'ablation':'Hold neural risk at training-mean while retaining fitted fusion weights and development threshold; no refit or retune.','training_mean_neural_risk':mean_neural,'splits':{}}
    dispersion={}
    for split in ['train','dev','test_joint']:
        dispersion[split]={}
        for feature in ['neural','retrieval']:
            z=np.array([r['scores'][feature] for r in rows if r['split']==split])
            dispersion[split][feature]={'mean':float(z.mean()),'std':float(z.std()),'min':float(z.min()),'max':float(z.max())}
    (OUT/'feature_dispersion.json').write_text(json.dumps(dispersion,indent=2))
    for split in ['dev','test_topic','test_joint','test_poison']:
        rr=[r for r in rows if r['split']==split];s=np.array([r['scores']['neural'] for r in rr]);original=np.array([r['blocked']['combined']for r in rr])
        ablated=expit(b+w[0]*mean_neural+w[1]*np.array([r['scores']['retrieval'] for r in rr]))
        d={'neural_fixed_0_5':metrics(rr,s,s>=.5),'neural_constant_ablation_combined':metrics(rr,ablated,ablated>=t),'ablation_decision_changes':int(((ablated>=t)!=original).sum()),'neural_risk_by_kind':{}}
        for kind in ['attack','quotation','manual','answer','minority']:
            z=s[np.array([r['kind']==kind for r in rr])]
            d['neural_risk_by_kind'][kind]={'n':len(z),'min':float(z.min()),'p05':float(np.quantile(z,.05)),'median':float(np.median(z)),'p95':float(np.quantile(z,.95)),'max':float(z.max())}
        out['splits'][split]=d
    public=OUT/'public_predictions.jsonl'
    if public.exists():
        pr=[json.loads(x)for x in public.read_text().splitlines()];out['public_fixed_0_5']={}
        for name in ['NotInject','BIPIA']:
            rr=[r for r in pr if r['dataset']==name]
            out['public_fixed_0_5'][name]={'n':len(rr),'blocked':sum(r['scores']['neural']>=.5 for r in rr),'rate':float(np.mean([r['scores']['neural']>=.5 for r in rr])),'metric':'benign FPR' if name=='NotInject' else 'standalone attack-payload detection rate'}
    (OUT/'diagnostics.json').write_text(json.dumps(out,indent=2))
    make_figures(rows,summary)
    print(json.dumps(out,indent=2))

def make_figures(rows,summary):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(1,2,figsize=(9,3.6),layout='constrained')
    for ax,split,title in zip(axs,['dev','test_joint'],['Development','Joint topic + family shift']):
        rr=[r for r in rows if r['split']==split];y=np.array([r['label'] for r in rr]);s=np.array([r['scores']['neural'] for r in rr]);fpr,tpr,_=roc_curve(y,s)
        ax.plot(fpr,tpr,color='#456C9A',lw=2,label=f'Neural AUROC {roc_auc_score(y,s):.3f}')
        ax.plot([0,1],[0,1],color='#D3D5D7',ls='--');ax.scatter([0],[0],color='#C66A47',s=55,label='Dev-selected: reject none',zorder=5)
        ax.scatter([float((s[y==0]>=.5).mean())],[float((s[y==1]>=.5).mean())],marker='x',color='#5E8C61',s=65,label='Fixed 0.5 reference',zorder=5)
        ax.axvline(.05,color='#A7A9AC',ls=':',label='5% dev FPR budget');ax.set(xlim=(-.02,1.02),ylim=(-.02,1.02),xlabel='Benign false-positive rate',ylabel='Attack passage recall',title=title);ax.legend(fontsize=7,loc='lower right',frameon=False);ax.spines[['top','right']].set_visible(False)
    fig.savefig(OUT/'neural_roc_diagnostic.png',dpi=200);fig.savefig(OUT/'neural_roc_diagnostic.svg');plt.close(fig)
    rr=[r for r in rows if r['split']=='test_joint'];fig,ax=plt.subplots(figsize=(7,3.8),layout='constrained')
    colors={'attack':'#C66A47','quotation':'#9862A2','manual':'#64A5A2','answer':'#456C9A','minority':'#A9AD6C'}
    for kind,color in colors.items():
        risks=np.array([r['scores']['neural'] for r in rr if r['kind']==kind]);z=logit(np.clip(risks,1e-7,1-1e-7));ax.hist(z,bins=18,density=True,histtype='step',lw=1.6,label=kind,color=color)
    ax.set(xlabel='Logit of neural injection risk (raw scores saturate near 1)',ylabel='Density',title='Joint-shift score overlap by passage kind');ax.legend(frameon=False);ax.spines[['top','right']].set_visible(False)
    fig.savefig(OUT/'neural_score_overlap.png',dpi=200);fig.savefig(OUT/'neural_score_overlap.svg');plt.close(fig)
if __name__=='__main__':main()
