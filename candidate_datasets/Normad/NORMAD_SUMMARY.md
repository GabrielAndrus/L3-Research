# NormAd experiments: running summary

Living document. It records every design decision and result for the NormAd work in this repo. Detail for the first phase lives in [`NORMAD_REPORT.md`](NORMAD_REPORT.md); this file is the index and the narrative.

**Last updated:** 2026-09-23
**Status:** Phase A (informal normalization) done and committed (`37486a8`). Phase B (Ki et al. replication): the OpenRouter route stopped at ~$0.25 of credits (§3.6); the work has moved to **Narval** with two iterations, single agent and multi-agent debate (§3.7). The Narval code is written and unit-tested offline but **has not been run**; it waits on the manual steps in `ki_replication/narval/RUNBOOK.md`. Formal normalization (atomic units `[cultural value]`, `[culture]`, `[cultural norm(n)]`) is the user's next design step and is not started here.

---

## 1. Goal and framing

The project's evaluation (CulFiT-style F1) scores a response against decomposed, verifiable ground-truth points. NormAd is a different task shape (a story plus a rule, with a yes/no/neither verdict). Two questions are running in parallel:

1. **Normalization:** how do we map NormAd (and future datasets) onto the GlobalCultureQA-style schema without losing the reasoning that makes items hard? (Phase A; formal definition still to do.)
2. **Baseline:** what does the published state of the art on NormAd-ETI (Ki et al., ACL 2025, multi-agent debate) actually report, and can we reproduce it, as the number a selective-CCKG-augmentation approach must beat? (Phase B.)

---

## 2. Phase A (2026-09-14): informal normalization and complexity

Full detail in [`NORMAD_REPORT.md`](NORMAD_REPORT.md). Summary of decisions:

| Decision | What we did | Why |
|---|---|---|
| Sample | 18 hand-picked rows from HuggingFace `akhilayerukola/NormAd` (13 countries; 7 yes / 6 no / 5 neutral) | The dataset is stored in label blocks (yes, then no, then neutral), so a plain head-of-file pull is all `yes` |
| Schema map | `query`=Story, `location`=Country, `sub_topic`=Subaxis, `verified_points`=[Rule-of-Thumb, derived verdict sentence, Explanation sentences] | Closest analogue of GlobalCultureQA's decomposed knowledge points |
| Neutral rows | Rule-of-Thumb **omitted** from `verified_points` for `neutral` rows | Neutral rows pair a story with a rule that does not govern it (a distractor); treating it as ground truth would be wrong |
| `location` on neutral rows | Kept, but flagged as unreliable | See §3.3: new evidence that neutral-row countries are not stable across dataset versions |
| Pipeline check | Mock-backend run of the orchestrator over the 18 items, 3 topologies (54 runs, all completed) | Structural check only; the mock backend ignores content, so approval rate is flat and says nothing about quality |
| Complexity metric | `orchestration/analyze_eval_complexity.py` augmented with a second, judgment-shaped view (`narrative_beats`, `action_density`, `lexical_specificity`, `ambiguity_flag`); original open-QA rule kept unchanged | Original rule (≥8 verified points and ≥30-word question) rated **0/18** NormAd items complex purely because NormAd ground truth is structurally one rule plus a verdict. New view rates **14/18 (77.8%)**; on GlobalCultureQA the old rule is unchanged (3/18) and the new view gives 0/18. Deliberately *not* collapsed into one score: complexity is multi-dimensional and partly subjective |
| Pipeline change | `run_ablation.py` gained `--mode gemini` (it existed in `llm_backend.py` but was never exposed in the ablation CLI) | Unblocks a real (non-mock) run once a key is set |

Committed and pushed as `37486a8`.

---

## 3. Phase B (2026-09-23): replicating Ki et al. on NormAd-ETI

### 3.1 The pasted "Phase 1" spec was reviewed and superseded

The original spec (Qwen2.5-7B, own prompt, `Yes/No/Neither`) was **not implemented as written**, because reading it against the paper and dataset turned up problems that would have made the result meaningless:

| # | Problem in the spec | Effect |
|---|---|---|
| 1 | Gold label is `Neither` in the spec but `neutral` in the data; comparison was `lower() ==` | Every neutral item scored wrong |
| 2 | Parser used substring checks (`"no" in text`), with `yes` tested first | `not`, `know`, `norm` all read as "No"; any explanation containing "yes" reads as "Yes" |
| 3 | Option A decoded prompt + completion, and the prompt itself contains "Yes, No, or Neither" | Every prediction would parse as "Yes" |
| 4 | Prompt includes `Cultural Norm: {rot}` | That is the paper's *with rule-of-thumb* setting (see 3.2) |
| 5 | Target model Qwen2.5-7B | The paper's Table 1 has **no Qwen row** |
| 6 | Temperature 0.3 | Paper uses 0.0 |

The parser issue (#2) turned out to matter far beyond the spec: it is also how the *paper's own scorer* behaves (see 3.5).

### 3.2 What the paper actually reports (Table 1, single model, accuracy %)

Source: Ki et al., "Multiple LLM Agents Debate for Equitable Cultural Alignment", ACL 2025 (code: `github.com/dayeonki/cultural_debate`). Temperature 0.0, accuracy vs ternary gold label.

| Model | Single, no RoT | Single, with RoT | Self-reflection |
|---|---:|---:|---:|
| Yes-only / No-only / Neither-only | 35.8 / 33.2 / 31.0 | - | - |
| Llama-3 (8B) | 49.5 | 63.7 | 65.7 |
| Gemma-2 (9B) | 50.7 | 68.9 | 72.5 |
| Yi-1.5 | 51.0 | 70.7 | 71.5 |
| Gemma-2-27B (judge) | 55.8 | 79.2 | 80.1 |

Key reading: the **"60-70%" single-LLM figure is the with-rule-of-thumb setting**. Without the rule, 7-9B models sit around 43-51%. Any comparison must say which setting it uses. The paper's models are Llama-3, Gemma-2, EXAONE-3, Yi-1.5, InternLM-2.5, Aya-23, SeaLLM-3 (7-9B) and the Gemma-2-27B judge. I did not verify the debate-variant numbers or the "+2-5%" debate gain quoted in the spec.

### 3.3 Dataset: Ki's file vs HuggingFace (new finding)

The paper's repo ships its own refined file (`data/normad.jsonl`, **2,633** items). HuggingFace's `akhilayerukola/NormAd` has **2,615**. Comparison (both fully downloaded):

- All 2,615 HF IDs exist in Ki's file; Ki's file has **18 extra items, all `neutral`**.
- All **1,818 yes/no rows are identical** on every field.
- **Neutral rows differ:** 797 shared neutral IDs differ in Country/Background/Explanation, 219 in Story, 59 in Rule-of-Thumb/Value. Gold labels never differ.
- Of 579 Ki neutral stories that also appear among HF neutral stories, **0 keep the same Country** (537 keep the same rule-of-thumb).
- Label counts: Ki yes 943 / no 875 / neutral 815 (this reproduces the paper's majority-class baselines exactly: 35.8 / 33.2 / 31.0). HF: 943 / 875 / 797.

Consequences: (a) replication uses Ki's file verbatim; (b) my Phase A sample came from the HF version, so its 5 neutral rows carry country assignments that differ from Ki's; (c) this is further evidence for the caveat that `location` on neutral rows is not an intrinsic property of the story. The Phase A sample should be rebuilt from Ki's file before the formal normalization is finalized.

### 3.4 Replication design

Code in [`ki_replication/`](ki_replication/):

| File | Role |
|---|---|
| `run_single_model.py` | Ki's `single_llm/single_model` baseline over OpenRouter: their prompts verbatim (`without_rot`, `with_rot`), their country-name map, user-role message, temperature 0, `max_tokens` 256 (Llama/Qwen) or 32 (Gemma), resumable, raw generation stored untouched with provider/served-model metadata |
| `score.py` | Scores with Ki's `evaluate/accuracy_single.py` logic **ported verbatim** ("paper" scorer) and a **strict** first-word parser; per-class confusion, per-country accuracy, comparison to Table 1 |
| `test_score.py` | Unit tests pinning the scorer behaviours below |
| `run_all.sh` | Six runs (3 models x 2 settings), resumable, `WORKERS` env var |
| `data/normad_ki.jsonl` | Ki's dataset (gitignored; re-download from their repo) |
| `results/` | Raw generations (JSONL), `summary.json`, `run_all.log` |

Deviations from an exact replication (unavoidable with an API):

| Aspect | Paper | Here |
|---|---|---|
| Models | Llama-3-8B-Instruct, Gemma-2-9B-it | OpenRouter serves neither. `meta-llama/llama-3.1-8b-instruct` is the **nearest** Llama; there is no Gemma-2-9B; `google/gemma-2-27b-it` matches the paper's 27B row |
| Serving | Local HF, bf16 | Third-party providers, recorded per row: Gemma-2-27B all by NextBit; Qwen2.5-7B all by Phala; **Llama-3.1-8B by four different providers within one run** (Cloudflare, DeepInfra, Groq, Novita), so its quantization/numerics are mixed. Temperature 0 is not guaranteed bit-deterministic across providers. Pinning one provider per model would tighten this |
| Gemma prompting | The Gemma-2-9B script feeds the raw string (no chat template) | Chat API (chat template applied by provider) |
| Qwen | Not in paper's table (repo has a `qwen.py` for Qwen2-7B) | `qwen/qwen-2.5-7b-instruct` run as an extension |
| Not attempted | Self-reflection, multi-agent debate, cultural-group parity (Inglehart-Welzel bins) | Needs models OpenRouter lacks (EXAONE, Yi, InternLM, Aya, SeaLLM, Gemma-9B); see §5 |

### 3.5 Scorer finding: the paper's answer extraction is a large, model-dependent effect

Ki's scorer runs `'yes' in text`, then `'no' in text`, then `'neither' in text` on the **whole generation**. A "Neither" answer that goes on to say "the norms..." or "not" contains the substring `no`, and is scored as "No". Verbose models are penalized; terse ones are not. Observed on Qwen2.5-7B, without RoT (n=2,269 partial, see 3.6): recall on neutral items is **1.8% under the paper scorer but 46.1% under the strict parser**. Gemma-2-27B answers with a bare label, so both scorers agree exactly. So the paper scorer's number is partly a measure of answer terseness, and any augmentation experiment that changes response length would move it for reasons unrelated to cultural knowledge. Recommendation: report both, and prefer strict for our own comparisons.

### 3.6 Results so far (INCOMPLETE)

**The runs were interrupted by OpenRouter HTTP 402 ("Insufficient credits. This account never purchased credits."), after about $0.25 of usage at list price.** The runner aborts after 25 failures per model, so nothing is corrupted and re-running resumes. Only the `without_rot` setting got far; `with_rot` has 31 / 3 / 48 items (pilot-level, not scored).

Partial `without_rot` results. Runs complete in roughly ID order, so the covered set over-represents yes/no items and under-represents neutral ones (Gemma: 444 of 815 neutral; Qwen: 451; Llama: 0). Raw accuracy on a partial set is therefore **not comparable** to the paper. The table gives per-class recall (robust to that skew) and a **label-reweighted estimate** (sum over classes of full-dataset class prior x recall), which is an interim estimate and not the replication number.

| Model | n done / 2,633 | Recall yes / no / neutral (paper scorer) | Label-reweighted acc. (paper scorer) | Paper (w/o RoT) |
|---|---:|---|---:|---:|
| google/gemma-2-27b-it | 2,262 | 91.8 / 45.4 / 28.4 | **56.8** | 55.8 |
| qwen/qwen-2.5-7b-instruct | 2,269 | 94.3 / 44.2 / 1.8 | 49.0 (strict parser: 50.3) | no reference |
| meta-llama/llama-3.1-8b-instruct | 847 (yes/no rows only) | 51.8 yes | cannot reweight yet | 49.5 (Llama-3-8B) |

Deterministic checks that are already final: dataset size 2,633; class priors 35.8 / 33.2 / 31.0 reproduce the paper's three baseline rows exactly.

Reading: the one model that maps cleanly onto the paper (Gemma-2-27B, no RoT) lands within about 1 point of the published 55.8, which is encouraging but is an interim estimate. Nothing has been established yet about the with-RoT setting (paper: 79.2 for Gemma-2-27B), which is the setting the "60-70%" target refers to.

---

### 3.7 Narval route: single-agent and multi-agent iterations (designed, not yet run)

Decision (user, 2026-09-23): use Narval per `orchestration/NARVAL.md` instead of OpenRouter, and test two iterations: **single agent** and **multi-agent debate**. Narval runs Ki et al.'s exact open-weight models (Llama-3-8B-Instruct, Gemma-2-9B-it, Gemma-2-27B-it) in bf16, which removes the model-identity and provider-mixing gaps of §3.4.

**New finding: the released multi-agent code does not implement the paper's debate.** Verified offline by executing their exact `.replace(...)` chains against their `prompt.py` (encoded as tests in `narval/test_logic.py`):

| # | Released code (`multi_llm/*.py`, all pairs) | Paper (Sec. 3.2, Appendix A.3) |
|---|---|---|
| 1 | Templates use `{{rot}}`, scripts replace `{{rule}}`: the **rule-of-thumb is never inserted**; models see the literal text `Rule: {{rot}}` | Rule-of-thumb in every debate prompt ("we include the rule-of-thumb information in the prompts for all subsequent experiments") |
| 2 | Final-decision template's `{{other_feedback}}` is never filled (scripts replace `{{feedback}}`) | Discussant's feedback is shown |
| 3 | In Model 2's feedback step, its own "You:" field is filled with **Model 1's feedback** | Each agent sees its own initial response |
| 4 | **No judge step anywhere**; `accuracy_multi.py` scores each agent's final decision separately | Disagreements go to a Gemma-2-27B judge; the headline "D" number is the adjudicated one |

(The single-model and self-reflection scripts do substitute correctly; this affects only the multi-agent scripts.) Consequence: running the public code verbatim measures a debate **without** the rule-of-thumb, which is not what Table 2 reports. I cannot tell from here whether the paper's numbers came from a different code version.

Design: run the debate in two variants and compare them.
- `fixed`: the paper's Appendix A prompts (rule inserted, feedback shared, own response in own slot), plus the Appendix A.3.4 judge prompt, Gemma-2-27B judge on disagreements only.
- `released`: the public code's actual substitution behaviour, reproduced exactly.

Protocol (paper Eq. 1-2): both agents give an initial decision with explanation, exchange one round of feedback, then give final decisions. If the finals agree (after the paper scorer's normalisation) that is the decision; otherwise the judge decides. Agents: A = Gemma-2-9B (raw prompt, as in Ki's scripts), B = Llama-3-8B (chat template). Judge labels Model1 = Llama-3, Model2 = Gemma-2 (paper: agents are exchangeable); judge prompt format (raw) is inferred, since the repo has no judge code.

Targets: Table 1 rows (Llama-3 49.5 / 63.7, Gemma-2 50.7 / 68.9, Gemma-2-27B 55.8 / 79.2) for iteration 1; Table 2 row Llama-3 + Gemma-2 (D(Llama-3) 66.5, D(Gemma-2) 76.7, adjudicated D 79.7) for iteration 2.

Engineering choices (all in `ki_replication/narval/`):
- **Batched greedy generation** (left-padded) instead of Ki's one-item-at-a-time loop, which would take ~10 h for the debate. Same algorithm; not bit-identical (bf16 near-ties). Per-model prompt format copied from their scripts (Llama chat template, Gemma raw string, eager attention for Gemma-2).
- Same scorer as §3.4 (paper scorer + strict parser) plus `score_debate.py` (D(Llama-3), D(Gemma-2), adjudicated D, agreement rate, judge accuracy).
- Resumable everywhere; jobs sized per NARVAL.md conventions (`def-enaskt`, node-local venv from Alliance wheels, models staged to `$SLURM_TMPDIR`, offline mode): `single_agent.slurm` (1 GPU), `debate.slurm` (2 GPUs, both variants), `judge_27b.slurm` (2 GPUs; Gemma-2-27B bf16 is ~54 GB; runs the 27B single-agent reference row and the judge). `smoke.sh` runs 8 items through every stage first.
- Verification so far: `narval/test_logic.py` (prompt substitution for both variants, debate stage flow with fake generators, judge routing and prompt, scorer) and `test_score.py` all pass offline. **The Hugging Face generation glue (`hf_gen.py`) is not testable without a GPU; the smoke test is its first real check.**
- Prerequisite discovered: `NARVAL.md` and the existing `.slurm` files point at `~/projects/def-enaskt/hhpfiona/` (a former student's directory). Access to the `def-enaskt` allocation under the user's own Alliance account is a manual prerequisite (RUNBOOK Step 0).

Status: nothing from this section has produced results yet. The next actions are the user's (Alliance login, Hugging Face licenses, `salloc` smoke test, `sbatch`), listed step by step in `ki_replication/narval/RUNBOOK.md`.

---

## 4. How to finish the OpenRouter replication (optional, superseded by 3.7)

1. Add credits to the OpenRouter account (or use a different key). Runs cost roughly $0.5 or less to finish at list price (estimate).
2. `export OPENROUTER_API_KEY=...` in your own shell, then:
   ```bash
   cd candidate_datasets/Normad/ki_replication
   WORKERS=32 ./run_all.sh          # resumes; skips finished items
   python3 score.py results/*.jsonl --out results/summary.json
   ```
3. Security: the key was pasted into a chat. Rotate it after the runs finish. It was kept only in a private scratch file outside the repo and has been deleted; it is not in any tracked file.

---

## 5. Open items

- Finish the six runs and replace §3.6 with full-set numbers; compare with-RoT to 79.2 (Gemma-2-27B) and 63.7 (Llama-3, nearest model).
- Run the Narval iterations (§3.7) and record results here; compare `fixed` vs `released` debate against Table 2 and each other. Self-reflection (paper Table 1 last column) and the other six model pairs are out of scope for now.
- Rebuild the Phase A sample from Ki's file (§3.3).
- Formal normalization: define `[cultural value]`, `[culture]`, `[cultural norm(n)]` as atomic units and the F1-style scoring over them (user's design step). Note the with-RoT vs without-RoT distinction is exactly "is the norm given or must it be recalled", which maps onto those units.
- Decide whether our own comparisons use the paper scorer or strict parser (§3.5).
- Folder cleanup of duplicate repo clones is being handled manually by the user; nothing was deleted here.

## 6. File index

- `NORMAD_REPORT.md`: Phase A detail (sampling, mapping, nuances, complexity, mock run, next steps)
- `NORMAD_SUMMARY.md`: this file
- `normad_raw_sample.jsonl`, `normalize_normad.py`, `normad_eval_set.jsonl`: Phase A data and mapping
- `normad_complexity.json`, `run_pipeline_normad_mock.py`, `normad_mock_run_*`: complexity and mock-pipeline outputs
- `ki_replication/`: Phase B code and results (§3.4); `ki_replication/narval/`: Narval scripts, offline tests and `RUNBOOK.md` (§3.7)
