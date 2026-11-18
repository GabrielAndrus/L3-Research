"""
Sanity check — run BEFORE a generate/judge run to confirm the orchestration layer
is in the right place and can see the vendored CulFiT repo.

    cd <repo root>
    python -m orchestration.check_setup

Prints the resolved repo path and confirms the CulFiT EVAL prompts load from the
expected file. Exits non-zero on any problem, so it's safe to chain before a run:
    python -m orchestration.check_setup && sbatch ...
"""

from __future__ import annotations
import os
import sys


def main() -> int:
    print("=== PluralTree setup check ===")
    from orchestration import bootstrap

    # 1. Resolved locations
    print(f"CSC494 root : {bootstrap.CSC494}")
    print(f"CulFiT      : {bootstrap.CULFIT}")

    ok = True
    for label, path in [("CulFiT", bootstrap.CULFIT)]:
        exists = os.path.isdir(path)
        print(f"  [{'OK' if exists else 'MISSING'}] {label}: {path}")
        ok = ok and exists
    if not ok:
        print("\nFAIL: the CulFiT folder is missing. Is orchestration/ a direct child "
              "of the repo root, and is the folder named exactly CulFiT?")
        return 1

    # 2. Load prompts via bootstrap
    try:
        mods = bootstrap.install()
    except Exception as e:
        print(f"\nFAIL: bootstrap.install() raised: {e}")
        return 1

    # 3. Confirm CulFiT EVAL prompts
    pu = mods["culfit_prompt_utils"]
    eval_names = ["EVAL_CULTURAL_GROUP_PROMPT", "EVAL_TOPIC_PROMPT",
                  "EVAL_CULTURAL_POINTS_PROMPT"]
    missing_eval = [n for n in eval_names if not hasattr(pu, n)]
    print(f"\nCulFiT prompt_utils -> {pu.__file__}")
    if missing_eval:
        print(f"  [FAIL] missing EVAL prompts: {missing_eval}")
        ok = False
    else:
        print(f"  [OK] EVAL prompts present: {eval_names}")

    # 4. Confirm the answer-generation / extraction prompts the F1 scorer uses
    score_names = ["ANSWER_GENERATION_SYS_PROMPT",
                   "ANSER_GENERATION_USER_PROMT",  # sic: CulFiT's own spelling
                   "ANSWER_EXTRACT_PROMPT_SYS", "ANSWER_EXTRACT_PROMPT_USER"]
    missing_score = [n for n in score_names if not hasattr(pu, n)]
    if missing_score:
        print(f"  [FAIL] missing scorer prompts: {missing_score}")
        ok = False
    else:
        print(f"  [OK] scorer prompts present: {score_names}")

    print("\n" + ("PASS — setup looks good." if ok else "FAIL — see issues above."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
