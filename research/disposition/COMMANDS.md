# Disposition Lab command examples

Status: `EXPERIMENTAL · ISSUE #200`

The examples below use the local research store. Replace placeholder evidence with actual observed/supplied evidence.

```bash
python scripts/sov_disposition.py init
```

Declare a human subject revision:

```bash
python scripts/sov_disposition.py subject add \
  --id alice \
  --revision baseline-1 \
  --kind human \
  --adapter human-scenario-v0.1
```

Declare a model subject revision with material configuration pinned:

```bash
python scripts/sov_disposition.py subject add \
  --id local-model-a \
  --revision qwen-example-r1 \
  --kind model \
  --adapter model-trial-v0.1 \
  --config-json '{"model":"example-model","system_digest":"sha256:example","temperature":0,"tools":[]}'
```

Append an observation:

```bash
python scripts/sov_disposition.py observe \
  --subject alice \
  --subject-revision baseline-1 \
  --construct invariant-fidelity \
  --probe invariant-fidelity.optimization-pressure.001 \
  --adapter human-scenario-v0.1 \
  --adapter-revision 1 \
  --context reversible-low-stakes \
  --value 0.75 \
  --evidence-json '{"response":"preserved the stated constraint","source":"recorded-session-example"}'
```

Build/rebuild the native profile:

```bash
python scripts/sov_disposition.py profile \
  --subject alice \
  --revision baseline-1
```

Render the native report:

```bash
python scripts/sov_disposition.py report \
  --subject alice \
  --revision baseline-1 \
  --projection sov-native-v0.1
```

Render an explicitly unvalidated research projection:

```bash
python scripts/sov_disposition.py report \
  --subject alice \
  --revision baseline-1 \
  --projection cvi-like-v0.1 \
  --allow-unvalidated
```

Verify append-chain integrity:

```bash
python scripts/sov_disposition.py verify
```

A successful command does not upgrade the psychometric standing of the instrument. Software correctness and measurement validity remain separate.
