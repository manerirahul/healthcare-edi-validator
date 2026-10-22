"""Minimal X12 tokenizer: text -> segments -> elements.

Deliberately lenient about ISA fixed-width padding (the ISA is parsed
positionally in strict implementations); here the element separator is
detected from the ISA itself, which is enough for analyst-level
structural validation of 837/835/270/271/276/277 files.
"""
from __future__ import annotations


class X12Document:
    def __init__(self, text: str):
        self.element_sep = "*"
        self.segment_sep = "~"
        stripped = text.strip()
        if stripped.startswith("ISA") and len(stripped) > 3:
            self.element_sep = stripped[3]
        raw = [s.strip() for s in stripped.replace("\r", "").split(self.segment_sep)]
        self.segments: list[list[str]] = [
            [e.strip() for e in seg.split(self.element_sep)]
            for seg in raw if seg.strip()
        ]

    def segment_ids(self) -> list[str]:
        return [seg[0] for seg in self.segments]

    def find(self, segment_id: str) -> list[list[str]]:
        return [seg for seg in self.segments if seg[0] == segment_id]

    def find_one(self, segment_id: str) -> list[str] | None:
        rows = self.find(segment_id)
        return rows[0] if rows else None

    def find_nm1(self, entity_code: str) -> list[str] | None:
        for seg in self.find("NM1"):
            if len(seg) > 1 and seg[1] == entity_code:
                return seg
        return None

    def transaction_type(self) -> str | None:
        st = self.find_one("ST")
        return st[1] if st and len(st) > 1 else None

    def st_se_span(self) -> tuple[int, int] | None:
        """Indices of the ST and its matching SE segment."""
        ids = self.segment_ids()
        try:
            start = ids.index("ST")
            end = ids.index("SE", start)
            return start, end
        except ValueError:
            return None


def parse_file(path: str) -> X12Document:
    with open(path, encoding="utf-8") as fh:
        return X12Document(fh.read())
