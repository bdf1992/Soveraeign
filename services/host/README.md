# Host Service

The Host Service is the registered SOV boundary for operating-system state and host
operations. Start with `CHARTER.md`; the machine surface is
`contracts/service.json`; `KNOWN-GAPS.md` names what remains unavailable.

The first reference slice is deliberately small:

```text
Human or Model Binding -> Node Interface -> Gateway -> Host Service -> Host Port
```

Only `sov://host/read-health` is bound and policy-active. It requires a live
`read:host-health` grant and returns the Host Service's durable terminal receipt.
Every mutation stays declared but unreachable.

Run its participant checks from the repository root:

```bash
python -m unittest discover -s services/host/tests -v
python scripts/sov_interface.py show host.read-health --binding MODEL
```
