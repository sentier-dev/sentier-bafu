import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("community_records", ROOT / "scripts/community.py")
records = importlib.util.module_from_spec(spec)
spec.loader.exec_module(records)


class ContributionTests(unittest.TestCase):
    def setUp(self):
        self.record = records.read(ROOT / "community/templates/contribution.json")
        self.record.update(
            id="C001",
            title="Test",
            status="accepted",
            evidence=["https://example.org/source"],
            required_checks=["roundtrip"],
            required_reviewers=["partner"],
            approvals=[{"reviewer": "partner", "evidence_url": "https://example.org/approval"}],
        )
        self.record["baseline"] = dict(
            dataset="test",
            release="1",
            import_repository="https://example.org/repo",
            import_revision="abc",
            input_hashes={"source": "hash"},
        )
        self.record["layer"]["implementation_revision"] = "def"
        self.record["layer"].update(
            kind="synthetic", implementation_url="https://example.org/layer"
        )
        self.record["approvals"][0].update(
            baseline=copy.deepcopy(self.record["baseline"]), layer_revision="def"
        )
        self.record["runs"] = [
            dict(
                baseline=copy.deepcopy(self.record["baseline"]),
                layer_revision="def",
                evidence_url="https://example.org/run",
                checks=[
                    dict(
                        id="roundtrip",
                        status="passed",
                        evidence_url="https://example.org/check",
                    )
                ],
            )
        ]

    def test_accepted_requires_passing_checks_and_approvals(self):
        self.assertFalse(records.validate(self.record))
        self.record["runs"][0]["checks"][0]["status"] = "skipped"
        self.assertTrue(records.validate(self.record))

    def test_old_run_cannot_validate_new_layer(self):
        self.record["layer"]["implementation_revision"] = "changed"
        self.assertTrue(records.validate(self.record))

    def test_missing_partner_review_is_not_consensus(self):
        self.record["approvals"] = []
        self.assertTrue(records.validate(self.record))

    def test_unresolved_objection_blocks_acceptance(self):
        self.record["objections"] = [{"reason": "boundary"}]
        self.assertTrue(records.validate(self.record))

    def test_approval_for_old_layer_is_not_consensus(self):
        self.record["approvals"][0]["layer_revision"] = "old-layer"
        self.assertTrue(records.validate(self.record))

    def test_empty_implementation_cannot_be_accepted(self):
        self.record["layer"]["implementation_revision"] = ""
        self.record["runs"][0]["layer_revision"] = ""
        self.record["approvals"][0]["layer_revision"] = ""
        self.assertTrue(records.validate(self.record))

    def test_comparison_checks_scope_metrics_units_and_finiteness(self):
        baseline = records.read(ROOT / "community/templates/run-summary.json")
        with tempfile.TemporaryDirectory() as directory:
            before, after = (
                Path(directory) / "baseline.json",
                Path(directory) / "candidate.json",
            )
            before.write_text(json.dumps(baseline))
            candidate = copy.deepcopy(baseline)
            candidate["metrics"]["processes"]["value"] = 2
            after.write_text(json.dumps(candidate))
            self.assertEqual(records.compare(before, after)["metrics"]["processes"]["delta"], 1)
            for change in [
                lambda x: x["scope"].update(method="different"),
                lambda x: x["metrics"].pop("processes"),
                lambda x: x["metrics"]["processes"].update(unit="kg"),
                lambda x: x["metrics"]["processes"].update(value=float("nan")),
            ]:
                candidate = copy.deepcopy(baseline)
                change(candidate)
                after.write_text(json.dumps(candidate))
                with self.assertRaises(ValueError):
                    records.compare(before, after)


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.reconciliation = records.read(ROOT / "community/reconciliation.json")
        self.rows = records.ledger_rows((ROOT / "community/findings.md").read_text())
        self.contributions = {
            p.stem: records.read(p)["status"]
            for p in (ROOT / "community/contributions").glob("*.json")
        }

    def errors(self):
        return records.validate_reconciliation(self.reconciliation, self.rows, self.contributions)

    def record(self, rid):
        return next(r for r in self.reconciliation["records"] if r["id"] == rid)

    def test_committed_reconciliation_matches_ledger(self):
        self.assertEqual(self.errors(), [])

    def test_status_drift_is_reported(self):
        self.record("F1")["ledger_status"]["after"] = "open"
        self.assertTrue(self.errors())

    def test_patch_cannot_mark_a_finding_fixed(self):
        self.rows["F1"]["status"] = "upstream-fixed"
        self.record("F1")["ledger_status"]["after"] = "upstream-fixed"
        self.assertTrue(self.errors())
        self.record("F1")["provider_correction_shipped"] = {
            "release": "BAFU:2027 v1",
            "evidence_url": "https://example.org/release",
        }
        self.assertEqual(self.errors(), [])

    def test_every_ledger_finding_needs_a_record(self):
        self.rows["F99"] = {"status": "open", "links": set()}
        self.assertTrue(self.errors())

    def test_ledger_links_are_preserved(self):
        self.rows["F2"]["links"].add("https://example.org/thread")
        self.assertTrue(self.errors())

    def test_open_record_needs_next_action_and_role(self):
        self.record("F9")["review_role"] = "anyone"
        self.assertTrue(self.errors())

    def test_provider_response_needs_public_evidence(self):
        self.record("F3")["provider_response"]["evidence_url"] = ""
        self.assertTrue(self.errors())

    def test_contribution_status_follows_its_record(self):
        self.contributions["C002"] = "accepted"
        self.assertTrue(self.errors())
