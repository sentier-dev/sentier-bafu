"""Regression checks for unsafe agreement between two mapping formats."""

import copy
import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location(
    "audit_flow_mapping", Path(__file__).resolve().parents[2] / "scripts/audit_flow_mapping.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MappingAuditTests(unittest.TestCase):
    def setUp(self):
        self.entry = {
            "source": {"name": "Test nuclide", "category": "emissions to air", "subcategory": "unspecified", "unit": "Bq"},
            "target": {"identifier": "00000000-0000-0000-0000-000000000001", "name": "Test nuclide", "context": "air/unspecified", "unit": "kBq"},
            "conversion_factor": 0.001,
            "match_step": "exact",
            "comment": "Synthetic conversion fixture",
        }
        self.pack = {"replace": [self.entry], "source_id": "synthetic", "target_id": "synthetic", "version": "test"}
        self.row = {
            **{"bafu_" + key: value for key, value in self.entry["source"].items()},
            **{"olca_" + key: self.entry["target"][field] for key, field in (("flow_uuid", "identifier"), ("name", "name"), ("context", "context"), ("unit", "unit"))},
            "n_exchanges": 3,
            "conversion_factor": 0.001,
            "match_step": "exact",
            "comment": "Synthetic conversion fixture",
            "factor_fallback_uuids": None,
        }

    def test_agreeing_files_cannot_hide_missing_bq_conversion(self):
        self.assertEqual(module.audit(self.pack, [self.row])["status"], "passed")
        self.entry["conversion_factor"] = self.row["conversion_factor"] = 1
        result = module.audit(self.pack, [self.row])
        self.assertEqual(result["status"], "failed")
        self.assertIn("Conversion factor differs from the stated unit convention", result["errors"])

    def test_source_duplicates_fail_instead_of_silently_overwriting(self):
        self.pack["replace"].append(copy.deepcopy(self.entry))
        self.assertEqual(module.audit(self.pack, [self.row])["status"], "failed")

    def test_fallback_order_is_part_of_the_contract(self):
        ids = ["00000000-0000-0000-0000-000000000002", "00000000-0000-0000-0000-000000000003"]
        self.entry["characterization_factor_fallbacks"] = [{"identifier": value, "kind": "duplicate"} for value in ids]
        self.row["factor_fallback_uuids"] = ";".join(ids)
        self.assertEqual(module.audit(self.pack, [self.row])["status"], "passed")
        self.row["factor_fallback_uuids"] = ";".join(reversed(ids))
        self.assertEqual(module.audit(self.pack, [self.row])["mismatched_fields"], {"ordered_fallbacks": 1})

    def test_unmatched_rows_remain_in_coverage_denominator(self):
        unmatched = {**self.row, "bafu_name": "Unmatched fixture", "olca_flow_uuid": None, "n_exchanges": 7}
        result = module.audit(self.pack, [self.row, unmatched])
        self.assertEqual(result["counts"]["workbook_weighted_mapping_coverage"], 0.3)
        self.assertFalse(result["inventory_recomputed"])
        self.assertFalse(result["lcia_recomputed"])


if __name__ == "__main__":
    unittest.main()
