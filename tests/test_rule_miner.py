"""Tests for the rule mining module."""

import pytest

from src.rule_miner import RuleMiner, RuleMatch


@pytest.fixture
def miner():
    """Create a RuleMiner with default config."""
    return RuleMiner()


class TestRuleMinerInit:
    def test_loads_rules(self, miner):
        assert len(miner._rules) > 0

    def test_has_all_labels(self, miner):
        expected = {
            "STANDARDIZATION",
            "PSEUDO_INDIVIDUALIZATION",
            "COMMODIFICATION_MARKET_LOGIC",
            "REGRESSIVE_LISTENING",
            "AFFECTIVE_PREPACKAGING",
            "FORMAL_RESISTANCE",
        }
        assert expected == set(miner._rules.keys())


class TestStandardization:
    def test_all_songs_sound_same(self, miner):
        result = miner.match_text("all these songs sound the same")
        assert result["STANDARDIZATION"].matched

    def test_formulaic(self, miner):
        result = miner.match_text("this is such formulaic pop music")
        assert result["STANDARDIZATION"].matched

    def test_cookie_cutter(self, miner):
        result = miner.match_text("cookie cutter music, nothing original")
        assert result["STANDARDIZATION"].matched

    def test_negation_not_generic(self, miner):
        result = miner.match_text("this is not generic at all, very original")
        assert not result["STANDARDIZATION"].matched or result["STANDARDIZATION"].negated

    def test_no_match_simple_praise(self, miner):
        result = miner.match_text("I love this song so much!")
        assert not result["STANDARDIZATION"].matched


class TestCommodification:
    def test_algorithm_bait(self, miner):
        result = miner.match_text("this is pure algorithm bait garbage")
        assert result["COMMODIFICATION_MARKET_LOGIC"].matched

    def test_industry_plant(self, miner):
        result = miner.match_text("obvious industry plant getting pushed by the label")
        assert result["COMMODIFICATION_MARKET_LOGIC"].matched

    def test_made_for_tiktok(self, miner):
        result = miner.match_text("made for tiktok not for real music fans")
        assert result["COMMODIFICATION_MARKET_LOGIC"].matched

    def test_sell_out(self, miner):
        result = miner.match_text("what a sell-out move")
        assert result["COMMODIFICATION_MARKET_LOGIC"].matched


class TestRegressiveListening:
    def test_background_music(self, miner):
        result = miner.match_text("this is just background music, nothing more")
        assert result["REGRESSIVE_LISTENING"].matched

    def test_brain_dead(self, miner):
        result = miner.match_text("brain dead music for brain dead listeners")
        assert result["REGRESSIVE_LISTENING"].matched

    def test_mindless(self, miner):
        result = miner.match_text("mindless consumption at its finest")
        assert result["REGRESSIVE_LISTENING"].matched


class TestAffectivePrepackaging:
    def test_manufactured_emotion(self, miner):
        result = miner.match_text("manufactured sadness, fake emotion designed to make you cry")
        assert result["AFFECTIVE_PREPACKAGING"].matched

    def test_emotional_manipulation(self, miner):
        result = miner.match_text("this is pure emotional manipulation of the audience")
        assert result["AFFECTIVE_PREPACKAGING"].matched

    def test_weaponized_nostalgia(self, miner):
        result = miner.match_text("weaponized nostalgia at its finest")
        assert result["AFFECTIVE_PREPACKAGING"].matched


class TestFormalResistance:
    def test_breaks_the_mold(self, miner):
        result = miner.match_text("this really breaks the mold of modern pop")
        assert result["FORMAL_RESISTANCE"].matched

    def test_unconventional(self, miner):
        result = miner.match_text("genuinely unconventional production choices here")
        assert result["FORMAL_RESISTANCE"].matched

    def test_complex_arrangement(self, miner):
        result = miner.match_text("the complex arrangement rewards repeated listens")
        assert result["FORMAL_RESISTANCE"].matched


class TestPseudoIndividualization:
    def test_illusion_of_choice(self, miner):
        result = miner.match_text("it's all an illusion of choice")
        assert result["PSEUDO_INDIVIDUALIZATION"].matched

    def test_style_over_substance(self, miner):
        result = miner.match_text("pure style over substance, no real artistry")
        assert result["PSEUDO_INDIVIDUALIZATION"].matched

    def test_manufactured_identity(self, miner):
        result = miner.match_text("manufactured identity with no genuine distinction")
        assert result["PSEUDO_INDIVIDUALIZATION"].matched


class TestEdgeCases:
    def test_empty_text(self, miner):
        result = miner.match_text("")
        assert all(not m.matched for m in result.values())

    def test_emoji_only(self, miner):
        result = miner.match_text("🔥🔥🔥💯")
        assert all(not m.matched for m in result.values())

    def test_very_long_text(self, miner):
        text = "This song is " + "really " * 500 + "good"
        result = miner.match_text(text)
        # Should not crash, just not match
        assert isinstance(result, dict)

    def test_spans_returned(self, miner):
        result = miner.match_text("all songs sound the same these days")
        if result["STANDARDIZATION"].matched:
            assert len(result["STANDARDIZATION"].spans) > 0
            # Each span is (start, end, matched_text)
            span = result["STANDARDIZATION"].spans[0]
            assert len(span) == 3
            assert isinstance(span[0], int)
            assert isinstance(span[1], int)
            assert isinstance(span[2], str)

    def test_confidence_returned(self, miner):
        result = miner.match_text("formulaic pop music")
        if result["STANDARDIZATION"].matched:
            assert result["STANDARDIZATION"].confidence > 0.0
            assert result["STANDARDIZATION"].confidence <= 1.0
