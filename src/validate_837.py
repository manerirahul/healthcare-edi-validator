"""Structural and balancing validation for X12 837 claim files.

Usage: python src/validate_837.py samples/sample_837.txt
Exit code 1 if any check fails (usable as a pre-submission gate).
"""
from __future__ import annotations

import os
import sys
from decimal import Decimal, InvalidOperation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from x12_parser import X12Document, parse_file


def check_envelope(doc: X12Document) -> tuple[bool, str]:
    ids = doc.segment_ids()
    for needed in ("ISA", "GS", "ST", "SE", "GE", "IEA"):
        if needed not in ids:
            return False, f"envelope: missing {needed} segment"
    if doc.transaction_type() != "837":
        return False, f"envelope: expected 837, found {doc.transaction_type()}"
    return True, "envelope: ISA/GS/ST present, transaction 837"


def check_se_count(doc: X12Document) -> tuple[bool, str]:
    span = doc.st_se_span()
    se = doc.find_one("SE")
    if not span or not se or len(se) < 2:
        return False, "SE count: ST/SE not found"
    actual = span[1] - span[0] + 1
    try:
        declared = int(se[1])
    except ValueError:
        return False, f"SE count: SE01 '{se[1]}' is not numeric"
    if declared != actual:
        return False, f"SE count: declared {declared}, actual {actual}"
    return True, f"SE segment count matches ({actual})"


def check_control_counts(doc: X12Document) -> tuple[bool, str]:
    ids = doc.segment_ids()
    ge, iea = doc.find_one("GE"), doc.find_one("IEA")
    try:
        if ge and int(ge[1]) != ids.count("ST"):
            return False, f"GE count: declared {ge[1]}, ST segments {ids.count('ST')}"
        if iea and int(iea[1]) != ids.count("GS"):
            return False, f"IEA count: declared {iea[1]}, GS segments {ids.count('GS')}"
    except (ValueError, IndexError):
        return False, "GE/IEA counts are not numeric"
    return True, "GE/IEA control counts balance"


def check_required(doc: X12Document) -> tuple[bool, str]:
    if not doc.find_one("BHT"):
        return False, "required: BHT segment missing"
    if doc.find_nm1("85") is None:
        return False, "required: billing provider (NM1*85) missing"
    if not doc.find("CLM"):
        return False, "required: no CLM claim segment"
    return True, "required segments present (BHT, billing provider, claim)"


def check_claim_balance(doc: X12Document) -> tuple[bool, str]:
    """Each CLM total must equal the sum of the SV1 charges that follow it."""
    segments = doc.segments
    results: list[str] = []
    i = 0
    while i < len(segments):
        seg = segments[i]
        if seg[0] != "CLM":
            i += 1
            continue
        claim_id = seg[1]
        try:
            total = Decimal(seg[2])
        except (IndexError, InvalidOperation):
            return False, f"claim {claim_id}: CLM02 total missing or not numeric"
        line_sum = Decimal("0")
        j = i + 1
        while j < len(segments) and segments[j][0] != "CLM":
            if segments[j][0] == "SV1" and len(segments[j]) > 2:
                try:
                    line_sum += Decimal(segments[j][2])
                except InvalidOperation:
                    return False, f"claim {claim_id}: SV102 charge not numeric"
            j += 1
        if line_sum != total:
            return False, (f"claim {claim_id}: CLM total {total} != "
                           f"service lines {line_sum}")
        results.append(f"claim {claim_id} total {total} equals service lines {line_sum}")
        i = j
    if not results:
        return False, "balance: no claims found"
    return True, "; ".join(results)


CHECKS = [check_envelope, check_se_count, check_control_counts,
          check_required, check_claim_balance]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    doc = parse_file(sys.argv[1])
    failed = 0
    for check in CHECKS:
        ok, msg = check(doc)
        print(f"[{'PASS' if ok else 'FAIL'}] {msg}")
        failed += 0 if ok else 1
    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
