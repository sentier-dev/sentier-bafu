"""Comparing two builds: which rows changed, which step explains them, which scores moved.

Synthetic tables only. The tests that need pandas are skipped where it isn't installed.
"""

import importlib.util
import json
import sys
import unittest
from collections import namedtuple
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "scripts"))

from release_build import compare_builds as compare  # noqa: E402

HAS_PANDAS = importlib.util.find_spec("pandas") is not None
AMOUNT = "0001-strawberry-polyethylene-disposal"
LOCATION = "0002-supplier-locations"
NAMES = "0007-flow-names"
COMPARTMENTS = "0008-flow-compartments"


class Explain(unittest.TestCase):
    def test_a_recorded_step_that_changes_the_field_explains_the_row(self):
        self.assertEqual(compare.explain({"amount"}, [AMOUNT, "0010-links"], "exchange"), [AMOUNT])
        self.assertEqual(compare.explain({"location"}, [LOCATION], "exchange"), [LOCATION])

    def test_a_step_on_another_dataset_or_another_field_does_not(self):
        self.assertEqual(compare.explain({"amount"}, [], "exchange"), [])
        self.assertEqual(compare.explain({"amount"}, [LOCATION], "exchange"), [])
        self.assertEqual(compare.explain({"unit"}, [AMOUNT, NAMES], "exchange"), [])
        self.assertEqual(compare.explain({"amount"}, ["not-in-the-table"], "exchange"), [])

    def test_rename_and_compartment_move_are_told_apart(self):
        both = [NAMES, COMPARTMENTS]
        self.assertEqual(compare.explain({"flow", "name"}, both, "exchange"), [NAMES])
        self.assertEqual(compare.explain({"flow"}, both, "exchange"), [COMPARTMENTS])
        self.assertEqual(compare.explain({"flow"}, [NAMES], "exchange"), [NAMES])

    def test_two_steps_together_can_explain_one_row(self):
        self.assertEqual(
            compare.explain({"amount", "location"}, [AMOUNT, LOCATION], "exchange"),
            sorted([AMOUNT, LOCATION]),
        )

    def test_dataset_fields_have_their_own_table(self):
        self.assertEqual(
            compare.explain({"location"}, ["location-codes"], "process"), ["location-codes"]
        )
        self.assertEqual(compare.explain({"location"}, [LOCATION], "process"), [])


class Graph(unittest.TestCase):
    consumers = {"a": {"b"}, "b": {"c", "d"}, "x": {"y"}, "d": {"b"}}

    def test_downstream_follows_consumers_and_includes_the_seed(self):
        self.assertEqual(compare.downstream({"a"}, self.consumers), {"a", "b", "c", "d"})
        self.assertEqual(compare.downstream({"c"}, self.consumers), {"c"})
        self.assertEqual(compare.downstream(set(), self.consumers), set())

    def test_attribute_names_the_steps_upstream_of_each_moved_dataset(self):
        reach = {"one": {"a", "b"}, "two": {"b", "c"}}
        self.assertEqual(
            compare.attribute({"a", "b", "z"}, reach), {"a": ["one"], "b": ["one", "two"], "z": []}
        )


class StepFields(unittest.TestCase):
    """What a step that the table does not list can explain: what the run says it changed."""

    def summary(self, **fields):
        return {"steps": [{"id": id, "fields": changed} for id, changed in fields.items()]}

    def test_a_new_patch_explains_the_fields_the_run_summary_says_it_changed(self):
        fields = compare.step_fields(
            self.summary(
                **{
                    "0012-unit": {
                        "flowData/exchange/@unit": 2,
                        "metaInformation/processInformation/referenceFunction/@unit": 2,
                    },
                    "0013-amount": {"flowData/exchange/@meanValue": 1},
                    "0014-supplier": {"flowData/exchange/@number": 1},
                    "0015-direction": {"flowData/exchange/inputGroup": 1},
                }
            )
        )
        self.assertEqual(
            fields["0012-unit"], {"exchange": {"flow", "unit"}, "process": {"reference_unit"}}
        )
        self.assertEqual(fields["0013-amount"], {"exchange": {"amount"}, "process": set()})
        self.assertEqual(fields["0014-supplier"]["exchange"], {"flow"})
        self.assertEqual(fields["0015-direction"]["exchange"], {"kind"})
        self.assertEqual(
            compare.explain({"unit"}, ["0012-unit"], "exchange", fields), ["0012-unit"]
        )
        self.assertEqual(
            compare.explain({"reference_unit"}, ["0012-unit"], "process", fields), ["0012-unit"]
        )
        self.assertEqual(compare.explain({"amount"}, ["0012-unit"], "exchange", fields), [])

    def test_a_step_in_the_table_keeps_what_the_table_says(self):
        # even if a run says it changed more: that is then an unexplained row, on purpose
        fields = compare.step_fields(
            self.summary(
                **{AMOUNT: {"flowData/exchange/@meanValue": 3, "flowData/exchange/@unit": 3}}
            )
        )
        self.assertEqual(fields[AMOUNT], compare.STEP_FIELDS[AMOUNT])
        self.assertEqual(compare.explain({"unit"}, [AMOUNT], "exchange", fields), [])

    def test_steps_the_importer_can_not_see_explain_nothing(self):
        fields = compare.step_fields(
            self.summary(
                **{
                    "0004-flow-cas-numbers-added": {"flowData/exchange/@CASNumber": 9},
                    "0010-brightway-flows-links": {
                        "flowData/exchange/extensions/@brightwayFlow": 9
                    },
                    "0003-flag-not-maintained": {"extensions/@maintenance": 9},
                    # the adapter gives every exchange its original number back
                    "renumber-exchanges": {"flowData/exchange/@number": 9},
                }
            )
        )
        self.assertEqual(set(fields), set(compare.STEP_FIELDS))

    def test_a_layer_explains_a_substituted_supplier(self):
        fields = compare.step_fields(None, {"step": "C900-other"})
        self.assertEqual(
            compare.explain({"flow", "name", "location"}, ["C900-other"], "exchange", fields),
            ["C900-other"],
        )
        self.assertEqual(compare.explain({"amount"}, ["C900-other"], "exchange", fields), [])

    def test_the_steps_of_a_dataset_include_the_layer_that_changed_it(self):
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            build = Path(folder)
            (build / "adapter-receipt.json").write_text(
                json.dumps(
                    {"steps_by_dataset": {"crop": {"import_fixes": ["a"], "patches": ["b"]}}}
                )
            )
            self.assertEqual(compare.read_steps(build), {"crop": ["a", "b"]})
            (build / "layer-receipt.json").write_text(
                json.dumps({"step": "C900-other", "datasets_changed": ["crop", "farm"]})
            )
            self.assertEqual(
                compare.read_steps(build),
                {"crop": ["a", "b", "C900-other"], "farm": ["C900-other"]},
            )

    def test_a_step_both_builds_share_explains_no_difference_between_them(self):
        # the patched copy and a contribution: the patch is in both, the layer in one
        candidate = {"crop": ["0007-flow-names", "C900-other"], "farm": ["C900-other"]}
        patched = {"crop": ["0007-flow-names"], "mill": ["location-codes"]}
        alone = compare.steps_of_the_candidate_alone(candidate, patched)
        self.assertEqual(alone, {"crop": ["C900-other"], "farm": ["C900-other"]})
        fields = compare.step_fields(None, {"step": "C900-other"})
        # a supplier of the same location: only the flow and its name change
        changed = {"flow", "name"}
        self.assertEqual(
            compare.explain(changed, candidate["crop"], "exchange", fields), ["0007-flow-names"]
        )
        self.assertEqual(
            compare.explain(changed, alone["crop"], "exchange", fields), ["C900-other"]
        )
        # the provider release has no step recorded: nothing is taken away
        self.assertEqual(compare.steps_of_the_candidate_alone(candidate, {}), candidate)


Entry = namedtuple("Entry", "target_code conversion_factor")
Method = namedtuple("Method", "method_id cfs")


@unittest.skipUnless(HAS_PANDAS, "pandas is not installed here")
class Tables(unittest.TestCase):
    def inventory(self, **changes):
        import pandas as pd

        processes = pd.DataFrame(
            {
                "process_id": ["farm", "gas", "mix"],
                "name": ["Fruit", "Gas, at production", "Mix"],
                "location": ["CH", "NO", changes.get("mix_location", "Europe without Switzerland")],
            }
        )
        rows = [
            ("farm", "farm", "Fruit", "production", 1.0, None),
            ("farm", "waste", "Disposal", "technosphere", changes.get("disposal", 100.0), "CH"),
            ("farm", "co2-old", "Carbon dioxide", "biosphere", 1.0, None),
            ("gas", "gas", "Gas, at production", "production", 1.0, None),
            (
                "gas",
                changes.get("gas_flow", "gas-old"),
                changes.get("gas_name", "Gas, natural/m3"),
                "biosphere",
                1.0,
                None,
            ),
            ("mix", "mix", "Mix", "production", 1.0, None),
            (
                "mix",
                "gas",
                "Gas, at production",
                "technosphere",
                2.0,
                changes.get("declared", "XX"),
            ),
            ("mix", "farm", "Fruit", "technosphere", 0.0, "CH"),
        ]
        columns = ["process_id", "flow", "flow_name", "flow_type", "amount", "location"]
        exchanges = pd.DataFrame(rows, columns=columns)
        exchanges["position"] = exchanges.groupby("process_id").cumcount()
        return processes, exchanges

    def setUp(self):
        self.base = self.inventory()
        self.cand = self.inventory(
            disposal=0.01,
            gas_flow="gas-new",
            gas_name="Gas, natural",
            declared="NO",
            mix_location="EURwoCH",
        )
        self.steps = {
            "farm": ["renumber-exchanges", AMOUNT],
            "gas": [NAMES, "0010-links"],
            "mix": ["location-codes", LOCATION],
        }
        self.bridge = {"gas-old": Entry("ef-gas", 35.98), "co2-old": Entry("ef-co2", 1.0)}
        self.methods = [
            Method("climate", (("ef-co2", 1.0),)),
            Method("fossils", (("ef-gas", 1.0),)),
        ]
        self.effective = compare.effective_factors(self.bridge, self.methods)

    def test_every_changed_row_is_attributed(self):
        result = compare.compare_rows(self.base, self.cand, self.steps)
        summary = result["summary"]
        self.assertEqual(summary["exchange_rows_compared"], 8)
        self.assertEqual(summary["exchange_rows_changed"], 3)
        self.assertEqual(summary["unexplained_count"], 0)
        self.assertEqual(summary["by_step"][AMOUNT], {"amount": 1, "rows": 1, "datasets": 1})
        self.assertEqual(
            summary["by_step"][NAMES], {"flow": 1, "name": 1, "rows": 1, "datasets": 1}
        )
        # Two steps recorded on "mix" can both change an exchange location: both are named
        self.assertEqual(
            summary["by_step"][f"location-codes + {LOCATION}"],
            {"location": 1, "rows": 1, "datasets": 1},
        )
        self.assertEqual(
            summary["dataset_rows_changed_by_step"], {"location-codes": {"location": 1}}
        )

    def test_a_step_explains_only_the_kind_of_exchange_it_changes(self):
        """A patch of a flow's compartment explains an elementary exchange, not an input from
        another dataset that was relinked in a dataset the patch also touched."""
        processes, exchanges = self.inventory()
        relinked = exchanges.copy()
        mix_gas = (relinked.process_id == "mix") & (relinked.flow == "gas")
        relinked.loc[mix_gas, "flow"] = "farm"  # the input now comes from another supplier
        result = compare.compare_rows(
            (processes, exchanges), (processes, relinked), {"mix": [COMPARTMENTS]}
        )
        self.assertEqual(result["summary"]["unexplained_count"], 1)
        self.assertEqual(result["summary"]["unexplained"], [{"dataset": "mix", "fields": ["flow"]}])
        # The same patch does explain a changed identity of an elementary exchange.
        moved = exchanges.copy()
        moved.loc[(moved.process_id == "gas") & (moved.flow == "gas-old"), "flow"] = "gas-other"
        result = compare.compare_rows(
            (processes, exchanges), (processes, moved), {"gas": [COMPARTMENTS]}
        )
        self.assertEqual(result["summary"]["unexplained_count"], 0)
        self.assertEqual(result["summary"]["by_step"][COMPARTMENTS]["rows"], 1)
        # And a patch of an input's amount does not explain a changed elementary amount.
        emitted = exchanges.copy()
        emitted.loc[(emitted.process_id == "farm") & (emitted.flow == "co2-old"), "amount"] = 2.0
        result = compare.compare_rows(
            (processes, exchanges), (processes, emitted), {"farm": [AMOUNT]}
        )
        self.assertEqual(result["summary"]["unexplained_count"], 1)
        self.assertTrue(compare.may_change("location-codes", {"technosphere"}))
        self.assertTrue(compare.may_change("a step the table does not know", {"biosphere"}))

    def test_the_attribution_is_by_dataset_and_says_so(self):
        """What stays open: two changed amounts in one dataset that patch 0001 touched are
        both put down to it, also the one the patch did not make. The patch run records the
        datasets a step changed, not the exchanges."""
        processes, exchanges = self.inventory()
        changed = exchanges.copy()
        changed.loc[(changed.process_id == "farm") & (changed.flow == "waste"), "amount"] = 0.01
        changed.loc[(changed.process_id == "mix") & (changed.flow == "gas"), "amount"] = 2000.0
        result = compare.compare_rows(
            (processes, exchanges), (processes, changed), {"farm": [AMOUNT], "mix": [AMOUNT]}
        )
        self.assertEqual(result["summary"]["by_step"][AMOUNT]["rows"], 2)
        self.assertIn("by dataset, not by exchange", compare.ATTRIBUTION)

    def test_a_change_no_recorded_step_explains_is_reported(self):
        result = compare.compare_rows(self.base, self.cand, {"gas": [NAMES], "mix": [LOCATION]})
        summary = result["summary"]
        self.assertEqual(summary["unexplained_count"], 2)  # the amount, and the dataset location
        self.assertIn("unexplained", summary["by_step"])
        self.assertEqual(
            {(item["dataset"], *item["fields"]) for item in summary["unexplained"]},
            {("farm", "amount"), ("mix", "location")},
        )

    def layered(self, **planted):
        """The base and a candidate in which a layer repoints the mix's gas input to the
        farm; `planted` changes the candidate beyond what the layer's receipt lists."""
        base = self.inventory()
        processes, exchanges = self.inventory()
        mix_gas = (exchanges["process_id"] == "mix") & (exchanges["flow"] == "gas")
        exchanges.loc[mix_gas, ["flow", "flow_name", "location"]] = ["farm", "Fruit", "CH"]
        for (process, position), values in planted.get("rows", {}).items():
            row = (exchanges["process_id"] == process) & (exchanges["position"] == position)
            exchanges.loc[row, list(values)] = list(values.values())
        receipt = {
            "step": "C900-other",
            "datasets_changed": ["mix"],
            "exchanges": [
                {"dataset": "mix", "position": 1}
                | {"before": {"flow": "gas"}, "after": {"flow": "farm"}}
            ],
        }
        steps = {"mix": ["C900-other"], "farm": ["C900-other"]}
        fields = compare.step_fields(None, receipt)
        return compare.compare_rows(base, (processes, exchanges), steps, fields, receipt)["summary"]

    def test_a_layer_explains_the_input_its_receipt_lists(self):
        summary = self.layered()
        self.assertEqual(summary["exchange_rows_changed"], 1)
        self.assertEqual(summary["unexplained_count"], 0)
        self.assertEqual(summary["by_step"]["C900-other"]["rows"], 1)

    def test_an_undeclared_repointing_in_a_dataset_the_layer_touches_is_unexplained(self):
        # the mix's second input, which the receipt does not list, is repointed too
        planted = {("mix", 2): {"flow": "gas", "flow_name": "Gas, at production"}}
        summary = self.layered(rows=planted)
        self.assertEqual(summary["exchange_rows_changed"], 2)
        self.assertEqual(summary["by_step"]["C900-other"]["rows"], 1)
        self.assertEqual(summary["unexplained_count"], 1)
        self.assertEqual(summary["unexplained"], [{"dataset": "mix", "fields": ["flow", "name"]}])

    def test_a_declared_input_that_took_another_supplier_is_unexplained(self):
        planted = {("mix", 1): {"flow": "mix", "flow_name": "Mix"}}
        summary = self.layered(rows=planted)
        self.assertEqual(summary["unexplained_count"], 1)
        self.assertNotIn("C900-other", summary["by_step"])

    def test_identical_builds_have_no_changes(self):
        summary = compare.compare_rows(self.base, self.base, {})["summary"]
        self.assertEqual(summary["exchange_rows_changed"], 0)
        self.assertEqual(summary["unexplained_count"], 0)

    def test_a_renamed_flow_that_the_mapping_does_not_know_loses_its_ef_flow(self):
        rows = compare.compare_rows(self.base, self.cand, self.steps)["rows"]
        flows = compare.compare_flows(rows, self.bridge, self.effective, {"ef-gas": "Natural Gas"})
        self.assertEqual(flows["exchanges_that_lost_their_ef_3_1_flow"], 1)
        self.assertEqual(flows["flows_that_lost_their_ef_3_1_flow"], 1)
        (flow,) = flows["flows_that_changed_identity"]
        self.assertEqual(
            (flow["name_before"], flow["name_after"]), ("Gas, natural/m3", "Gas, natural")
        )
        self.assertEqual(flow["ef_3_1_flow_before"], "Natural Gas")
        self.assertIsNone(flow["ef_3_1_flow_after"])
        self.assertEqual(flow["methods_whose_factor_changes"], ["fossils"])
        self.assertEqual(flow["steps"], [NAMES])

    def test_a_renamed_flow_that_the_mapping_knows_stays_linked(self):
        bridge = {**self.bridge, "gas-new": Entry("ef-gas", 35.98)}
        effective = compare.effective_factors(bridge, self.methods)
        rows = compare.compare_rows(self.base, self.cand, self.steps)["rows"]
        flows = compare.compare_flows(rows, bridge, effective, {})
        self.assertEqual(flows["exchanges_that_lost_their_ef_3_1_flow"], 0)
        (flow,) = flows["flows_that_changed_identity"]
        self.assertEqual(flow["methods_whose_factor_changes"], [])
        self.assertEqual(flow["ef_3_1_flow_after"], "EF 3.1 flow ef-gas")

    def test_seeds_are_the_datasets_whose_change_can_move_a_method(self):
        rows = compare.compare_rows(self.base, self.cand, self.steps)["rows"]
        seeds = compare.relevant_seeds(rows, self.effective, ["climate", "fossils"])
        self.assertEqual(dict(seeds["climate"]), {AMOUNT: {"farm"}})
        self.assertEqual(dict(seeds["fossils"]), {AMOUNT: {"farm"}, NAMES: {"gas"}})

    def test_zero_amount_inputs_are_not_supply_chain_links(self):
        graph = compare.consumer_graph(self.base[1], self.cand[1])
        self.assertEqual(dict(graph), {"waste": {"farm"}, "gas": {"mix"}})  # not farm -> mix

    def test_moved_scores_are_attributed_or_reported(self):
        import pandas as pd

        rows = compare.compare_rows(self.base, self.cand, self.steps)["rows"]
        seeds = compare.relevant_seeds(rows, self.effective, ["climate", "fossils"])
        graph = compare.consumer_graph(self.base[1], self.cand[1])
        index = pd.Index(["farm", "gas", "mix"], name="code")
        before = pd.DataFrame(
            {"climate": [300.0, 0.0, 0.0], "fossils": [5.0, 36.0, 72.0]}, index=index
        )
        after = pd.DataFrame(
            {"climate": [1.0, 0.0, 0.0], "fossils": [0.1, 0.0, 72.0 * (1 + 1e-9)]}, index=index
        )
        names = {"farm": {"name": "Fruit", "location": "CH"}}
        result = compare.compare_scores(before, after, seeds, graph, names)
        climate, fossils = result["methods"]
        self.assertEqual(climate["datasets_moved"], 1)
        self.assertEqual(climate["moved_by_step"], {AMOUNT: 1})
        self.assertEqual(climate["moved"][0]["name"], "Fruit")
        self.assertAlmostEqual(climate["moved"][0]["change_percent"], -99.6666667, places=5)
        self.assertEqual(fossils["moved_by_step"], {AMOUNT: 1, NAMES: 1})
        self.assertEqual(fossils["datasets_that_could_move"], {AMOUNT: 1, NAMES: 2})
        self.assertEqual(fossils["differences_below_tolerance"], 1)  # the solver noise on "mix"
        self.assertEqual(result["unexplained_moves"], 0)

        after.loc["mix", "climate"] = 9.0  # nothing upstream of "mix" changed for climate
        result = compare.compare_scores(before, after, seeds, graph, names)
        self.assertEqual(result["unexplained_moves"], 1)
        self.assertEqual(result["methods"][0]["moved_by_step"], {AMOUNT: 1, "unexplained": 1})

    def test_what_moved_is_written_for_the_site_dataset_by_dataset(self):
        """`before-after.json`: the same counts as the comparison, every moved dataset with its
        results in every method, the furthest first, and each step with what it changed."""
        import pandas as pd
        from release_build import before_after_account
        from runrecord import before_after

        rows = compare.compare_rows(self.base, self.cand, self.steps)
        seeds = compare.relevant_seeds(rows["rows"], self.effective, ["climate", "fossils"])
        graph = compare.consumer_graph(self.base[1], self.cand[1])
        index = pd.Index(["farm", "gas", "mix"], name="code")
        before = pd.DataFrame(
            {"climate": [300.0, 0.0, 0.0], "fossils": [5.0, 36.0, 72.0]}, index=index
        )
        after = pd.DataFrame(
            {"climate": [1.0, 0.0, 0.0], "fossils": [0.1, 0.0, 72.0 * (1 + 1e-9)]}, index=index
        )
        names = {
            "farm": {"name": "Fruit", "location": "CH"},
            "gas": {"name": "Gas", "location": "NO"},
        }
        moved, reach = {}, {}
        scores = compare.compare_scores(before, after, seeds, graph, names, moved, reach)
        self.assertEqual(
            moved, {"climate": {"farm": [AMOUNT]}, "fossils": {"farm": [AMOUNT], "gas": [NAMES]}}
        )
        # what each step can move: everything downstream of what it changed, per method
        self.assertEqual(reach["climate"], {AMOUNT: {"farm"}})
        self.assertEqual(reach["fossils"], {AMOUNT: {"farm"}, NAMES: {"gas", "mix"}})
        comparison = {
            "scores": scores,
            "rows": rows["summary"],
            "builds": {"candidate": {"datasets": 3}},
            "linked_on_the_declared_flow": {"exchanges": 2},
            "elementary_flows": {"exchanges_that_lost_their_ef_3_1_flow": 1},
        }
        records = (
            {"patched": False, "databases": {"inventory": "x-2026"}},
            {
                "patched": True,
                "databases": {"inventory": "x-2026-patched"},
                "release": {"name": "X:2026"},
            },
        )
        steps = {AMOUNT: {"kind": "patch", "description": "Correct the disposal. "}}

        def account(**more):
            return before_after_account.account(
                comparison, records, (before.to_dict(), after.to_dict()), moved, names,
                {"climate": "kg CO2 eq"}, steps, reach, **more,
            )  # fmt: skip

        data = account()
        self.assertEqual(before_after.shape_errors(data), [])
        self.assertEqual(data["title"], "X:2026 and the patched copy")
        self.assertEqual(
            (data["before"]["label"], data["after"]["label"]), ("X:2026", "Patched copy")
        )
        self.assertIn("`x-2026`", data["before"]["about"])
        self.assertEqual(
            data["items"], {"one": "dataset", "many": "datasets", "compared": 3, "moved": 2}
        )
        climate, fossils = data["indicators"]
        self.assertEqual((climate["unit"], climate["moved"]), ("kg CO2 eq", 1))
        self.assertEqual((climate["lower"], climate["unexplained"]), (1, 0))
        self.assertEqual((fossils["moved"], fossils["lower"], fossils["higher"]), (2, 2, 0))
        self.assertEqual(sum(fossils["bands"]), 3)
        # the furthest from no change first: a factor of 300 lies further than a lost score,
        # which counts as a factor of 100
        self.assertEqual([item["id"] for item in data["moved"]], ["farm", "gas"])
        farm = data["moved"][0]
        self.assertEqual((farm["name"], farm["place"], farm["causes"]), ("Fruit", "CH", [AMOUNT]))
        self.assertEqual(farm["values"], {"climate": [300.0, 1.0], "fossils": [5.0, 0.1]})
        causes = {cause["id"]: cause for cause in data["causes"]}
        self.assertEqual(causes[AMOUNT]["kind"], "patch")
        self.assertEqual(causes[AMOUNT]["title"], "Correct the disposal.")
        amount = causes[AMOUNT]
        self.assertEqual(
            (amount["rows"], amount["changed"], amount["moved"]), (1, {"amount": 1}, 1)
        )
        # a row two steps explain together is listed under both names. Such a pair has no
        # reach of its own, so it has no count of what it moved and no claim: not "0", unknown
        both = causes[f"location-codes + {LOCATION}"]
        self.assertEqual(
            (both["kind"], both["moved"], both["claim"]), ("two steps together", None, None)
        )
        # each step's claim is worked out: how many datasets it reaches, and never which
        self.assertEqual(
            (amount["claim"]["derived"], amount["claim"]["reach"], amount["claim"]["scope"]),
            (True, 1, []),
        )
        self.assertEqual(causes[NAMES]["claim"]["reach"], 2)
        # a step that changed nothing a result depends on claims that nothing moves
        nothing = before_after_account.derived_claim(LOCATION, reach)
        self.assertEqual((nothing["derived"], nothing["reach"]), (True, 0))
        self.assertIn("Nothing this step changed can move a result", nothing["text"])
        # every value has a class; what moved inside a step's reach is as claimed, and "mix",
        # which the names step reaches and which did not move, is unchanged: a reach that was
        # worked out says what may move
        self.assertEqual(climate["classes"], {"unchanged": 2, "as claimed": 1})
        self.assertEqual(fossils["classes"], {"unchanged": 1, "as claimed": 2})
        self.assertEqual(farm["classes"], {"climate": "as claimed", "fossils": "as claimed"})
        self.assertEqual(farm["moved"], ["climate", "fossils"])
        # noise is not measured, and the file claims nothing about it that was not measured
        self.assertEqual(
            data["noise"],
            {
                "measured": False,
                "between": None,
                "note": "Both builds were made in one run, on one machine.",
            },
        )
        self.assertEqual(data["rows"]["differ"], rows["summary"]["exchange_rows_changed"])
        self.assertEqual(len(data["notes"]), 2)
        # a page lists only so many datasets with their results, and says how many it left out
        short = account(listed=1)
        self.assertEqual(
            ([item["id"] for item in short["moved"]], short["moved_not_listed"]), (["farm"], 1)
        )
        self.assertEqual(short["items"]["moved"], 2)
        # a name of any length, with a line break in it, is a name the format takes
        long = dict(names) | {"farm": {"name": "Fruit\n" + "x" * 500, "location": "C\tH" * 40}}
        written = before_after_account.account(
            comparison, records, (before.to_dict(), after.to_dict()), moved, long,
            {"climate": "kg CO2 eq"}, steps, reach,
        )  # fmt: skip
        self.assertEqual(before_after.shape_errors(written), [])
        self.assertTrue(written["moved"][0]["name"].startswith("Fruit xxx"))
        # a score that moved outside every step's reach is not claimed: what the comparison
        # calls unexplained, and the two counts must agree
        outside = after.copy()
        outside.loc["mix", "climate"] = 9.0
        moved_2, reach_2 = {}, {}
        scores_2 = compare.compare_scores(before, outside, seeds, graph, names, moved_2, reach_2)
        found = before_after_account.account(
            comparison | {"scores": scores_2}, records, (before.to_dict(), outside.to_dict()),
            moved_2, names, {"climate": "kg CO2 eq"}, steps, reach_2,
        )  # fmt: skip
        self.assertEqual(found["indicators"][0]["classes"]["not claimed"], 1)
        self.assertEqual(found["indicators"][0]["unexplained"], 1)
        mix = next(item for item in found["moved"] if item["id"] == "mix")
        self.assertEqual((mix["classes"]["climate"], mix["causes"]), ("not claimed", []))
        # A row that no step explains is the comparison's finding, under its label
        # "unexplained". The label is no cause: a dataset it reaches beside a real step is
        # listed under the step alone, and one it alone reaches is not claimed.
        label = before_after_account.UNEXPLAINED
        by_step = comparison["rows"]["by_step"] | {label: {"rows": 1, "datasets": 1}}
        labelled = comparison | {
            "scores": scores_2,
            "rows": comparison["rows"] | {"by_step": by_step},
        }
        moved_3 = {m: {code: [*why, label] for code, why in found.items()}
                   for m, found in moved_2.items()}  # fmt: skip
        reach_3 = {m: by | {label: {"farm", "mix"}} for m, by in reach_2.items()}
        self.assertEqual(moved_3["climate"], {"farm": [AMOUNT, label], "mix": [label]})
        marked = before_after_account.account(
            labelled, records, (before.to_dict(), outside.to_dict()), moved_3, names,
            {"climate": "kg CO2 eq"}, steps, reach_3,
        )  # fmt: skip
        self.assertNotIn(label, [cause["id"] for cause in marked["causes"]])
        by_id = {item["id"]: item for item in marked["moved"]}
        self.assertEqual(by_id["farm"]["causes"], [AMOUNT])
        self.assertEqual((by_id["mix"]["causes"], by_id["mix"]["classes"]["climate"]),
                         ([], "not claimed"))  # fmt: skip
        self.assertEqual(marked["indicators"][0]["unexplained"], 1)
        wider = reach_2 | {"climate": {AMOUNT: {"farm", "mix"}}}
        with self.assertRaisesRegex(ValueError, "0 moved outside every step's reach"):
            before_after_account.account(
                comparison | {"scores": scores_2},
                records,
                (before.to_dict(), outside.to_dict()),
                moved_2,
                names,
                {},
                steps,
                wider,
            )
        # a count that is not the comparison's own stops the file from being written
        scores["methods"][0]["datasets_moved"] = 2
        with self.assertRaisesRegex(ValueError, "the comparison counted 2 moved of 3"):
            account()

    def chain_inputs(self):
        """What compare_scores gives the writers, on the synthetic tables."""
        import pandas as pd

        rows = compare.compare_rows(self.base, self.cand, self.steps)
        seeds = compare.relevant_seeds(rows["rows"], self.effective, ["climate", "fossils"])
        graph = compare.consumer_graph(self.base[1], self.cand[1])
        index = pd.Index(["farm", "gas", "mix"], name="code")
        before = pd.DataFrame(
            {"climate": [300.0, 0.0, 2.0], "fossils": [5.0, 36.0, 72.0]}, index=index
        )
        after = pd.DataFrame(
            {"climate": [1.0, 0.0, 2.0], "fossils": [0.1, 0.0, 72.0 * (1 + 1e-9)]}, index=index
        )
        names = {
            "farm": {"name": "Fruit", "location": "CH"},
            "gas": {"name": "Gas", "location": "NO"},
        }
        moved, reach = {}, {}
        scores = compare.compare_scores(before, after, seeds, graph, names, moved, reach)
        comparison = {
            "scores": scores,
            "rows": rows["summary"],
            "builds": {"candidate": {"datasets": 3}},
            "linked_on_the_declared_flow": {"exchanges": 2},
            "elementary_flows": {"exchanges_that_lost_their_ef_3_1_flow": 0},
        }
        records = (
            {"databases": {"inventory": "x-2026"}, "tools": {"this repository": "abc1234"}},
            {"databases": {"inventory": "x-2026-patched"}, "release": {"name": "X:2026"}},
        )
        steps = {AMOUNT: {"kind": "patch", "description": "Correct the disposal."}}
        units = {"farm": "kg", "gas": "MJ", "mix": "MJ"}
        return comparison, records, (before.to_dict(), after.to_dict()), names, steps, reach, units

    @unittest.skipUnless(
        importlib.util.find_spec("sentier_diagnostics"), "needs sentier-diagnostics"
    )
    def test_the_comparison_is_written_as_a_chain_in_the_shared_format(self):
        import tempfile

        from release_build import diagnostics_account as account
        from sentier_diagnostics import fileformat

        comparison, records, scores, names, steps, reach, units = self.chain_inputs()
        data = account.chain(
            comparison, records, scores, names, {"climate": "kg CO2 eq"}, steps, reach, units,
            item_groups={"farm": "agriculture", "gas": "fuels"},
        )  # fmt: skip
        self.assertEqual(fileformat.errors(data), [])
        # a dataset's sector is its group; one without a sector has none
        groups = {item["id"]: item["group"] for item in data["items"]}
        self.assertEqual(groups.get("farm"), "agriculture")
        self.assertEqual([s["id"] for s in data["states"]], ["before", "after"])
        # noise belongs to a state, and none is built twice in a run: each state says so, and a
        # step takes the noise of its two states, not measured either
        for state in data["states"]:
            self.assertEqual(
                (state["noise"]["measured"], state["noise"]["note"]),
                (False, "No state is built twice in a run."),
            )
        (step,) = data["steps"]
        self.assertFalse(step["noise"]["measured"])
        # the claim is the comparison's reach (farm in climate; farm, gas and mix in fossil
        # resources), published as a count only
        self.assertEqual((step["claim"]["reach"], step["claim"]["scope"][0]["items"]), (3, None))
        climate = data["counts"]["steps"]["fixes"]["climate"]
        self.assertEqual(climate["verdicts"]["as claimed"], 1)
        self.assertEqual(climate["verdicts"]["not claimed"], 0)
        # with a build of the world's factors, the countries' factors are a step of their own,
        # claimed in the categories the install report names
        with tempfile.TemporaryDirectory() as tmp:
            world, provider = Path(tmp) / "world", Path(tmp) / "provider"
            for folder in (world / "audit", provider / "logs"):
                folder.mkdir(parents=True)
            (world / "audit" / "scores.csv").write_text(
                "code,climate,fossils\nfarm,300,5\ngas,0,36\nmix,1.5,72\n"
            )
            report = {"coverage": {"located_by_method": [["climate", 1], ["fossils", 0]]}}
            (provider / "logs" / "install-report.json").write_text(json.dumps(report))
            # the state "the world's factors" is BAFU's release built without the countries'
            # factors, as the provider build was built: any other build is refused
            record = world / "build.json"
            for written, said in (
                (None, "not a build with the world's factors"),
                ({"install": {"located": True}}, "not a build with the world's factors"),
                ({"install": {"located": False}, "patched": True}, "a patched copy"),
                ({"install": {"located": False}, "release": {"name": "Y:2027"}},
                 "another release"),
                ({"install": {"located": False, "flow_links": {"file": "links.csv"}}},
                 "another linking"),
            ):  # fmt: skip
                if written is not None:
                    record.write_text(json.dumps(written))
                with self.assertRaisesRegex(account.ChainError, said):
                    account.chain(
                        comparison, records, scores, names, {}, steps, reach, units,
                        world=world, candidate=provider,
                    )  # fmt: skip
            record.write_text(json.dumps({"patched": False, "install": {"located": False}}))
            data = account.chain(
                comparison, records, scores, names, {}, steps, reach, units,
                world=world, candidate=provider,
            )  # fmt: skip
            self.assertEqual(fileformat.errors(data), [])
            self.assertEqual([s["id"] for s in data["states"]], ["world", "before", "after"])
            located = data["steps"][0]
            self.assertEqual(located["claim"]["text"], "Climate may move; nothing else moves.")
            self.assertEqual(located["claim"]["scope"][0]["indicators"], ["climate"])
            # mix moved 1.5 -> 2 in climate: as claimed; nothing moved in fossils
            self.assertEqual(
                data["counts"]["steps"]["located-factors"]["climate"]["verdicts"]["as claimed"], 1
            )
            # an install report that does not say where the countries' factors are refuses
            (provider / "logs" / "install-report.json").write_text(json.dumps({"coverage": {}}))
            with self.assertRaisesRegex(account.ChainError, "located_by_method"):
                account.chain(
                    comparison, records, scores, names, {}, steps, reach, units,
                    world=world, candidate=provider,
                )  # fmt: skip
        # a value that moved outside every reach where the comparison says all is explained
        # stops the file: the two must agree
        narrowed = {method: {} for method in reach}
        with self.assertRaisesRegex(account.ChainError, "outside the reach of every step"):
            account.chain(comparison, records, scores, names, {}, steps, narrowed, units)

    @unittest.skipUnless(
        importlib.util.find_spec("sentier_diagnostics"), "needs sentier-diagnostics"
    )
    def test_the_chain_and_the_comparison_count_what_nothing_explains_by_one_rule(self):
        """The comparison judges every value above its threshold, however small. The chain
        must not set such a value aside as "near zero", nor take the comparison's label
        "unexplained" for a step that reaches it."""
        import pandas as pd
        from release_build import diagnostics_account as account
        from sentier_diagnostics import fileformat

        comparison, records, _, names, steps, _, units = self.chain_inputs()
        rows = compare.compare_rows(self.base, self.cand, self.steps)
        seeds = compare.relevant_seeds(rows["rows"], self.effective, ["climate", "fossils"])
        graph = compare.consumer_graph(self.base[1], self.cand[1])
        index = pd.Index(["farm", "gas", "mix"], name="code")
        before = pd.DataFrame(
            {"climate": [300.0, 2.0, 1e-9], "fossils": [5.0, 36.0, 72.0]}, index=index
        )
        # "mix" goes from 1e-9 to 5e-9 in climate, and no step reaches it there. Beside
        # "gas" (2.0, in the same unit) it lies far below 1 % of the median size, the floor
        # sentier-diagnostics would set by itself.
        after = pd.DataFrame(
            {"climate": [1.0, 2.0, 5e-9], "fossils": [0.1, 0.0, 72.0]}, index=index
        )
        moved, reach = {}, {}
        scores = compare.compare_scores(before, after, seeds, graph, names, moved, reach)
        self.assertEqual(scores["unexplained_moves"], 1)
        tiny = comparison | {"scores": scores}
        tables = (before.to_dict(), after.to_dict())
        data = account.chain(tiny, records, tables, names, {}, steps, reach, units)
        self.assertEqual(fileformat.errors(data), [])
        climate = data["counts"]["steps"]["fixes"]["climate"]["verdicts"]
        self.assertEqual((climate["not claimed"], climate["as claimed"]), (1, 1))
        # the comparison's label among the reach, as it is when a row is unexplained: the
        # value is still not claimed
        labelled = {m: by | {account.UNEXPLAINED: {"mix"}} for m, by in reach.items()}
        again = account.chain(tiny, records, tables, names, {}, steps, labelled, units)
        self.assertEqual(again["counts"]["steps"]["fixes"]["climate"]["verdicts"]["not claimed"], 1)
        # and the two counts must be equal: a comparison that calls one value unexplained
        # where the chain finds none outside a reach is refused as well
        wider = {m: by | {AMOUNT: {"farm", "mix"}} for m, by in reach.items()}
        with self.assertRaisesRegex(account.ChainError, "0 values moved outside"):
            account.chain(tiny, records, tables, names, {}, steps, wider, units)

    def test_scores_are_read_exactly_on_both_sides(self):
        import tempfile

        from release_build import diagnostics_account as account

        # A default CSV reader reads this score one bit off. A change of one bit would then be
        # merged with no change, and a score the two sides read differently would read as one.
        written = "449.49106478873813"
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp)
            (build / "audit").mkdir()
            (build / "audit" / "scores.csv").write_text(f"code,climate\nfarm,{written}\n")
            exact = float(written)
            self.assertEqual(compare.read_scores(build).at["farm", "climate"], exact)
            self.assertEqual(
                account.scores_of(build, ["climate"], ["farm"])["climate"]["farm"], exact
            )

    @unittest.skipUnless(
        importlib.util.find_spec("sentier_diagnostics"), "needs sentier-diagnostics"
    )
    def test_each_fix_on_its_own_is_a_file_of_fixes_on_the_local_chain(self):
        from release_build import diagnostics_account as account
        from release_build import fixes_account
        from sentier_diagnostics import fixes, matrix

        comparison, records, scores, names, steps, reach, units = self.chain_inputs()
        data, full = account.chain(
            comparison, records, scores, names, {}, steps, reach, units, local=True
        )
        # the local chain: every dataset in its matrix, each claim with its list
        self.assertEqual(data["audience"], "local")
        self.assertEqual(matrix.against(full, data), [])
        self.assertEqual(data["steps"][0]["claim"]["scope"][0]["items"], ["farm"])
        before, after = scores
        summary = {
            "steps": [
                {"id": "location-codes", "kind": "import fix"},
                {"id": AMOUNT, "kind": "patch", "description": "Correct the disposal."},
                {"id": NAMES, "kind": "patch", "description": "Correct the names."},
                {"id": LOCATION, "kind": "patch", "description": "Correct the locations."},
            ]
        }
        # the comparison says which patches reach a result: those are built alone
        planned = fixes_account.plan(summary, comparison)
        self.assertEqual(
            [(b["id"], b["skip"], b["only"]) for b in planned["builds"]],
            [
                ("import-fixes", [AMOUNT, NAMES, LOCATION], None),
                (AMOUNT, None, [AMOUNT]),
                (NAMES, None, [NAMES]),
            ],
        )
        self.assertEqual(planned["not_built"], [LOCATION])
        # the patch to the amount alone moves the fruit, the names alone the gas and the mix
        alone_amount = {m: dict(v) for m, v in before.items()}
        alone_names = {m: dict(v) for m, v in before.items()}
        for method in before:
            alone_amount[method]["farm"] = after[method]["farm"]
            for code in ("gas", "mix"):
                alone_names[method][code] = after[method][code]
        index = {"builds": planned["builds"], "not_built": planned["not_built"]}

        built = {"import-fixes": before, AMOUNT: alone_amount, NAMES: alone_names}

        def made(every_fix=after, results=built):
            return fixes_account.fixes_file(
                data, full, summary, index,
                results=results,
                every_fix=every_fix,
                claims_of={
                    fixes_account.IMPORT_FIXES: fixes_account.claim_of({}, "Nothing moves.", "t"),
                    AMOUNT: fixes_account.claim_of(
                        fixes_account.step_reach(reach, {AMOUNT}), "The fruit may move.", "t"
                    ),
                    NAMES: fixes_account.claim_of(
                        fixes_account.step_reach(reach, {NAMES}), "The gas may move.", "t"
                    ),
                },
                pairs=[], tolerance=account.tolerance_of(comparison),
            )  # fmt: skip

        f = made()
        self.assertEqual(fixes.errors(f), [])
        self.assertEqual(fixes.against(f, data, full), [])
        self.assertEqual(
            [one["id"] for one in f["fixes"]], ["import-fixes", AMOUNT, NAMES, LOCATION]
        )
        self.assertTrue(all(one["requires"] == ["import-fixes"] for one in f["fixes"][1:]))
        # the base is BAFU's release, whose noise was not measured, and the release is the
        # chain's state after it
        self.assertEqual((f["of"]["base"], f["of"]["base_noise"]["measured"]), ("before", False))
        self.assertEqual([(b["id"], b["state"]) for b in f["built"]], [("patched", "after")])
        effect = {one["id"]: one["effect"] for one in f["fixes"]}
        self.assertEqual(effect["import-fixes"], {"climate": [], "fossils": []})
        self.assertEqual(effect[LOCATION], {"climate": [], "fossils": []})
        self.assertEqual(len(effect[AMOUNT]["climate"]), 1)
        # a patch alone is a build; two that were checked and are no pair add up exactly
        self.assertEqual(fixes.label(f, [AMOUNT]), fixes.BUILT)
        self.assertEqual(fixes.label(f, [AMOUNT, NAMES]), fixes.EXACT)
        self.assertEqual(fixes.chosen(f, [AMOUNT])[1], ["import-fixes"])
        both = fixes.compose(f, [AMOUNT, NAMES])["results"]
        # results are in the matrix's order of items, the worst first
        farm = [item[0] for item in full["items"]].index("farm")
        self.assertEqual(both["climate"][farm], after["climate"]["farm"])
        # a patched copy that is not the sum of its fixes is refused: two fixes called
        # independent are not
        wrong = {m: dict(v) for m, v in after.items()}
        wrong["climate"]["farm"] = 7.0
        with self.assertRaisesRegex(
            ValueError, "built set 'patched'.*independent, and they are not"
        ):
            made(every_fix=wrong)
        # also far below the size of the other values: every value is judged, with no floor
        # (the sum of the effects gives 1.0 for the fruit, the built copy says 2.9)
        small = {m: dict(v) for m, v in after.items()}
        small["climate"]["farm"] = 2.9
        with self.assertRaisesRegex(
            ValueError, "built set 'patched'.*independent, and they are not"
        ):
            made(every_fix=small)
        # results of a patch that was not built alone are refused
        with self.assertRaisesRegex(fixes_account.FixesError, "not built alone"):
            made(results=built | {LOCATION: before})

    def test_what_a_patch_changes_counts_only_the_rows_a_score_follows(self):
        """`changes_of`, on the made-up tables with their three patches: the amount patch
        changes an input, the names patch elementary flows, and the location patch only a
        field no score is computed from."""
        from release_build import fixes_account

        rows = compare.compare_rows(self.base, self.cand, self.steps)["rows"]
        amount = fixes_account.changes_of(rows, {AMOUNT})
        names = fixes_account.changes_of(rows, {NAMES})
        location = fixes_account.changes_of(rows, {LOCATION})
        self.assertTrue(amount["rows"] and amount["technosphere"] and not amount["emission"])
        self.assertTrue(names["rows"] and names["emission"] and not names["technosphere"])
        self.assertFalse(amount["rows"] & names["rows"])
        # the location patch did change rows, and none of them is one a score follows
        self.assertTrue(any(LOCATION in found for _, found in rows))
        self.assertEqual(location, {"rows": set(), "technosphere": False, "emission": False})
        both = fixes_account.changes_of(rows, {AMOUNT, NAMES})
        self.assertEqual(both["rows"], amount["rows"] | names["rows"])
        self.assertTrue(both["technosphere"] and both["emission"])
        # with two patches at hand, the pairs are found from what each changes and reaches
        changes = {AMOUNT: amount, NAMES: names}
        apart = {AMOUNT: {"farm"}, NAMES: {"gas", "mix"}}
        self.assertEqual(fixes_account.pairs_of([AMOUNT, NAMES], apart, changes), [])
        meeting = {AMOUNT: {"farm", "mix"}, NAMES: {"gas", "mix"}}
        self.assertEqual(len(fixes_account.pairs_of([AMOUNT, NAMES], meeting, changes)), 1)

    def test_a_patch_that_may_be_hidden_behind_another_is_built_alone(self):
        """The comparison names the narrowest patch that fits a changed row, by dataset. A
        wider patch on the same dataset is then left without a reach although it changed a
        field a score is computed from: it is built alone too, and its effect measured."""
        from release_build import fixes_account

        comparison = self.chain_inputs()[0]
        wider = {"flowData/exchange/@meanValue": 1, "flowData/exchange/@name": 1}
        summary = {
            "steps": [
                {"id": "location-codes", "kind": "import fix"},
                {"id": AMOUNT, "kind": "patch"},
                {"id": "0009-wider", "kind": "patch", "fields": wider},
                {"id": "0010-apart", "kind": "patch", "fields": wider},
                {"id": LOCATION, "kind": "patch", "fields": {"flowData/exchange/@location": 1}},
            ]
        }
        recorded = {
            "farm": ["location-codes", AMOUNT, "0009-wider", LOCATION],
            "mix": ["0010-apart"],
        }
        self.assertEqual(fixes_account.reached(comparison).get("0009-wider", 0), 0)
        planned = fixes_account.plan(summary, comparison, recorded)
        self.assertEqual(
            [b["id"] for b in planned["builds"]], ["import-fixes", AMOUNT, "0009-wider"]
        )
        self.assertEqual(planned["built_although_no_reach"], {"0009-wider": [AMOUNT, LOCATION]})
        # alone on its datasets, the comparison's word stands; a location is no score field
        self.assertEqual(planned["not_built"], ["0010-apart", LOCATION])
        # without the record of who changed which dataset, the plan is the comparison's
        plain = fixes_account.plan(summary, comparison)
        self.assertEqual([b["id"] for b in plain["builds"]], ["import-fixes", AMOUNT])
        self.assertEqual(plain["built_although_no_reach"], {})

    def test_two_patches_are_a_pair_where_their_changes_meet(self):
        from release_build import fixes_account
        from sentier_diagnostics import fixes

        a = {"rows": {("farm", 1)}, "technosphere": True, "emission": False}
        b = {"rows": {("gas", 1)}, "technosphere": False, "emission": True}
        c = {"rows": {("mix", 2)}, "technosphere": False, "emission": True}
        same = {"rows": {("farm", 1)}, "technosphere": True, "emission": False}
        self.assertEqual(fixes_account.pair_kind(a, same), fixes.SAME_ENTRY)
        self.assertEqual(fixes_account.pair_kind(a, b), fixes.TECHNOSPHERE_AND_EMISSION)
        # two changes to amounts of elementary flows in different rows add up exactly
        self.assertIsNone(fixes_account.pair_kind(b, c))
        changes = {"a": a, "b": b, "c": c}
        # a pair only where what the two reach overlaps
        reach = {"a": {"farm"}, "b": {"gas", "mix"}, "c": {"mix"}}
        self.assertEqual(fixes_account.pairs_of(["a", "b", "c"], reach, changes), [])
        reach["b"] = {"gas", "farm"}
        self.assertEqual(
            fixes_account.pairs_of(["a", "b", "c"], reach, changes),
            [fixes.pair("a", "b", fixes.TECHNOSPHERE_AND_EMISSION)],
        )

    def test_a_contribution_is_compared_with_the_patched_copy_under_its_own_name(self):
        from release_build import before_after_account

        patched = {"databases": {"inventory": "x-patched"}, "release": {"name": "X:2026"}}
        with_layer = patched | {
            "databases": {"inventory": "x-c7"},
            "contribution": {"id": "C7", "standing": "not authorised", "step": "C7-sea"},
        }
        title, before, after = before_after_account.sides(patched, with_layer)
        self.assertEqual(title, "The patched copy and contribution C7")
        self.assertEqual((before[0], after[0]), ("Patched copy", "Contribution C7"))
        self.assertIn("`x-patched`", before[1])
        self.assertIn("`x-c7`", after[1])
        self.assertIn("not authorised", after[1])

    def test_a_score_that_is_not_finite_has_moved_and_a_dataset_scored_once_stops_the_comparison(
        self,
    ):
        import pandas as pd

        index = pd.Index(["a", "b", "c", "d", "e"], name="code")
        nan, inf = float("nan"), float("inf")
        before = pd.DataFrame({"climate": [1.0, 1.0, 1.0, nan, inf]}, index=index)
        after = pd.DataFrame({"climate": [nan, inf, -inf, nan, inf]}, index=index)
        result = compare.compare_scores(before, after, {"climate": {}}, {}, {})
        (climate,) = result["methods"]
        # 1 to NaN, to +inf and to -inf have moved; NaN to NaN and inf to inf are the same.
        self.assertEqual(climate["datasets_moved"], 3)
        self.assertEqual(result["unexplained_moves"], 3)
        self.assertEqual(sorted(row["code"] for row in climate["moved"]), ["a", "b", "c"])
        self.assertEqual({row["after"] for row in climate["moved"]}, {"nan", "inf", "-inf"})
        self.assertEqual({row["change_percent"] for row in climate["moved"]}, {None})
        json.dumps(result, allow_nan=False)  # what is written is JSON
        # A dataset that one build scored and the other did not is not left out in silence.
        fewer = after.drop(index="e")
        with self.assertRaisesRegex(
            compare.CompareError, "1 only in the first, 0 only in the second"
        ):
            compare.compare_scores(before, fewer, {"climate": {}}, {}, {})
        with self.assertRaisesRegex(
            compare.CompareError, "0 only in the first, 1 only in the second"
        ):
            compare.compare_scores(fewer, before, {"climate": {}}, {}, {})

    def test_corrected_flows_are_listed_with_the_ef_flow_they_stay_on(self):
        receipt = {
            "source_observations": [
                {
                    "dataset": "gas",
                    "position": 1,
                    "declared": {"name": "Gas, natural/m3", "category": "resources"},
                    "patched": {"name": "Gas, natural", "category": "resources"},
                },
                {
                    "dataset": "farm",
                    "position": 2,
                    "declared": {"name": "Carbon dioxide", "category": "biotic"},
                    "patched": {"name": "Carbon dioxide", "category": "in air"},
                },
            ]
        }
        steps = {"gas": [NAMES], "farm": [COMPARTMENTS, AMOUNT]}
        result = compare.declared_flows(
            receipt, self.base[1], steps, self.bridge, {"ef-gas": "Natural Gas"}
        )
        self.assertEqual(
            (result["exchanges"], result["datasets"], result["unexplained"]), (2, 2, 0)
        )
        by_step = {flow["steps"][0]: flow for flow in result["flows"]}
        self.assertEqual(by_step[NAMES]["ef_3_1_flow"], ["Natural Gas"])
        self.assertTrue(by_step[NAMES]["linked_to_ef_3_1"])
        self.assertEqual(by_step[COMPARTMENTS]["ef_3_1_flow"], ["EF 3.1 flow ef-co2"])

        result = compare.declared_flows(receipt, self.base[1], {}, self.bridge, {})
        self.assertEqual(result["unexplained"], 2)
        self.assertEqual(
            compare.declared_flows({}, self.base[1], {}, self.bridge, {})["exchanges"], 0
        )

    def test_the_name_of_the_release_is_not_a_changed_row(self):
        processes = self.base[0].assign(source="bafu-2026", source_version="v1")
        patched = self.base[0].assign(source="bafu-2026-v1-patched", source_version="tree-1")
        summary = compare.compare_rows((processes, self.base[1]), (patched, self.base[1]), {})[
            "summary"
        ]
        self.assertEqual(summary["dataset_rows_changed_by_step"], {})
        self.assertEqual(summary["unexplained_count"], 0)

    def test_declared_supplier_location_is_compared_with_the_linked_dataset(self):
        before = compare.declared_against_linked(*self.base)
        after = compare.declared_against_linked(*self.cand)
        self.assertEqual(before["technosphere_inputs"], 3)
        self.assertEqual(before["without_a_linked_dataset"], 1)  # "waste" is not a dataset here
        self.assertEqual(before["no_declared_location"], 0)
        self.assertNotIn("declared_unit_differs", before)  # these tables carry no units
        self.assertEqual(
            before["declared_location_differs"] - after["declared_location_differs"], 1
        )

    def test_declared_units_are_compared_with_the_linked_datasets_unit(self):
        processes, exchanges = self.base
        processes = processes.assign(reference_unit=["kg", "MJ", "kWh"])
        exchanges = exchanges.assign(unit=["kg", "kg", "kg", "MJ", "Nm3", "kWh", "kWh", "p"])
        result = compare.declared_against_linked(processes, exchanges)
        # "mix" takes gas in kWh from a dataset in MJ, and fruit in p from a dataset in kg;
        # the input without a linked dataset is not counted
        self.assertEqual(result["declared_unit_differs"], 2)
        self.assertEqual(
            result["declared_and_linked_units"],
            {"kWh for a dataset in MJ": 1, "p for a dataset in kg": 1},
        )


class Guards(unittest.TestCase):
    """Two builds are compared only when a difference between them can be a step's."""

    def builds(self, tmp, first, second):
        import json

        made = []
        for name, record in (("first", first), ("second", second)):
            folder = Path(tmp) / name
            folder.mkdir()
            (folder / "build.json").write_text(json.dumps(record))
            made.append(folder)
        return made

    def refused(self, first, second):
        import contextlib
        import io
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            one, other = self.builds(tmp, first, second)
            with self.assertRaises(compare.CompareError) as raised:
                compare.compare(one, other)
            # and the command says so in one line, and writes no comparison
            out, said = Path(tmp) / "comparison.json", io.StringIO()
            with contextlib.redirect_stderr(said):
                code = compare.main(
                    [
                        str(one),
                        str(other),
                        "--out",
                        str(out),
                        "--before-after",
                        str(Path(tmp) / "b.json"),
                    ]
                )
            self.assertEqual(
                (code, out.exists(), (Path(tmp) / "b.json").exists()), (2, False, False)
            )
            self.assertIn("Comparison failed:", said.getvalue())
            self.assertNotIn("Traceback", said.getvalue())
        return str(raised.exception)

    def test_a_build_with_the_countries_factors_is_not_compared_with_one_without(self):
        why = self.refused({"install": {"located": True}}, {"install": {"located": False}})
        self.assertIn("that country's factor", why)
        # a build made before the rule says nothing, and did not apply it
        self.assertFalse(compare.located_of(Path("/nowhere")))
        self.assertIn("that country's factor", self.refused({"install": {"located": True}}, {}))

    def test_two_builds_of_two_linkings_are_not_compared(self):
        why = self.refused({"linking": compare.LINKINGS[0]}, {"linking": compare.LINKINGS[1]})
        self.assertIn("Compare two builds of one linking", why)

    def test_a_build_of_the_second_linking_without_its_file_says_so(self):
        linked = {"linking": compare.LINKINGS[1], "install": {"located": True}}
        why = self.refused(linked, linked)
        self.assertIn(compare.FLOW_LINKS, why)
        self.assertIn("before a build kept that file", why)


class Published(unittest.TestCase):
    def test_two_builds_are_put_side_by_side_only_when_both_were_compared(self):
        import json
        import tempfile

        def summary(share):
            categories = {"energy": {"compared": 9, "within_1_percent": share}}
            return {"joined": 9, "not_joined": 1, "categories": categories}

        with tempfile.TemporaryDirectory() as temp:
            base, cand = Path(temp) / "base", Path(temp) / "cand"
            base.mkdir()
            cand.mkdir()
            (base / "published-results.json").write_text(json.dumps(summary(97.75)))
            self.assertIsNone(compare.published_results(base, cand))
            (cand / "published-results.json").write_text(json.dumps(summary(11.56)))
            result = compare.published_results(base, cand)
        self.assertEqual(
            result["within_1_percent"]["energy"], {"baseline": 97.75, "candidate": 11.56}
        )
        self.assertEqual(result["not_joined"], {"baseline": 1, "candidate": 1})


if __name__ == "__main__":
    unittest.main()
