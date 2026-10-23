#!/usr/bin/env python3
"""Query-paired uncertainty and exposure diagnostics for frozen predictions."""
import collections,json
import numpy as np
from run import OUT,VARIANTS,read,write,jsonl

def load_rows(p):return [json.loads(l)for l in p.read_text().splitlines()]
def main():
    bootstrap_ids=np.random.default_rng(12).integers(0,100,size=(10000,100));methods=list(VARIANTS);results={};paired={};coverage={};admission={}
    for suite in ['main','single_matched','single_supplied','benign_echo','benign_mirror']:
        rows=load_rows(OUT/f'predictions_{suite}.jsonl');results[suite]={};paired[suite]={}
        for setting in sorted({r['setting']for r in rows}):
            rr=[r for r in rows if r['setting']==setting];qids=sorted({r['qid']for r in rr});qgroup={q:[r for r in rr if r['qid']==q]for q in qids}
            tp=np.array([[sum(r['label']and r['blocked'][m]for r in qgroup[q])for m in methods]for q in qids]);fp=np.array([[sum(not r['label']and r['blocked'][m]for r in qgroup[q])for m in methods]for q in qids]);pos=np.array([sum(r['label']for r in qgroup[q])for q in qids]);neg=20-pos
            control_counts=np.array([sum(r['family'].startswith('benign_')for r in qgroup[q])for q in qids]);control_fp=np.array([[sum(r['family'].startswith('benign_')and r['blocked'][m]for r in qgroup[q])for m in methods]for q in qids])
            assert len(qids)==100
            ids=bootstrap_ids;tpb=tp[ids].sum(1);fpb=fp[ids].sum(1);posb=pos[ids].sum(1);negb=neg[ids].sum(1)
            rec=tpb/np.maximum(1,posb[:,None]);fpr=fpb/negb[:,None];results[suite][setting]={}
            for mi,m in enumerate(methods):
                d={'recall_ci95':np.quantile(rec[:,mi],[.025,.975]).tolist()if pos.sum()else None,'fpr_ci95':np.quantile(fpr[:,mi],[.025,.975]).tolist()}
                if control_counts.sum():
                    cfp=control_fp[ids].sum(1)/control_counts[ids].sum(1)[:,None];d['modified_control_fpr_ci95']=np.quantile(cfp[:,mi],[.025,.975]).tolist()
                results[suite][setting][m]=d
            paired[suite][setting]={}
            for a,b in [('fused','ctx'),('aug_fused','fused'),('fused','content'),('fused','no_guard')]:
                ai,bi=methods.index(a),methods.index(b)
                paired[suite][setting][a+'_minus_'+b]={'recall_delta_ci95':np.quantile(rec[:,ai]-rec[:,bi],[.025,.975]).tolist()if pos.sum()else None,'fpr_delta_ci95':np.quantile(fpr[:,ai]-fpr[:,bi],[.025,.975]).tolist()}
                if control_counts.sum():paired[suite][setting][a+'_minus_'+b]['modified_control_fpr_delta_ci95']=np.quantile(cfp[:,ai]-cfp[:,bi],[.025,.975]).tolist()
    write(OUT/'bootstrap.json',{'unit':'Whole query with every candidate and paired method;10000 percentile replicates,seed12,same sorted-QID resamples across suites/settings,conditional on authored families and fixed fitted fold heads','intervals':results,'paired':paired})
    # Report how many of each family's constructed attacks enter the candidate
    # pool, rather than calling non-retrieved attacks detector false negatives.
    for suite in ['main','single_matched','single_supplied']:
        pools=load_rows(OUT/f'pools_{suite}.jsonl');coverage[suite]={}
        for setting in sorted({r['setting']for r in pools}):
            rr=[r for r in pools if r['setting']==setting];coverage[suite][setting]={'queries':len(rr),'adv_in_pool':sum(sum(p['label']for p in r['pool'])for r in rr),'mean_adv_at_5':float(np.mean([sum(p['label']for p in r['pool'][:5])for r in rr]))}
    write(OUT/'retrieval_exposure.json',coverage)
    for suite in ['main','single_matched','single_supplied','benign_echo','benign_mirror']:
        rows=load_rows(OUT/f'predictions_{suite}.jsonl');admission[suite]={}
        for setting in sorted({r['setting']for r in rows}):
            rr=[r for r in rows if r['setting']==setting];qids=sorted({r['qid']for r in rr});byq={q:sorted([r for r in rr if r['qid']==q],key=lambda r:r['index'])for q in qids}
            gates=['none']+methods+['oracle'];counts=np.zeros((100,len(gates)));filled=np.zeros_like(counts)
            for qi,q in enumerate(qids):
                for gi,g in enumerate(gates):
                    selected=[r for r in byq[q]if (r['label']==0 if g=='oracle'else True if g=='none'else not r['blocked'][g])][:5]
                    counts[qi,gi]=sum(r['label']for r in selected);filled[qi,gi]=len(selected)
            any_adv=(counts>0).astype(float);bs=any_adv[bootstrap_ids].mean(1);cnt_bs=counts[bootstrap_ids].mean(1)
            d={}
            for gi,g in enumerate(gates):
                d[g]={'queries':100,'attack_admitted_queries':int(any_adv[:,gi].sum()),'query_attack_admission_rate':float(any_adv[:,gi].mean()),'query_attack_admission_ci95':np.quantile(bs[:,gi],[.025,.975]).tolist(),'mean_adversarial_contexts':float(counts[:,gi].mean()),'mean_adversarial_contexts_ci95':np.quantile(cnt_bs[:,gi],[.025,.975]).tolist(),'malicious_slot_fraction_denom_500':float(counts[:,gi].sum()/500),'mean_filled_contexts':float(filled[:,gi].mean()),'empty_query_contexts':int((filled[:,gi]==0).sum())}
            d['paired_differences']={}
            for a,b in [('fused','ctx'),('aug_fused','fused'),('fused','content'),('fused','no_guard')]:
                ai,bi=gates.index(a),gates.index(b);d['paired_differences'][a+'_minus_'+b]={'query_admission_delta':float(any_adv[:,ai].mean()-any_adv[:,bi].mean()),'query_admission_delta_ci95':np.quantile(bs[:,ai]-bs[:,bi],[.025,.975]).tolist(),'mean_adv_contexts_delta':float(counts[:,ai].mean()-counts[:,bi].mean()),'mean_adv_contexts_delta_ci95':np.quantile(cnt_bs[:,ai]-cnt_bs[:,bi],[.025,.975]).tolist()}
            admission[suite][setting]=d
    write(OUT/'policy_admission.json',{'unit':'100 queries per setting; query attack admission=at least1 malicious selected context. Mean adversarial contexts denominator100; slot fraction denominator500capacity even if fewer than5 accepted. All paired intervals reuse seed12/10000 whole-QID draws. This measures exposure, not generator ASR.','suites':admission})
    # Record the few cross-question source-document overlaps; never claim
    # document-disjoint evaluation when only questions were grouped.
    base=load_rows(OUT/'pools_main.jsonl');fold=read(OUT/'protocol.json')['fold_assignment'];seen=collections.defaultdict(set)
    for r in base:
        if r['setting']!='none':continue
        for p in r['pool']:seen[p['id']].add(r['qid'])
    overlap={doc:sorted(qs)for doc,qs in seen.items()if len({fold[q]for q in qs})>1}
    write(OUT/'document_overlap.json',{'cross_fold_document_ids':overlap,'affected_questions':sorted({q for qs in overlap.values()for q in qs}),'scope':'Question-disjoint cross-validation, not strict document/topic holdout.'})
    print('Pairedbootstrap, candidate exposure and overlap audits written.')
if __name__=='__main__':main()
