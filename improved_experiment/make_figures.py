#!/usr/bin/env python3
"""Render measured fresh results, keeping passage exposure distinct from ASR."""
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from run import OUT,read

def heatmap(ax,data,rows,cols,title):
    im=ax.imshow(data,cmap='YlOrRd',vmin=0,vmax=100,aspect='auto')
    ax.set_xticks(range(len(cols)),cols);ax.set_yticks(range(len(rows)),rows);ax.set_title(title)
    for i in range(len(rows)):
        for j in range(len(cols)):ax.text(j,i,f'{data[i,j]:.1f}',ha='center',va='center',color='white'if data[i,j]>65 else '#28333F',fontsize=10)
    ax.spines[:].set_visible(False);return im

def save(fig,name):fig.savefig(OUT/(name+'.png'),dpi=220,bbox_inches='tight');fig.savefig(OUT/(name+'.svg'),bbox_inches='tight');plt.close(fig)
def main():
    metrics=read(OUT/'results.json');policies=read(OUT/'policy_admission.json')['suites'];methods=['none','rule','guard','ctx','fused','aug_fused','oracle'];labels=['No filter','Rules','Guard','Context','Fusion','Aug. fusion','Corruption removal'];families=['poison','ignore','stealth']
    fig,ax=plt.subplots(figsize=(6.8,4.3),layout='constrained');matrix=np.array([[100*policies['main'][f][m]['query_attack_admission_rate']for f in families]for m in methods]);im=heatmap(ax,matrix,labels,['Factual poison','Ignore injection','Held-out stealth'],'Queries admitting ≥1 adversarial context (%)\nPassage exposure before generation; 100 queries per setting');fig.colorbar(im,ax=ax,label='% queries');save(fig,'main_attack_admission')
    fig,axs=plt.subplots(1,2,figsize=(10,4.1),layout='constrained')
    for ax,suite,title in zip(axs,['main','single_matched'],['Five attack records','One strongest same-set attack']):
        matrix=np.array([[100*policies[suite][f][m]['query_attack_admission_rate']for f in families]for m in methods]);im=heatmap(ax,matrix,labels,families,title)
    fig.suptitle('Frozen five-attack heads under an attack-count shift (exposure, not ASR)');fig.colorbar(im,ax=axs,label='% queries');save(fig,'count_transfer')
    chosen=['rule','guard','ctx','fused','aug_fused'];names=['Rules','Guard','Context','Fusion','Aug. fusion'];conditions=[('main','none','fpr','Ordinary clean pool'),('benign_echo','benign_echo','benign_control_fpr','Question echo: modified records'),('benign_mirror','benign_mirror','benign_control_fpr','Mirrors: copied records')]
    fig,ax=plt.subplots(figsize=(8,4.1),layout='constrained');x=np.arange(len(chosen));width=.24;colors=['#A7A9AC','#456C9A','#C66A47'];maximum=0
    for j,(suite,setting,key,label)in enumerate(conditions):
        vals=np.array([100*metrics[suite][setting][m][key]for m in chosen]);maximum=max(maximum,vals.max());bars=ax.bar(x+(j-1)*width,vals,width,label=label,color=colors[j])
        for b,v in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,v+.7,f'{v:.1f}',ha='center',fontsize=7)
    ax.axhline(5,ls=':',color='#656C75',lw=1,label='5% clean validation budget');ax.set_xticks(x,names);ax.set_ylim(0,min(105,max(15,maximum*1.18)));ax.set_ylabel('Benign false-positive rate (%)');ax.set_title('Specificity under fact-preserving benign stress controls');ax.legend(fontsize=7,frameon=False,loc='upper left');ax.spines[['top','right']].set_visible(False);save(fig,'benign_controls')
    ablations=['score','density','ctx','content','no_guard','fused','aug_fused'];fig,ax=plt.subplots(figsize=(6,3.8),layout='constrained');matrix=np.array([[100*metrics['main'][f][m]['recall']for f in families]for m in ablations]);im=heatmap(ax,matrix,['Score only','Density only','Context','Guard + rules','Rules + context','Fusion','Aug. fusion'],families,'Recall among retrieved adversarial passages (%)\nThresholds calibrated on clean validation questions');fig.colorbar(im,ax=ax,label='% blocked');save(fig,'signal_ablation')
if __name__=='__main__':main()
