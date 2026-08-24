# Hygiene traversal repair observation

Observed 2026-08-24 while repairing the inherited Day-0 verification budget.

## Defect

`scripts/lint.py` declared `.git`, `.venv`, `__pycache__`, `lineage`, and `.local` outside the repository text population, but discovered candidates with `Path.rglob("*")` and filtered those parts only after traversal. The excluded trees therefore still consumed directory and metadata I/O before being discarded.

Hosted verification showed repository hygiene varying from sub-second observations to roughly two seconds under concurrent root-gate load. The fixed 3.0-second repository budget consequently had too little margin even after PR #88 parallelized the tooling suite.

## Repair

`repository_text_files()` now uses top-down `os.walk` and removes excluded directory names from the mutable child list before descent. File suffix/name selection, byte reading, UTF-8 handling, CR/LF rules, secret patterns, local-path rules, AST checks, and named production debt are unchanged.

A defeating test supplies `.git`, `.local`, and a visible directory to a synthetic walker and proves only the visible directory remains eligible for descent.

## Standing

This is an engineering repair to the existing hygiene mechanism. It does not widen the three-second budget, drop a check, alter service standing, or grant authority. Verification results remain evidence only.
