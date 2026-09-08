# Experiment 02 — Surface categorization

Status: `EXPERIMENTAL`  
Issue: #200

## Question

Can a small open-weight model classify directly observable behavioral acts well enough to improve disposition evidence collection without being allowed to predict or overwrite latent disposition constructs?

The experiment tests the classification layer, not personality validity.

## Pipeline

```text
raw observation
  -> surface classifier
  -> versioned surface labels + confidence + provenance
  -> candidate mapping (UNVALIDATED)
  -> construct-scoring experiment
  -> disposition profile
```

A surface prediction is never a profile update by itself.

## Candidates

Run four increasingly capable baselines against the same frozen benchmark:

1. deterministic lexical/rule baseline;
2. embedding prototype or nearest-centroid classifier using a small embedding model;
3. fine-tuned encoder classifier (ModernBERT-base is the initial candidate);
4. constrained JSON classification using a sub-1B instruction model (Gemma 3 270M-IT is the initial candidate).

Qwen3-Embedding-0.6B is the initial embedding candidate. SmolLM3-3B is a useful upper-bound generative control if sub-1B performance is insufficient. Model names are research candidates, not dependencies. CI must not download weights.

## Dataset

Start with 80–200 frozen snippets. Balance both poles of each construct and the subject kinds `human`, `agent/model`, and `code/mechanism` where semantically possible.

The first seed set may be synthetic and curated. Any claim about real-world behavior requires a later blinded corpus.

Include adversarial pairs:

- enacted statement versus quotation;
- positive statement versus explicit negation;
- request for alternatives versus rejection of alternatives;
- reversible action versus irreversible action;
- checking a constraint versus discussing a constraint without checking it;
- local concrete implementation versus explicit abstraction;
- prose behavior versus code/trace behavior expressing the same surface act.

Do not commit private conversation text as a fixture. Use structurally equivalent synthetic examples.

## Measures

Primary engineering measures:

- macro F1;
- per-label precision and recall;
- confusion matrix;
- Brier score or expected calibration error;
- coverage and retained accuracy under abstention;
- paraphrase stability;
- negation and quotation robustness;
- subject-kind slices;
- code/prose transfer.

Provisional engineering gate for a learned candidate:

- materially beats the deterministic baseline;
- macro F1 at or above 0.80 on the frozen validation set;
- no core label recall below 0.65;
- abstention improves retained accuracy;
- no material subject-kind collapse hidden by aggregate score.

These thresholds select an engineering candidate. They do not establish construct validity.

## Profile A/B

Only after the surface classifier clears its gate:

A. profile using directly scored probe evidence only;  
B. profile using directly scored evidence plus separately identified learned surface evidence.

Compare rebuild determinism, test/retest stability, sensitivity to paraphrase, and dependence on classifier/version. Do not call agreement with an existing personality inventory "accuracy" unless the inventory is explicitly being used as an external criterion and the limitations are stated.

## Required custody

Every learned prediction records:

- subject kind;
- observation reference;
- surface taxonomy version and digest;
- exact model ID and revision;
- inference-template revision;
- calibration revision when present;
- per-label confidence;
- threshold and abstention;
- rejected low-confidence labels.

The deterministic layer rejects unknown labels, taxonomy drift, unpinned models, and direct construct labels.

## Failure is useful

Reject or revise the surface layer if a small model mainly learns vocabulary, fails quotation/negation controls, collapses across subject kinds, or destabilizes profiles. A good result may also show that embeddings or rules are sufficient and a generative model is unnecessary.
