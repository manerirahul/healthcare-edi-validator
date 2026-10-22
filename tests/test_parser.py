"""Unit tests for the X12 parser and 837 checks. Run: python -m unittest discover tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from x12_parser import parse_file
from validate_837 import check_claim_balance, check_se_count

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "samples", "sample_837.txt")


class TestParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = parse_file(SAMPLE)

    def test_transaction_type(self):
        self.assertEqual(self.doc.transaction_type(), "837")

    def test_billing_provider_found(self):
        nm1 = self.doc.find_nm1("85")
        self.assertIsNotNone(nm1)
        self.assertEqual(nm1[3], "BILLING CLINIC")

    def test_se_count_check(self):
        ok, _ = check_se_count(self.doc)
        self.assertTrue(ok)

    def test_claim_balances(self):
        ok, msg = check_claim_balance(self.doc)
        self.assertTrue(ok, msg)


if __name__ == "__main__":
    unittest.main()
