"""Checks for the benchmark page's score and runtime calculations."""

import unittest

from build import REVIEWERS, adjusted_reviewer_score, extract, page


SCENARIO_IDS = {
    "code-standards-reviewer": ("default",),
    "code-spec-reviewer": ("default",),
    "commit-audit-reviewer": ("default",),
    "spec-readiness-reviewer": ("runtime-migration", "artifact-promotion"),
}


def repetition(number, score, source="formal", corrected=False):
    return {"repetition": number, "score": score, "scoreSource": source,
            "mainAgentCorrectedScoringCopy": corrected}


class ScoreRulesTests(unittest.TestCase):
    def test_diagnostic_and_main_agent_correction_both_apply(self):
        role = {"repetitions": [repetition(1, 0.8, "diagnostic", True),
                                repetition(2, 0.6), repetition(3, 0.4)]}
        score, eligible = adjusted_reviewer_score(role)
        self.assertAlmostEqual(score, (0.8 * 0.9 + 0.6 + 0.4) / 3)
        self.assertEqual(eligible, {1, 2, 3})

    def test_status_and_excluded_score_apply_at_most_two_discounts(self):
        role = {"repetitions": [repetition(1, 0.8, "diagnostic", True),
                                repetition(2, 0), repetition(3, None, "unavailable")]}
        score, eligible = adjusted_reviewer_score(role)
        self.assertAlmostEqual(score, 0.8 * 0.9 * 0.9)
        self.assertEqual(eligible, {1})

    def test_main_agent_correction_alone_applies(self):
        role = {"repetitions": [repetition(1, 0.8, corrected=True),
                                repetition(2, 0.6), repetition(3, 0.4)]}
        score, _ = adjusted_reviewer_score(role)
        self.assertAlmostEqual(score, (0.8 * 0.9 + 0.6 + 0.4) / 3)

    def test_zero_and_unavailable_are_excluded_with_one_reviewer_penalty(self):
        role = {"repetitions": [repetition(1, 0.8),
                                repetition(2, 0, "diagnostic", True),
                                repetition(3, None, "unavailable")]}
        score, eligible = adjusted_reviewer_score(role)
        self.assertAlmostEqual(score, 0.8 * 0.9)
        self.assertEqual(eligible, {1})

    def test_missing_repetition_and_zero_share_one_reviewer_penalty(self):
        role = {"repetitions": [repetition(1, 0.8), repetition(3, 0)]}
        score, eligible = adjusted_reviewer_score(role)
        self.assertAlmostEqual(score, 0.8 * 0.9)
        self.assertEqual(eligible, {1})

    def test_missing_repetitions_keep_only_two_possible_discounts(self):
        role = {"repetitions": [repetition(2, 0.8, "diagnostic", True)]}
        score, eligible = adjusted_reviewer_score(role)
        self.assertAlmostEqual(score, 0.8 * 0.9 * 0.9)
        self.assertEqual(eligible, {2})

    def test_reviewer_without_positive_score_is_unavailable(self):
        role = {"repetitions": [repetition(1, 0), repetition(2, 0),
                                repetition(3, None, "unavailable")]}
        self.assertIsNone(adjusted_reviewer_score(role))


class ConfigurationRulesTests(unittest.TestCase):
    def fixture(self):
        configuration = {"model": "gpt-6-sol", "reasoningEffort": "low"}
        roles = []
        observations = []
        for reviewer_id, _, _ in REVIEWERS:
            scores = (0.5, 0, 1.0) if reviewer_id == "code-standards-reviewer" else (0.5,) * 3
            roles.append({"reviewerId": reviewer_id,
                          "repetitions": [repetition(number, score)
                                          for number, score in enumerate(scores, 1)]})
            for number in (1, 2, 3):
                for scenario in SCENARIO_IDS[reviewer_id]:
                    duration = (60_000, 120_000, 240_000)[number - 1]
                    if reviewer_id == "spec-readiness-reviewer":
                        duration //= 2
                    usage = {"input": duration // 1000, "cachedInput": 0, "output": 0}
                    # The early-return scenario must not affect displayed metrics.
                    if scenario == "runtime-migration":
                        duration = 9_000_000
                        usage = None
                    if reviewer_id == "code-standards-reviewer" and number == 2:
                        usage = None
                    observations.append({"reviewerId": reviewer_id, "repetition": number,
                                         "scenarioId": scenario,
                                         "runtime": {"durationMs": duration, "tokenUsage": usage}})
        return {"schemaVersion": 4, "configuration": configuration,
                "roles": roles, "observations": observations}

    def test_runtime_averages_only_positive_repetitions_per_reviewer(self):
        grouped, complete = extract([self.fixture()])
        self.assertEqual(len(grouped), 1)
        self.assertEqual(len(complete), 1)
        result = complete[0]
        self.assertAlmostEqual(result["score"], 53.5)
        self.assertAlmostEqual(result["minutes"], (2.5 + 7/3 + 7/3 + 7/6) / 4)
        self.assertAlmostEqual(result["tokenUsage"]["input"], 500 / 4)
        self.assertAlmostEqual(result["cost"], (500 * 2 / 1_000_000) / 4)
        self.assertEqual(result["costReviewerCount"], 4)

    def test_deepseek_prices_cached_and_uncached_input_separately(self):
        item = self.fixture()
        item["configuration"] = {"model": "deepseek-flash", "reasoningEffort": "max"}
        for observation in item["observations"]:
            observation["runtime"]["tokenUsage"] = {
                "input": 1_000_000, "cachedInput": 1_000_000, "output": 1_000_000}
        _, complete = extract([item])
        self.assertAlmostEqual(complete[0]["cost"], 1.1295)
        self.assertEqual(complete[0]["label"], "DeepSeek V4.1 Flash / max")
        self.assertEqual(complete[0]["costReviewerCount"], 4)

    def test_missing_tokens_in_positive_repetition_uses_other_repetition(self):
        item = self.fixture()
        item["observations"][0]["runtime"]["tokenUsage"] = None
        grouped, complete = extract([item])
        result = complete[0]
        self.assertAlmostEqual(result["minutes"], (2.5 + 7/3 + 7/3 + 7/6) / 4)
        self.assertAlmostEqual(grouped[0]["roles"]["code-standards-reviewer"]["tokenUsage"]["input"], 240)
        self.assertEqual(grouped[0]["roles"]["code-standards-reviewer"]["tokenRepetitionCount"], 1)
        self.assertAlmostEqual(result["tokenUsage"]["input"], 590 / 4)
        self.assertAlmostEqual(result["cost"], (590 * 2 / 1_000_000) / 4)
        self.assertEqual(result["costReviewerCount"], 4)

    def test_incomplete_token_set_excludes_whole_repetition(self):
        item = self.fixture()
        usage = item["observations"][0]["runtime"]["tokenUsage"]
        usage["output"] = 30
        del usage["cachedInput"]
        grouped, _ = extract([item])
        role = grouped[0]["roles"]["code-standards-reviewer"]
        self.assertEqual(role["tokenRepetitionCount"], 1)
        self.assertEqual(role["tokenUsage"], {"input": 240, "cachedInput": 0, "output": 0})

    def test_no_complete_token_set_omits_only_that_reviewer_tokens_and_cost(self):
        item = self.fixture()
        for observation in item["observations"]:
            if observation["reviewerId"] == "code-standards-reviewer":
                observation["runtime"]["tokenUsage"] = None
        grouped, complete = extract([item])
        self.assertIsNone(grouped[0]["roles"]["code-standards-reviewer"]["tokenUsage"])
        self.assertAlmostEqual(complete[0]["tokenUsage"]["input"], 350 / 3)
        self.assertEqual(complete[0]["costReviewerCount"], 3)
        self.assertEqual(complete[0]["timeReviewerCount"], 4)

    def test_missing_duration_averages_other_positive_repetitions(self):
        item = self.fixture()
        item["observations"][0]["runtime"]["durationMs"] = None
        grouped, complete = extract([item])
        result = complete[0]
        self.assertAlmostEqual(grouped[0]["roles"]["code-standards-reviewer"]["minutes"], 4)
        self.assertAlmostEqual(result["minutes"], (4 + 7/3 + 7/3 + 7/6) / 4)
        self.assertEqual(result["timeReviewerCount"], 4)
        self.assertEqual(result["tokenReviewerCount"], 4)

    def test_no_usable_duration_omits_only_that_reviewer_time(self):
        item = self.fixture()
        for observation in item["observations"]:
            if observation["reviewerId"] == "code-standards-reviewer":
                observation["runtime"]["durationMs"] = None
        grouped, complete = extract([item])
        self.assertIsNone(grouped[0]["roles"]["code-standards-reviewer"]["minutes"])
        self.assertAlmostEqual(complete[0]["minutes"], (7/3 + 7/3 + 7/6) / 3)
        self.assertEqual(complete[0]["timeReviewerCount"], 3)
        self.assertEqual(complete[0]["tokenReviewerCount"], 4)

    def test_missing_normal_scenario_keeps_other_time_repetition(self):
        item = self.fixture()
        item["observations"] = [observation for observation in item["observations"]
                                if not (observation["reviewerId"] == "code-standards-reviewer"
                                        and observation["repetition"] == 1)]
        grouped, complete = extract([item])
        self.assertAlmostEqual(grouped[0]["roles"]["code-standards-reviewer"]["minutes"], 4)
        self.assertAlmostEqual(grouped[0]["roles"]["code-standards-reviewer"]["tokenUsage"]["input"], 240)
        self.assertEqual(complete[0]["timeReviewerCount"], 4)
        self.assertEqual(complete[0]["tokenReviewerCount"], 4)

    def test_missing_runtime_keeps_other_positive_repetition(self):
        item = self.fixture()
        item["observations"][0]["runtime"] = None
        grouped, complete = extract([item])
        role = grouped[0]["roles"]["code-standards-reviewer"]
        self.assertAlmostEqual(role["minutes"], 4)
        self.assertEqual(role["tokenUsage"], {"input": 240, "cachedInput": 0, "output": 0})
        self.assertEqual(complete[0]["timeReviewerCount"], 4)
        self.assertEqual(complete[0]["tokenReviewerCount"], 4)

    def test_missing_score_repetition_preserves_reviewer_metrics(self):
        item = self.fixture()
        role = next(role for role in item["roles"]
                    if role["reviewerId"] == "code-standards-reviewer")
        role["repetitions"] = [repetition(1, 0.5), repetition(2, 0)]
        grouped, complete = extract([item])
        standard = grouped[0]["roles"]["code-standards-reviewer"]
        self.assertAlmostEqual(standard["score"], 0.5 * 0.9)
        self.assertAlmostEqual(standard["minutes"], 1)
        self.assertEqual(standard["tokenUsage"]["input"], 60)
        self.assertAlmostEqual(complete[0]["score"], 49)

    def test_zero_and_missing_reviewers_keep_their_weight_as_zero(self):
        item = self.fixture()
        item["roles"] = [role for role in item["roles"]
                         if role["reviewerId"] != "commit-audit-reviewer"]
        code_spec = next(role for role in item["roles"]
                         if role["reviewerId"] == "code-spec-reviewer")
        code_spec["repetitions"] = [repetition(number, 0) for number in (1, 2, 3)]
        grouped, complete = extract([item])
        self.assertAlmostEqual(complete[0]["score"], 31.0)
        self.assertEqual(grouped[0]["roles"]["code-spec-reviewer"]["score"], 0)
        self.assertEqual(grouped[0]["roles"]["commit-audit-reviewer"]["score"], 0)
        self.assertEqual(complete[0]["timeReviewerCount"], 2)
        self.assertAlmostEqual(complete[0]["minutes"], (2.5 + 7/6) / 2)

    def test_spec_readiness_uses_only_full_review_scenario(self):
        item = self.fixture()
        item["observations"] = [observation for observation in item["observations"]
                                if observation["scenarioId"] != "runtime-migration"]
        grouped, complete = extract([item])
        role = grouped[0]["roles"]["spec-readiness-reviewer"]
        self.assertAlmostEqual(role["minutes"], 7/6)
        self.assertAlmostEqual(role["tokenUsage"]["input"], 70)
        self.assertAlmostEqual(complete[0]["score"], 53.5)
        self.assertEqual(complete[0]["costReviewerCount"], 4)

    def test_version_three_is_rejected(self):
        item = self.fixture()
        item["schemaVersion"] = 3
        with self.assertRaisesRegex(ValueError, "schema-version-4"):
            page([item])


if __name__ == "__main__":
    unittest.main()
