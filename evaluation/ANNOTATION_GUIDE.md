# Manual annotation required before research evaluation

The paper's claimed scores are not labels and are never used by this pipeline.
The legacy `dataset/*_examples.json` and old saved metrics are unverified examples.
The active dataset is **`evaluation/datasets/`** (plural). All generated labels
start blank. Automated preparation extracts Git facts only.

## How many cases?

| Item | Available candidates | Paper-design target | Additional candidates needed if all current candidates qualify |
|---|---:|---:|---:|
| Distinct source repositories | 1 | 25 | 24 |
| Intent cases | 3 | 40 | 37 |
| Scope task/diff pairs | 3 | 30 | 27 |
| Distinct unfinished recovery repositories | 1, eligibility unconfirmed | 20 | at least 19 |
| Total analysis cases | 7, none labelled | 90 | at least 83 |
| Commits in registered history | 4 | approximately 1,800 | approximately 1,796 |

The targets describe the proposed experiment, not a statistical power guarantee.
Repositories may contribute both intent and scope cases and belong to the recovery
cohort. They need not total 40 + 30 + 20 distinct repositories. Count commit SHAs
within each repository; forked/shared histories require deduplication in a larger study.

For a smaller scored pilot, the full runner needs at least **1 labelled intent
case, 1 labelled scope pair, and 2 distinct labelled recovery repositories**.
Every case in the selected task files must be labelled; do not silently drop hard
cases. Use the task-specific runners to evaluate a completed task independently.
The current seven candidates do not satisfy even that recovery minimum.

## What to label

The current case IDs and selected regions are:

| Intent case | File and inclusive lines |
|---|---|
| `aicar_intent_07b121617c2a` | `backend/agents/intent_agent.py`, 1–30 |
| `aicar_intent_df3ad517cd35` | `backend/main.py`, 1–30 |
| `aicar_intent_1e253587774c` | `backend/agents/intent_agent.py`, 1–30 |

The matching scope IDs are `aicar_scope_07b121617c2a` (26 hunks),
`aicar_scope_df3ad517cd35` (8 hunks), and `aicar_scope_1e253587774c`
(60 hunks). The recovery candidate is `aicar_recovery` at the pinned current
revision. All seven annotations are pending.

### Intent: `datasets/intent_cases.json`

Each case already has a real repository, pinned revision, file and inclusive
1-based `[start, end]` line region. Read that region, its diffs and earlier history
in `datasets/evidence/<case_id>.json`; inspect the repository when necessary.
Automatically selected regions are only starting points. Replace unsuitable
regions with meaningful code regions and regenerate/inspect their evidence.

Fill in:

- `gold_intent`: your evidence-grounded explanation of **why this region exists**.
- `accepted_intents`: include `gold_intent` and any preregistered acceptable textual
  answers. Scoring ignores case and repeated whitespace, but otherwise uses exact
  matching. It is deliberately strict, not a semantic accuracy estimate.
- `introducing_commit`: the full 40-character SHA that introduced the selected
  region. Inspect history; the file's first commit or latest blame is not always
  the region's introducing commit.
- `supporting_commits`: real full SHAs that support the explanation, including
  the introducing commit, no later than the case revision.
- `annotation.annotator`: a human annotator ID, and `annotation.rationale`: cite
  actual paths, line ranges, hunks and/or commit messages explaining the label.
- Finally set `annotation.status` from `pending` to `labelled`.

Do not simply copy the latest commit message as the answer. Do not add accepted
answers after seeing a method's output to improve its score. Rename/move histories,
mixed-origin regions and ambiguous intent need careful human review or a documented
exclusion rule fixed before running the methods.

### Scope: `datasets/scope_cases.json`

Current candidates have 26, 8 and 60 text hunks respectively (**94 hunk labels**).
Their full real diffs and stable `hunk_<digest>` IDs are already populated.
Each candidate requires:

- `task`: the original intended task, taken from an actual issue, requirement,
  PR description, assignment or a suitably specific contemporaneous commit message.
- `task_source.reference`: an issue/PR URL or repository commit/path reference.
- `task_source.text`: an archived exact quotation of the task evidence. Confirm
  it describes the intended work before inspecting unrelated edits. Do not invent
  a task from the diff just to make it scoreable.
- **Every** `gold_hunks` value: `in-scope`, `out-of-scope`, or `unclear`.
- `gold_verdict`: `keep` when the patch is one justified task, `split` when it
  contains separable unrelated work, `justify` when more justification is needed.
  Leave null if there is no defensible verdict; decision accuracy then excludes it.
- Human annotator, rationale and `labelled` status as above.

Use `unclear` for genuinely ambiguous hunks, not as a substitute for missing
annotation. Binary precision/recall/F1 treats out-of-scope as positive and excludes
gold unclear hunks. Predicted unclear on an actual positive is a false negative.
Initial imports with no original task evidence may be unsuitable: replace them
with real issue-linked changes. Never fabricate their missing task descriptions.

### Recovery: `datasets/recovery_cases.json`

First establish that each project was unfinished at its pinned revision; set
`unfinished: true` only with supporting evidence. Select distinct repositories.
Read the extracted feature lists and inspect code, documentation and remaining
requirements. The scanner does not execute untrusted projects, verify deployment,
infer dependency health or turn README/test presence into completion percentages.

Fill in:

- `gold_recoverability`: integer relevance grade on the preregistered scale below.
- `gold_rank`: positive cohort rank; rank 1 is easiest to resume successfully.
  Ties are allowed. Rank ordering must not contradict relevance grades.
- Annotator, evidence rationale and `labelled` status.

Suggested rubric, to agree on before annotation:

| Grade | Human assessment |
|---|---|
| 0 | Recovery infeasible under the agreed effort/resources, with documented blockers |
| 1 | Major rebuilding or unresolved blockers required |
| 2 | Feasible with substantial but bounded remaining work |
| 3 | Feasible with limited remaining work and strong supporting evidence |

Specify a common time budget, environment, definition of completion and reviewer
expertise in the rationale or an accompanying protocol. Use the same constraints
for every project. nDCG uses graded relevance (not invented completion percentages).
At least one nonzero grade and two repositories are needed for defined nDCG.

## Review and evidence support

Prefer two independent human annotators, blinded to method identity/results.
Keep original judgements, record disagreements and adjudicate with a third reviewer
or documented consensus. Record exclusions before running the scored experiment.
The current pipeline validates annotation presence/provenance; it cannot certify
that a human's semantic interpretation is correct.

Every run exports `raw/<run_id>/review_template.json`, keyed by case, method and
prediction SHA-256. It lists claims for human support assessment and intent
correctness review. This is an annotation artifact only: **human review fields are
not yet consumed as a semantic metric**. Do not silently substitute those reviews
for the strict automatic intent metric in the paper. Automatic evidence support
credits exact extractive quotes only, flags interpretations for review, and never
treats a resolvable citation alone as proof. Its rate is a conservative extractive
measure; a full semantic evidence-support study still needs an adjudication scorer.

## Expand from actual repositories

Clone each selected repository locally, review its suitability, then register it:

```powershell
git clone https://github.com/OWNER/REPO evaluation/datasets/repositories/REPO
python evaluation/prepare_dataset.py --repository evaluation/datasets/repositories/REPO --id repo_id --limit 5
```

Preparation appends candidates, freezes the current HEAD and generates blank
annotations plus readable JSON evidence packs. It refuses to overwrite an existing
repository's annotations. Generated scope/intent counts depend on actual source
commits; `--limit` is an upper bound, not a claimed case count. Select additional
regions/pairs using real pinned revisions until the intended composition is met.
Use forward slashes in portable repository paths. Keep the registered snapshots
available on every machine; no floating HEAD is used during evaluation.

## Reproduce

```powershell
python -m pip install -r evaluation/requirements.txt
python -m pytest -q --junitxml=evaluation/results/test_results.xml
python evaluation/runners/run_all.py --smoke
```

After filling all selected labels:

```powershell
python evaluation/runners/run_all.py
# Or one completed task:
python evaluation/runners/run_intent_eval.py
```

Offline mode runs Git, Git script and AICAR local fallback; it skips the single
LLM method. Recovery abstentions are not rankings. For a live comparison, install
`google-genai`, set `GEMINI_API_KEY` and an explicitly selected `GEMINI_MODEL` in
the process environment, then run `python evaluation/runners/run_all.py --live`.
Do not put credentials in dataset files. The provider response is nondeterministic
even at temperature zero; saved raw responses are the audit record.

Strict runs fail clearly on missing labels. Smoke runs never produce research
accuracy metrics, even if some cases have been labelled. New runs retain immutable
raw records, code/data hashes, versions, input packs and measured timings.
