# Healthcare EDI Validator

A small X12 parser and validation tool for healthcare EDI transactions,
built from my work with healthcare data exchange (claims and eligibility)
as a Business / Data Analyst. It parses the envelope (ISA/GS/ST), walks
segments and elements, and runs the structural checks an analyst runs
first when a file fails at a clearinghouse or payer gateway.

**Synthetic samples only — no real PHI, ever.**

## What's here

| File | Purpose |
|---|---|
| `src/x12_parser.py` | Segment/element tokenizer, envelope reader, control-count helpers |
| `src/validate_837.py` | Structural + balancing checks for 837 claim files |
| `samples/sample_837.txt` | Synthetic professional claim file (2 service lines, balanced) |
| `samples/sample_270.txt` | Synthetic eligibility inquiry (270) |
| `tests/test_parser.py` | Parser and balance-check unit tests |

## Run it

```bash
python src/validate_837.py samples/sample_837.txt
python -m unittest discover tests
```

Example output:

```
[PASS] envelope: ISA/GS/ST present, transaction 837
[PASS] SE segment count matches (19)
[PASS] GE/IEA control counts balance
[PASS] required segments present (BHT, billing provider, claim)
[PASS] claim CLM001 total 250.00 equals service lines 250.00
```

## Checks performed (837)

- **Envelope integrity** — ISA/GS/ST/SE/GE/IEA present and nested in order
- **Control counts** — SE count vs actual segments; GE vs ST count;
  IEA vs GS count (the first thing a gateway rejects on)
- **Required segments** — BHT, billing provider (NM1\*85), at least one
  claim loop (CLM)
- **Charge balancing** — each CLM total equals the sum of its SV1 line
  charges, the classic claim-level reject

The parser itself is transaction-agnostic — the same tokenizer reads
835 remittances, 270/271 eligibility, and 276/277 claim status files;
per-transaction check modules plug in beside `validate_837.py`.

## License

MIT
