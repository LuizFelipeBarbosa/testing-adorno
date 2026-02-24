"""Stage 3: Embedding-based semantic retrieval for critique detection.

Builds a prototype bank per label (curated example comments that exemplify
each critique category) and computes cosine similarity between incoming
comments and prototypes to produce soft label signals.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from src.utils.io_utils import load_yaml, load_json, save_json, ensure_dir, project_root
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Prototype bank: curated examples per label
# ---------------------------------------------------------------------------

DEFAULT_PROTOTYPES: dict[str, list[str]] = {
    "STANDARDIZATION": [
        "All these songs sound exactly the same, just different singers",
        "This is the same beat every pop song uses, nothing new",
        "Every song on the radio follows the exact same formula",
        "Copy paste music, zero originality in the structure",
        "They literally use the same chord progression every time",
        "This could be any pop song from the last 5 years, completely interchangeable",
        "Generic pop formula: verse chorus verse chorus bridge chorus fade",
        "I can predict every note before it plays, so formulaic",
        "Music industry just recycles the same template over and over",
        "This is cookie cutter pop at its most blatant",
        "Sounds like everything else on Spotify's top 50",
        "No originality, just another song following the hit formula",
        "Swap the vocals and you wouldn't know which song is which",
        "The production is identical to every other track this year",
        "Manufactured on an assembly line, not a studio",
        "How many times can they release the same song with different words",
        "Pop music is dead, it's all the same recycled garbage",
        "Another day another formulaic hit designed by committee",
        "This beat has been used in literally 50 songs this year",
        "Paint by numbers pop music at its finest",
        "Radio pop is just one big copy paste operation",
        "Same structure same sounds same everything different name",
        "You could shuffle all these songs together and nobody would notice",
        "When every song sounds the same what's the point of new releases",
        "Standardized mass produced music pretending to be art",
        "Heard this exact same melody arrangement in three other songs this month",
        "The music industry has one formula and they never deviate",
        "This is what happens when AI could literally write your music",
        "Indistinguishable from every other chart topper",
        "They found a formula that works and just keep milking it",
    ],
    "PSEUDO_INDIVIDUALIZATION": [
        "She's marketed as unique but sounds like every other pop star",
        "Different aesthetic same music, it's all branding",
        "The only thing different is the packaging, the music is identical",
        "They just slap a new image on the same product",
        "Her 'unique style' is literally manufactured by the same team",
        "Illusion of choice - all these artists are made in the same factory",
        "The industry creates fake personas to sell identical music",
        "Style over substance, the brand is more important than the art",
        "Just another manufactured identity with no real artistic distinction",
        "Strip away the image and there's nothing original underneath",
        "They pretend to be alternative but it's the same mainstream formula",
        "The 'indie' aesthetic is just another marketing strategy",
        "Different wrapper same candy inside",
        "Every artist has their 'unique sound' that sounds exactly like everyone else",
        "The persona is the product not the music",
        "Fake authenticity is the new marketing strategy",
        "They sell you individuality that was designed by a committee",
        "The branding is unique the music is not",
        "Pseudo-rebel aesthetic masking total conformity",
        "Different flavor of the same ice cream",
        "Her brand of uniqueness is carefully manufactured",
        "All these artists are interchangeable behind the marketing",
        "The aesthetic variety masks the musical uniformity",
        "They give each artist a different costume but the same script",
        "So-called artistic identity is just market positioning",
        "Pretending to be authentic while being completely manufactured",
        "The image is curated the music is standardized",
        "Same product different brand ambassador",
        "Fake indie vibes on a major label budget",
        "The uniqueness is only skin deep",
    ],
    "COMMODIFICATION_MARKET_LOGIC": [
        "This was clearly made to game the Spotify algorithm",
        "Industry plant getting pushed by the label",
        "Made for TikTok not for actual music lovers",
        "This song exists only because it's optimized for streaming numbers",
        "Chart manipulation at its finest, bought streams",
        "The music industry is just a content factory now",
        "Everything is about playlist placement not artistry",
        "Sell out, this is pure commercial product",
        "Music as content, not as art - just feed the algorithm",
        "This only got popular because of label money and payola",
        "Viral bait designed for 15 second clips",
        "They don't make music they make content for engagement metrics",
        "Stream farming and playlist politics is all that matters now",
        "The song is a product the listener is the consumer",
        "Corporate music designed by data scientists not musicians",
        "Clout chasing disguised as artistry",
        "This exists to sell merch and concert tickets not to be listened to",
        "Algorithm fodder, designed to hit specific streaming thresholds",
        "The charts don't reflect taste they reflect marketing budgets",
        "Music reduced to a commodity traded on streaming platforms",
        "This got big because of the algorithm not because it's good",
        "Label push is doing all the heavy lifting here",
        "Optimized for maximum playlist coverage minimum artistic risk",
        "Cash grab single designed to go viral and be forgotten",
        "The song is just an ad for the brand at this point",
        "Spotify curated music as a product line",
        "Chart position is bought not earned anymore",
        "This is what music sounds like when it's designed by marketers",
        "Pure commercial calculation zero artistic intent",
        "Content mill pop designed for passive streaming revenue",
    ],
    "REGRESSIVE_LISTENING": [
        "Nobody actually listens to the lyrics they just vibe to it",
        "Perfect background music, doesn't require any thought",
        "People just put this on shuffle and zone out",
        "Music for people who don't actually listen to music",
        "This generation can't even sit through a full album",
        "Brain dead listening, no engagement with the actual music",
        "Everyone just skips after 30 seconds anyway",
        "Designed for passive consumption not active listening",
        "People don't listen anymore they just stream",
        "Background noise for scrolling through your phone",
        "The attention span is gone, music is just filler now",
        "Nobody appreciates music anymore just consumes it",
        "Elevator music for the streaming age",
        "Mindless listening, in one ear out the other",
        "People treat music like wallpaper now",
        "Short attention span generation doesn't deserve good music",
        "They skip to the chorus and that's all they know",
        "Music is just content to consume between TikTok videos",
        "Nobody sits down and actually listens to an album start to finish anymore",
        "Passive consumption has killed music appreciation",
        "This is for people who have music on but aren't really listening",
        "The 15 second preview is all most people need",
        "Listeners have become consumers not audiences",
        "Zero attention paid to craft or composition just vibes",
        "Music as ambient noise not as an experience",
        "People stream this while doing something else entirely",
        "The death of active listening summarized in one song",
        "Nobody cares about the artistry just the aesthetic",
        "Zombie listening mode engaged",
        "Goldfish memory generation can't engage with music deeply",
    ],
    "AFFECTIVE_PREPACKAGING": [
        "This is manufactured sadness, designed to make you cry on command",
        "Fake emotion, the producers engineered every feeling",
        "Calculated emotional manipulation, not genuine expression",
        "The sadness is as real as the autotune",
        "Pre-packaged emotions for mass consumption",
        "They know exactly which chord progression triggers which feeling",
        "Weaponized nostalgia designed by a marketing team",
        "The vulnerability is performative, just another selling point",
        "Engineered to hit you right in the feels for streaming numbers",
        "Emotional manipulation disguised as artistry",
        "Crocodile tears set to a beat",
        "This isn't real emotion it's a formula for making people feel something",
        "The emotional response is designed not organic",
        "Synthetic feelings in a synthetic song",
        "Prefab sadness for people who want to feel something without the work",
        "The emotion is as manufactured as the beat",
        "Designed to trigger an emotional response not express one",
        "Performative vulnerability is the new trend",
        "They've reduced human emotion to a production technique",
        "The feelings are pre-packaged like fast food",
        "Commodified emotion sold as authentic expression",
        "The tearjerker formula is getting predictable",
        "Manufactured catharsis for the masses",
        "This song emotionally manipulates you and people celebrate it",
        "Canned feelings, assembly line sadness",
        "The emotion is calculated not felt by the artist",
        "Designed to be the soundtrack for crying TikToks",
        "Fake deep lyrics designed to seem meaningful",
        "The vulnerability is a brand not a feeling",
        "Algorithmic emotion optimization at its peak",
    ],
    "FORMAL_RESISTANCE": [
        "Finally something that actually challenges the listener",
        "This breaks every rule of pop music and that's what makes it great",
        "The structure is genuinely complex, not your typical verse chorus",
        "This refuses to be easy listening and I love it",
        "Actual artistry and innovation in the arrangement",
        "Bold choice to make something this uncomfortable for mainstream",
        "This doesn't pander to the algorithm, genuine creative risk",
        "The dissonance is intentional and it works beautifully",
        "This song demands your attention, you can't just background it",
        "Real experimentation in a sea of formula",
        "The production is genuinely avant-garde for pop music",
        "Unconventional song structure that actually rewards repeated listens",
        "This is what happens when artists take real creative risks",
        "Refreshingly anti-formula, doesn't follow any template",
        "The complexity here is incredible layers on layers",
        "Boundary pushing production that challenges expectations",
        "This is genuine art not product, demands active engagement",
        "Genre-bending in a way that feels authentic not calculated",
        "The tension in this composition is genuinely sophisticated",
        "Daring to be difficult in the age of easy consumption",
        "Actual musical innovation not just marketing innovation",
        "This resists easy categorization which is the whole point",
        "Intricate arrangement that reveals new details every listen",
        "Bold artistic vision that doesn't compromise for accessibility",
        "This fights against the homogenization of pop music",
        "Real compositional depth, not surface-level complexity",
        "Challenging music that respects the listener's intelligence",
        "The harmonic choices here are genuinely surprising and earned",
        "Anti-pop in the best way, refuses to be consumed passively",
        "Brave enough to be weird in a conformist landscape",
    ],
}


@dataclass
class EmbeddingMatch:
    """Result of embedding similarity for one label."""

    label: str
    score: float  # max cosine similarity to prototype bank
    nearest_prototype: str  # text of nearest prototype
    top_k_scores: list[float] = field(default_factory=list)


class EmbeddingRetriever:
    """Computes semantic similarity between comments and per-label prototype banks."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        prototypes: dict[str, list[str]] | None = None,
        prototype_path: str | Path | None = None,
        normalize: bool = True,
    ):
        self.model_name = model_name
        self.normalize = normalize
        self._model = None
        self._prototype_embeddings: dict[str, np.ndarray] = {}
        self._prototype_texts: dict[str, list[str]] = {}

        # Load prototypes
        if prototype_path and Path(prototype_path).exists():
            loaded = load_json(prototype_path)
            self._prototype_texts = loaded
            logger.info("Loaded prototypes from %s", prototype_path)
        elif prototypes is not None:
            self._prototype_texts = prototypes
        else:
            self._prototype_texts = DEFAULT_PROTOTYPES
            logger.info("Using default prototype bank (%d labels)", len(DEFAULT_PROTOTYPES))

    @property
    def model(self):
        """Lazy-load the sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
                logger.info("Loaded embedding model: %s", self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    def build_prototype_bank(self) -> None:
        """Encode all prototypes and cache embeddings."""
        for label, texts in self._prototype_texts.items():
            if not texts:
                logger.warning("No prototypes for label %s, skipping", label)
                continue
            embs = self.model.encode(texts, normalize_embeddings=self.normalize)
            self._prototype_embeddings[label] = np.array(embs)
            logger.info(
                "Built prototype bank for %s: %d prototypes, dim=%d",
                label,
                len(texts),
                embs.shape[1],
            )

    def save_prototypes(self, path: str | Path) -> None:
        """Save prototype texts to JSON."""
        save_json(self._prototype_texts, path)
        logger.info("Saved prototypes to %s", path)

    def encode_texts(self, texts: list[str], batch_size: int = 256) -> np.ndarray:
        """Encode a batch of texts into embeddings."""
        return self.model.encode(
            texts,
            normalize_embeddings=self.normalize,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 1000,
        )

    def match_single(
        self, text: str, top_k: int = 3
    ) -> dict[str, EmbeddingMatch]:
        """Compute similarity of a single text against all prototype banks."""
        if not self._prototype_embeddings:
            self.build_prototype_bank()

        emb = self.model.encode([text], normalize_embeddings=self.normalize)[0]
        results: dict[str, EmbeddingMatch] = {}

        for label, proto_embs in self._prototype_embeddings.items():
            sims = proto_embs @ emb  # cosine similarity (both normalized)
            top_indices = np.argsort(sims)[::-1][:top_k]
            top_scores = sims[top_indices].tolist()
            best_idx = top_indices[0]

            results[label] = EmbeddingMatch(
                label=label,
                score=float(sims[best_idx]),
                nearest_prototype=self._prototype_texts[label][best_idx],
                top_k_scores=top_scores,
            )

        return results

    def match_batch(
        self,
        texts: list[str],
        batch_size: int = 256,
        top_k: int = 3,
    ) -> list[dict[str, EmbeddingMatch]]:
        """Compute similarity for a batch of texts against all prototype banks."""
        if not self._prototype_embeddings:
            self.build_prototype_bank()

        embeddings = self.encode_texts(texts, batch_size=batch_size)
        all_results: list[dict[str, EmbeddingMatch]] = []

        for emb in embeddings:
            results: dict[str, EmbeddingMatch] = {}
            for label, proto_embs in self._prototype_embeddings.items():
                sims = proto_embs @ emb
                top_indices = np.argsort(sims)[::-1][:top_k]
                top_scores = sims[top_indices].tolist()
                best_idx = top_indices[0]

                results[label] = EmbeddingMatch(
                    label=label,
                    score=float(sims[best_idx]),
                    nearest_prototype=self._prototype_texts[label][best_idx],
                    top_k_scores=top_scores,
                )
            all_results.append(results)

        return all_results

    def match_dataframe(
        self,
        df: pd.DataFrame,
        text_col: str = "clean_text",
        batch_size: int = 256,
    ) -> pd.DataFrame:
        """Add embedding similarity columns to a DataFrame.

        Adds columns: emb_{label}_score, emb_{label}_prototype for each label.
        """
        texts = df[text_col].fillna("").tolist()
        results = self.match_batch(texts, batch_size=batch_size)

        # Flatten results into columns
        labels = list(self._prototype_texts.keys())
        for label in labels:
            df[f"emb_{label}_score"] = [r[label].score for r in results]
            df[f"emb_{label}_prototype"] = [
                r[label].nearest_prototype for r in results
            ]

        logger.info(
            "Added embedding features for %d labels across %d comments",
            len(labels),
            len(df),
        )
        return df
