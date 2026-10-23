"""Step 4 - Run the RAG pipeline (vanilla baseline or a defense) and measure the attack.

For every attack setting it builds the PoisonedRAG prompt from the (defended) top-k contexts,
queries the LLM and reports:

  ASR        % questions whose answer contains the attacker's target answer  (PoisonedRAG metric)
  Acc        % questions whose answer contains the correct answer
  adv@k      avg #adversarial passages that reached the LLM context
  kept_clean avg #clean passages in the context (utility side of filtering)

Outputs: results/{ds}/{defense}_{llm}/{setting}.jsonl (every prompt/response) and summary.csv
"""
import argparse
import csv
import os
import time

import numpy as np

from common import answer_hit, load_jsonl, save_jsonl, wrap_prompt, set_seed
from defenses import get_defense
from llm import get_llm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="nq")
    ap.add_argument("--data_dir", default="data")
    ap.add_argument("--results_dir", default="results")
    ap.add_argument("--defense", default="none")
    ap.add_argument("--settings", default="all", help="comma list, e.g. none,poison,ignore  (default: all files)")
    ap.add_argument("--backend", default="openai", choices=["openai", "hf", "mock"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--top_k", type=int, default=5)
    ap.add_argument("--max_questions", type=int, default=None, help="use the first N questions (cheap trial runs)")
    ap.add_argument("--retrieved_subdir", default=None,
                    help="default: 'retrieved_scored' for trust_* defenses, else 'retrieved'")
    ap.add_argument("--seed", type=int, default=12)
    args = ap.parse_args()
    set_seed(args.seed)

    sub = args.retrieved_subdir or ("retrieved_scored" if args.defense.startswith("trust") else "retrieved")
    rdir = os.path.join(args.data_dir, args.dataset, sub)
    settings = sorted(f[:-6] for f in os.listdir(rdir) if f.endswith(".jsonl")) if args.settings == "all" \
        else args.settings.split(",")
    settings = ["none"] + [s for s in settings if s != "none"] if "none" in settings else settings

    defense = get_defense(args.defense)
    llm = get_llm(args.backend, args.model)
    tag = f"{args.defense}_{args.backend}" + (f"-{args.model.split('/')[-1]}" if args.model else "")
    out_dir = os.path.join(args.results_dir, args.dataset, tag)

    summary = []
    for s in settings:
        rows = load_jsonl(os.path.join(rdir, f"{s}.jsonl"))[: args.max_questions]
        t0 = time.time()
        ctxs = [defense(r["question"], r["pool"], args.top_k) for r in rows]
        t_def = (time.time() - t0) / max(len(rows), 1)
        prompts = [wrap_prompt(r["question"], [p["text"] for p in c]) for r, c in zip(rows, ctxs)]
        responses = llm.generate(prompts)

        recs = []
        for r, c, p, resp in zip(rows, ctxs, prompts, responses):
            recs.append({"qid": r["qid"], "question": r["question"], "correct": r["correct"],
                         "incorrect": r["incorrect"], "n_adv_ctx": sum(x["is_adv"] for x in c),
                         "n_clean_ctx": sum(not x["is_adv"] for x in c), "prompt": p, "response": resp,
                         "attack_success": answer_hit(r["incorrect"], resp), "correct_hit": answer_hit(r["correct"], resp)})
        save_jsonl(recs, os.path.join(out_dir, f"{s}.jsonl"))
        row = {"setting": s, "n": len(recs),
               "ASR": round(100 * float(np.mean([x["attack_success"] for x in recs])), 1) if s != "none" else "-",
               "Acc": round(100 * float(np.mean([x["correct_hit"] for x in recs])), 1),
               "adv@k": round(float(np.mean([x["n_adv_ctx"] for x in recs])), 2),
               "kept_clean": round(float(np.mean([x["n_clean_ctx"] for x in recs])), 2),
               "defense_ms": round(1000 * t_def, 2)}
        summary.append(row)
        print(row)

    with open(os.path.join(out_dir, "summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    print(f"\nSaved -> {out_dir}/summary.csv")


if __name__ == "__main__":
    main()
