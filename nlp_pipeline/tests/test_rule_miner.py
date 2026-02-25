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

    # --- New colloquial pattern tests ---
    def test_nothing_new(self, miner):
        result = miner.match_text("there's nothing new about this song lol")
        assert result["STANDARDIZATION"].matched

    def test_copy_paste_music(self, miner):
        result = miner.match_text("this is copy paste pop music fr")
        assert result["STANDARDIZATION"].matched

    def test_same_old_stuff(self, miner):
        result = miner.match_text("same old shit different album")
        assert result["STANDARDIZATION"].matched

    def test_heard_this_before(self, miner):
        result = miner.match_text("i swear ive heard this before")
        assert result["STANDARDIZATION"].matched

    def test_sounds_like_everything_else(self, miner):
        result = miner.match_text("sounds like everything else on the radio")
        assert result["STANDARDIZATION"].matched

    def test_rinse_and_repeat(self, miner):
        result = miner.match_text("rinse and repeat, same trash every year")
        assert result["STANDARDIZATION"].matched

    def test_trash_music(self, miner):
        result = miner.match_text("trash music, nothing worth listening to")
        assert result["STANDARDIZATION"].matched

    def test_repetitive(self, miner):
        result = miner.match_text("this song sounds pretty repetitive to me now")
        assert result["STANDARDIZATION"].matched

    def test_soulless(self, miner):
        result = miner.match_text("soulless pop with no heart")
        assert result["STANDARDIZATION"].matched

    # --- Negation / false-positive tests ---
    def test_generic_comment_not_matched(self, miner):
        result = miner.match_text("this is a generic comment")
        assert not result["STANDARDIZATION"].matched or result["STANDARDIZATION"].negated

    def test_great_formula_not_matched(self, miner):
        result = miner.match_text("they perfected the formula, love the template")
        assert not result["STANDARDIZATION"].matched or result["STANDARDIZATION"].negated

    def test_never_heard_before_not_matched(self, miner):
        """'Never heard this before' is discovery, not critique."""
        result = miner.match_text("I have never heard this before, but just now my new kitten stepped on my radio")
        assert not result["STANDARDIZATION"].matched or result["STANDARDIZATION"].negated


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

    # --- New colloquial pattern tests ---
    def test_sold_their_soul(self, miner):
        result = miner.match_text("they sold their soul for a hit record")
        assert result["COMMODIFICATION_MARKET_LOGIC"].matched

    def test_fake_streams(self, miner):
        result = miner.match_text("bot views and bought streams for sure")
        assert result["COMMODIFICATION_MARKET_LOGIC"].matched

    def test_spotify_pushing(self, miner):
        result = miner.match_text("spotify is pushing this on everyone's playlist")
        assert result["COMMODIFICATION_MARKET_LOGIC"].matched

    def test_tiktok_bait(self, miner):
        result = miner.match_text("this is tiktok bait disguised as music")
        assert result["COMMODIFICATION_MARKET_LOGIC"].matched

    # --- Negation / false-positive tests ---
    def test_sold_out_arena_not_matched(self, miner):
        result = miner.match_text("she sold out the arena in 2 minutes")
        assert not result["COMMODIFICATION_MARKET_LOGIC"].matched or result["COMMODIFICATION_MARKET_LOGIC"].negated

    def test_sold_out_concert_not_matched(self, miner):
        result = miner.match_text("they sold out the concert instantly")
        assert not result["COMMODIFICATION_MARKET_LOGIC"].matched or result["COMMODIFICATION_MARKET_LOGIC"].negated


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

    # --- New colloquial pattern tests ---
    def test_brain_rot(self, miner):
        result = miner.match_text("this is brainrot for the masses")
        assert result["REGRESSIVE_LISTENING"].matched

    def test_vibes_no_substance(self, miner):
        result = miner.match_text("just vibes no substance whatsoever")
        assert result["REGRESSIVE_LISTENING"].matched

    def test_nobody_listens_full_albums(self, miner):
        result = miner.match_text("nobody listens to full albums anymore smh")
        assert result["REGRESSIVE_LISTENING"].matched

    def test_this_generation(self, miner):
        result = miner.match_text("this generation doesn't appreciate real music")
        assert result["REGRESSIVE_LISTENING"].matched

    # --- Negation / false-positive tests ---
    def test_what_background_music_not_matched(self, miner):
        """Asking 'what's the background music?' should not match."""
        result = miner.match_text("what is the background music in this video")
        assert not result["REGRESSIVE_LISTENING"].matched or result["REGRESSIVE_LISTENING"].negated

    def test_good_background_music_not_matched(self, miner):
        """'good background music' is praise, not critique."""
        result = miner.match_text("great background music for studying")
        assert not result["REGRESSIVE_LISTENING"].matched or result["REGRESSIVE_LISTENING"].negated


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

    # --- New colloquial pattern tests ---
    def test_fake_deep(self, miner):
        result = miner.match_text("this song is so fake deep lmao")
        assert result["AFFECTIVE_PREPACKAGING"].matched

    def test_trying_hard_to_be_sad(self, miner):
        result = miner.match_text("trying so hard to be sad it's cringe")
        assert result["AFFECTIVE_PREPACKAGING"].matched

    def test_trauma_for_clout(self, miner):
        result = miner.match_text("using trauma for clout is disgusting")
        assert result["AFFECTIVE_PREPACKAGING"].matched

    def test_milking_nostalgia(self, miner):
        result = miner.match_text("they keep milking the nostalgia")
        assert result["AFFECTIVE_PREPACKAGING"].matched

    # --- Negation / false-positive tests ---
    def test_relationship_manipulation_not_matched(self, miner):
        """Interpersonal manipulation should not match as music critique."""
        result = miner.match_text("he was manipulating her the whole time")
        assert not result["AFFECTIVE_PREPACKAGING"].matched or result["AFFECTIVE_PREPACKAGING"].negated

    def test_autotune_manipulation_not_matched(self, miner):
        """Auto-tune manipulation is COMMODIFICATION, not AFFECTIVE."""
        result = miner.match_text("It's basically K-Pop's signature = Auto-tune manipulation & synthetic vocals")
        assert not result["AFFECTIVE_PREPACKAGING"].matched or result["AFFECTIVE_PREPACKAGING"].negated


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

    # --- New colloquial pattern tests ---
    def test_ahead_of_their_time(self, miner):
        result = miner.match_text("this artist is ahead of their time fr")
        assert result["FORMAL_RESISTANCE"].matched

    def test_writes_own_music(self, miner):
        result = miner.match_text("she actually writes her own songs unlike most pop stars")
        assert result["FORMAL_RESISTANCE"].matched

    def test_underrated_standalone(self, miner):
        result = miner.match_text("this performance is underrated I did not expect it to be this good")
        assert result["FORMAL_RESISTANCE"].matched

    def test_this_is_real_music(self, miner):
        result = miner.match_text("this is real music, not that auto-tune stuff")
        assert result["FORMAL_RESISTANCE"].matched

    def test_real_music_standalone(self, miner):
        result = miner.match_text("those classics were real music")
        assert result["FORMAL_RESISTANCE"].matched

    def test_doesnt_follow_trends(self, miner):
        result = miner.match_text("he doesn't follow trends, he sets them")
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

    # --- New colloquial pattern tests ---
    def test_walmart_version(self, miner):
        result = miner.match_text("she's the walmart version of Beyonce")
        assert result["PSEUDO_INDIVIDUALIZATION"].matched

    def test_same_music_different_name(self, miner):
        result = miner.match_text("same music different name, they're all the same")
        assert result["PSEUDO_INDIVIDUALIZATION"].matched

    def test_manufactured_pop_star(self, miner):
        result = miner.match_text("just another manufactured pop star with no talent")
        assert result["PSEUDO_INDIVIDUALIZATION"].matched

    def test_all_vibes_no_substance(self, miner):
        result = miner.match_text("all vibes no substance, just an aesthetic")
        assert result["PSEUDO_INDIVIDUALIZATION"].matched

    # --- Negation / false-positive test ---
    def test_actually_unique_not_matched(self, miner):
        result = miner.match_text("she's actually unique and different from everyone else")
        assert not result["PSEUDO_INDIVIDUALIZATION"].matched or result["PSEUDO_INDIVIDUALIZATION"].negated


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

    def test_multi_label_match(self, miner):
        """A comment can match multiple categories simultaneously."""
        result = miner.match_text("cookie cutter manufactured pop star with fake emotion")
        matched_labels = [l for l, m in result.items() if m.matched]
        assert len(matched_labels) >= 2
