# Node journals

A node's journal is the node's record. This directory holds it as the Record Service's
own export, one file per node under `nodes/<node>/journal/<head>.json`, named by the first
twelve characters of the head it replays to. A node has one head, so one export sits
under each node; replacing it is how the node's history advances here. The file is
self-verifying: every entry's
digest is recomputed from its contents and chained to the one before, so an edited entry
or a broken chain refuses to replay. What the file cannot prove by itself is that it is
complete, because a shorter journal is a valid journal. The head held outside it belongs
to a witness record; a reader who has that head passes it to the verifier.

Read one:

```bash
python scripts/sov_node.py journals
PYTHONPATH=services/record/src python -m soveraeign_record_service.cli verify-export \
  --export nodes/node-local/journal/<head>.json --expect-head <the witness's head>
```

Bring the node back on another host, into an empty state, so its history stays one chain
and its permits office is opened once rather than once per host:

```bash
python scripts/sov_node.py restore-journal --export nodes/node-local/journal/<head>.json \
  --node-state .local/node-interface --expect-head <the witness's head>
```

A self-report under `reports/observations/` that relies on a journal names the export by
`journal.address` and `journal.head` and the entries it leans on in `cited_entries`;
`python scripts/sov_node.py journals` refuses a citation that does not resolve. Nothing
here grants anything: the grants are entries in the journal, and who issued them is what
the journal says, not what this directory says.
