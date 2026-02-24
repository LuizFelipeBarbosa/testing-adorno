# Error Analysis: Common Failure Modes

This document catalogs known and anticipated failure modes of the multi-label culture-industry critique classifier, organized by label. It serves as a living reference for model developers, annotators, and evaluators, supporting systematic improvement through targeted mitigation. All failure modes are grounded in observed or theoretically predicted patterns specific to YouTube music comment data.

---

## Per-Label Failure Modes

---

### STANDARDIZATION

#### Common False Positives

1. **Genre-convention descriptions mistaken for standardization critique.**
   - **Trigger:** Comments like "All blues songs use the 12-bar form" or "Punk is supposed to be three chords" describe genre norms approvingly or neutrally. The model detects language about sameness and misclassifies.
   - **Mitigation:** Train on contrastive examples where genre-convention descriptions are labeled NONE. Add features for sentiment polarity around sameness-language. A neutral or positive stance toward shared conventions should suppress STANDARDIZATION.

2. **Artist-consistency praise misread as homogeneity critique.**
   - **Trigger:** "She always delivers that signature sound" or "You know exactly what you're getting with this producer." The commenter values predictability; the model sees "always" + "same" patterns.
   - **Mitigation:** Incorporate contextual sentiment: praise of consistency (positive valence) vs. critique of sameness (negative valence). Fine-tune on examples where "signature" and "consistent" co-occur with positive markers.

3. **Comparison between two specific songs.**
   - **Trigger:** "This sounds a lot like [other song]" without generalization. The model detects similarity language and triggers STANDARDIZATION.
   - **Mitigation:** Require scope indicators (industry-level, genre-level, or trend-level language) for STANDARDIZATION. Two-song comparisons without systemic framing should remain NONE.

4. **Nostalgic "music was better" comments.**
   - **Trigger:** "Music was better in the 2000s" or "They don't make them like they used to." The model associates temporal comparison with standardization critique.
   - **Mitigation:** Nostalgia without mechanism identification is NONE. Train the model to require co-occurrence of temporal language with specific standardization vocabulary (formula, template, same, identical, interchangeable).

#### Common False Negatives

1. **Implicit standardization via metaphor.**
   - **Miss:** "This is assembly-line music" or "We're living in the Spotify factory era." The model fails to connect manufacturing metaphors to standardization.
   - **Mitigation:** Expand training data with metaphorical standardization critiques. Add lexical features for industrial/manufacturing vocabulary (factory, assembly line, cookie-cutter, template, mass-produced).

2. **Standardization critique embedded in long comments.**
   - **Miss:** A multi-paragraph comment where the standardization critique appears in the third sentence, surrounded by personal anecdotes and taste statements.
   - **Mitigation:** Ensure training examples include long-form comments with critique buried in context. Consider sentence-level attention mechanisms that can locate critique-bearing segments within longer texts.

3. **Code-switched or slang-heavy standardization critique.**
   - **Miss:** "Bruh every joint on the radio be sounding the same frfr no cap" -- the model fails to parse AAVE/internet slang and misses the critique.
   - **Mitigation:** Include diverse linguistic registers in training data. Avoid over-reliance on formal vocabulary as features.

4. **Standardization critique of non-musical elements.**
   - **Miss:** "Every music video now has the same aesthetic -- dark, moody, slow-motion shots in an empty warehouse." The model is tuned for musical standardization and misses visual/aesthetic critiques.
   - **Mitigation:** Expand scope to include comments about music videos, album art, and artist presentation as valid sites of standardization critique.

---

### PSEUDO_INDIVIDUALIZATION

#### Common False Positives

1. **Plagiarism accusations.**
   - **Trigger:** "She totally copied [artist]'s style" is about imitation, not about industry-manufactured uniqueness. The model detects "copied" + artist comparison and triggers PSEUDO_INDIVIDUALIZATION.
   - **Mitigation:** Distinguish between interpersonal copying (one artist imitating another) and systemic pseudo-individualization (the industry creating the illusion of difference). Require language about manufacturing, branding, marketing, or industry mechanisms.

2. **Fan defense of an artist's uniqueness.**
   - **Trigger:** "She is NOT like the other artists, her style is completely her own." The model detects discourse about uniqueness and individuality. But the commenter is affirming, not critiquing, the individuality.
   - **Mitigation:** Sentiment-aware classification: affirmation of genuine uniqueness (positive) vs. critique of manufactured uniqueness (negative or ironic).

3. **Genre-blending praise.**
   - **Trigger:** "She blends jazz, hip-hop, and electronic in a way nobody else does." The model detects individualization language and triggers the label. But the commenter is praising actual differentiation, not critiquing its simulation.
   - **Mitigation:** PSEUDO_INDIVIDUALIZATION requires the commenter to frame the individuality as illusory or manufactured. Genuine praise of actual uniqueness is NONE.

4. **"Industry plant" accusations without elaboration.**
   - **Trigger:** "Total industry plant" -- the model associates this phrase with pseudo-individualization. But without elaboration, the comment may simply be expressing suspicion of an artist's rise, not critiquing the mechanism of manufactured individuality.
   - **Mitigation:** Treat bare "industry plant" as borderline. If no further context specifies how the artist's individuality is manufactured, lean NONE. Include calibration examples with and without elaboration.

#### Common False Negatives

1. **Subtle critique through juxtaposition.**
   - **Miss:** "Her Instagram says 'just a girl with a guitar' but her Spotify bio says 'managed by [major label subsidiary].'" The critique of manufactured authenticity is conveyed through juxtaposition, not explicit language.
   - **Mitigation:** Train on examples where pseudo-individualization is expressed through factual juxtaposition rather than evaluative language.

2. **Critique of "authentic" marketing.**
   - **Miss:** "The 'raw and unfiltered' marketing campaign for this album is ironic considering it took 15 producers and a year of studio time." The word "authentic" does not appear; the model misses the critique of manufactured rawness.
   - **Mitigation:** Expand the feature set beyond explicit authenticity vocabulary. Include markers like "marketing campaign," "branding," "curated" alongside descriptions of artistic identity.

3. **Pseudo-individualization in fan-culture terms.**
   - **Miss:** "Every fandom thinks their fave is different but they're all stanning the same corporate product with different merch." The critique is embedded in fan-culture vocabulary the model may not parse.
   - **Mitigation:** Include fan-culture terminology (stan, fave, fandom, merch, era) in training data for this label.

---

### COMMODIFICATION_MARKET_LOGIC

#### Common False Positives

1. **Neutral reporting of commercial performance.**
   - **Trigger:** "This went platinum in 3 weeks" or "Number one in 15 countries." The model detects market vocabulary and triggers COMMODIFICATION. But the commenter is reporting, not critiquing.
   - **Mitigation:** Require negative or critical framing around market vocabulary. Neutral or celebratory commercial reporting is NONE.

2. **Fan streaming campaigns.**
   - **Trigger:** "Stream this to get it to number one!" The model detects market-oriented language. But the commenter is participating in, not critiquing, market logic.
   - **Mitigation:** Distinguish between endorsement of market activity (NONE) and critique of market activity (COMMODIFICATION). Key markers: "just," "only," "reduced to," "nothing but" + market terms indicate critique.

3. **Artist business praise.**
   - **Trigger:** "She's such a smart businesswoman, she owns her masters and negotiates her own deals." The model detects business/market vocabulary. But the commenter is praising agency within the market, not critiquing the market itself.
   - **Mitigation:** Praise of individual agency within the market is distinct from critique of the market's effect on music. Train on contrastive pairs.

4. **Price complaints.**
   - **Trigger:** "Tickets are way too expensive" or "Can't believe they charge $15 for a vinyl." The commenter is dissatisfied with pricing but is not critiquing the commodification of music as such -- they want the commodity at a lower price.
   - **Mitigation:** Consumer complaints about pricing are NONE unless they connect to a broader argument about music being reduced to a market object.

#### Common False Negatives

1. **Critique of platform economics without using market vocabulary.**
   - **Miss:** "Spotify decides what you hear, and artists get pennies while the platform gets billions. The music is just the bait." The model may fail to connect "bait" to commodification if it is tuned to explicit market terms.
   - **Mitigation:** Train on platform-critique vocabulary: "pennies," "royalties," "paywall," "free tier," "content farm," "bait."

2. **Ironic celebration of market logic.**
   - **Miss:** "Love how we've reduced centuries of musical tradition to 'content' that exists to serve ads between tracks." The model may interpret "love" as positive sentiment and miss the ironic critique.
   - **Mitigation:** Pair sentiment analysis with sarcasm detection. Ironic positive framing of negative phenomena should trigger closer inspection.

3. **Critique of music as "content."**
   - **Miss:** "It's all just 'content' now." The comment is extremely compressed but the scare quotes around "content" signal critique of the commodity form. The model may not pick up on punctuation-level signals.
   - **Mitigation:** Add features for scare quotes, which in this domain frequently signal critique of the term being quoted.

---

### REGRESSIVE_LISTENING

#### Common False Positives

1. **Taste elitism without mechanism.**
   - **Trigger:** "People who listen to this have no taste" or "This generation's music is terrible." The model detects critique of listeners and triggers REGRESSIVE_LISTENING. But the comment is an insult, not a critique of conditioned listening.
   - **Mitigation:** Require identification of a conditioning mechanism (algorithms, industry, platforms, media) or a specific regression pattern (passivity, distraction, skip culture). Pure insults are NONE.

2. **Gatekeeping.**
   - **Trigger:** "You're not a real fan if you only know the singles" or "Normies ruined this genre." The model detects listener-directed critique. But gatekeeping is about subcultural boundaries, not Adornoian regression.
   - **Mitigation:** Train on contrastive pairs: gatekeeping (NONE) vs. regressive-listening critique (REGRESSIVE_LISTENING). Key distinction: gatekeeping polices identity; regressive-listening critique identifies a mechanism of conditioned passivity.

3. **Personal listening preference.**
   - **Trigger:** "I like having music on in the background while I work." The model detects background-listening language and triggers REGRESSIVE_LISTENING. But the commenter is describing their own behavior, not critiquing it.
   - **Mitigation:** Self-description of passive listening is NONE. REGRESSIVE_LISTENING requires a critical stance toward the phenomenon, not participation in it.

4. **Attention-span comments without industry connection.**
   - **Trigger:** "Kids these days can't focus on anything." The model detects attention-related language. But this is a generic cultural complaint, not a critique of how the music industry conditions listening.
   - **Mitigation:** Require connection to music, the industry, or platform design. Generic attention-span complaints are NONE.

#### Common False Negatives

1. **Critique of "vibes" culture.**
   - **Miss:** "Everyone just wants 'vibes' now. Nobody wants to be challenged or confronted by music anymore." The model may not connect "vibes" vocabulary to regressive listening.
   - **Mitigation:** Add "vibes," "mood," "aesthetic," "chill" to the feature vocabulary for REGRESSIVE_LISTENING when combined with critique of superficiality.

2. **Platform-design critique as listening critique.**
   - **Miss:** "Spotify's shuffle is designed to keep you passive. You never have to make a choice." The comment critiques platform design but the target is the listening behavior it produces.
   - **Mitigation:** Train the model to recognize that platform-design critique often implies regressive-listening critique. Cross-label with COMMODIFICATION_MARKET_LOGIC.

3. **Critique through historical comparison.**
   - **Miss:** "In the 60s people sat in a room and listened to an album front to back. Now music is wallpaper." The critique is embedded in a historical comparison the model may interpret as mere nostalgia.
   - **Mitigation:** Distinguish between nostalgia (NONE) and nostalgia that identifies a specific regression in listening behavior (REGRESSIVE_LISTENING). Key marker: description of *how* listening has changed, not just *what* was better.

---

### AFFECTIVE_PREPACKAGING

#### Common False Positives

1. **Emotional effectiveness praise.**
   - **Trigger:** "This song really knows how to hit you in the feels" or "The producers knew exactly how to make this hit emotionally." The model detects language about emotional engineering but the commenter is praising it.
   - **Mitigation:** AFFECTIVE_PREPACKAGING requires a critical stance. If the commenter approves of the emotional effectiveness, this is NONE. Look for words like "manipulative," "calculated," "manufactured," "forced," "cheap" as negative markers.

2. **Music theory analysis.**
   - **Trigger:** "The modulation to the relative major in the chorus creates a sense of uplift." The model detects technical production language and emotional outcome language. But the commenter is performing musical analysis, not critiquing manipulation.
   - **Mitigation:** Neutral or academic analysis of how music produces emotion is not a critique of prepackaging. Require negative framing.

3. **Film/TV soundtrack discussion.**
   - **Trigger:** "The way they used this song in the movie scene made me cry." The model detects emotional engineering language. But the commenter is describing the effect of a creative choice, not critiquing the music industry.
   - **Mitigation:** Distinguish between appreciation of artistic deployment (NONE) and critique of industrial emotional manipulation (AFFECTIVE_PREPACKAGING).

#### Common False Negatives

1. **Implicit critique via deconstruction.**
   - **Miss:** "Quiet verse, loud chorus, key change at the bridge. Works every time, doesn't it?" The final question is mildly ironic, implying the formula is transparent and therefore manipulative. The model may miss the ironic edge.
   - **Mitigation:** Train on examples where rhetorical questions after formulaic descriptions signal critique.

2. **Critique of "reaction content" culture.**
   - **Miss:** "This whole song was engineered to be a 'reaction video' clip. The big note at 3:15 exists solely so YouTubers can pretend to be shocked." The model may focus on the YouTube-specific vocabulary and miss the affective-prepackaging dimension.
   - **Mitigation:** Include reaction-culture vocabulary in training data for AFFECTIVE_PREPACKAGING: "reaction video," "react," "surprise face," "thumbnail moment."

3. **Critique of playlist mood-engineering.**
   - **Miss:** "Spotify literally has playlists called 'Happy Hits' and 'Sad Songs.' They've reduced music to a mood-delivery system." The critique targets prepackaged affect but operates at the platform/curation level rather than the song level.
   - **Mitigation:** Expand AFFECTIVE_PREPACKAGING scope to include platform-level mood curation as a site of affective engineering.

4. **Critique masked by humor.**
   - **Miss:** "Me: I'm not going to cry. This song: *key change* Me: *sobbing* Every. Single. Time." The meme format may obscure the implicit critique that the key change is a predictable manipulation.
   - **Mitigation:** This is genuinely ambiguous. The commenter may be enjoying the experience (NONE) or recognizing the formula with mild critique. Flag meme-format comments about predictable emotional triggers for review.

---

### FORMAL_RESISTANCE

#### Common False Positives

1. **General praise of music quality.**
   - **Trigger:** "This is the best album of the year, no contest." The model may trigger FORMAL_RESISTANCE because the comment is positive about music. But no resistance to industry logic is articulated.
   - **Mitigation:** FORMAL_RESISTANCE requires framing the praise *in opposition to* industry norms. Praise without contrast is NONE.

2. **Hipster elitism.**
   - **Trigger:** "You guys probably haven't heard of this artist" or "This is way too smart for the average listener." The model detects opposition between the praised music and mainstream norms. But the commenter is performing social distinction, not articulating resistance.
   - **Mitigation:** Require identification of *what* the music resists and *how*. Social superiority claims are NONE.

3. **Underground/indie preference.**
   - **Trigger:** "I only listen to underground artists." The model detects alternative-to-mainstream positioning. But preference for obscurity is not the same as articulation of formal resistance.
   - **Mitigation:** FORMAL_RESISTANCE requires the commenter to identify specific formal or structural properties that resist industry logic, not merely to claim alternative taste.

4. **Anti-mainstream sentiment.**
   - **Trigger:** "Mainstream music is dead, this is the real stuff." The model detects opposition to the mainstream. But "real" is too vague to constitute formal resistance.
   - **Mitigation:** Require specificity about what makes the praised music resistant: structural innovation, refusal of commercial form, demand for active engagement.

#### Common False Negatives

1. **Resistance language in technical terms.**
   - **Miss:** "The way this piece uses irregular time signatures and avoids resolution for 8 straight minutes is exactly what music needs right now." The comment describes formal resistance in music-theory terms the model may not connect to the label.
   - **Mitigation:** Include music-theory vocabulary (time signatures, resolution, atonality, polyrhythm, through-composed) in training data for FORMAL_RESISTANCE when combined with advocacy language.

2. **Resistance framed as artist biography.**
   - **Miss:** "She turned down a major label deal to keep creative control. That's why this album sounds like nothing else." The resistance is narrated as an industry decision, not as formal properties.
   - **Mitigation:** Include industry-decision resistance (turning down deals, self-releasing, rejecting commercial pressure) as valid triggers for FORMAL_RESISTANCE.

3. **Implicit resistance via contrast.**
   - **Miss:** "In an ocean of 3-minute playlist fillers, this 20-minute suite is a lifeline." The resistance is implicit in the contrast but may be missed if the model requires explicit opposition language.
   - **Mitigation:** Train on implicit-contrast examples where the praised work is positioned against described industry norms without the word "resist" or "refuse."

---

## Cross-Label Confusion Matrix

The following label pairs are most frequently confused by the model and/or human annotators.

### STANDARDIZATION vs. PSEUDO_INDIVIDUALIZATION

**Confusion pattern:** Both labels concern the sameness-difference dialectic. STANDARDIZATION focuses on the sameness; PSEUDO_INDIVIDUALIZATION focuses on the false appearance of difference. Comments that address both aspects often trigger confusion about which label to assign.

**Resolution:** These labels are not mutually exclusive. When a comment identifies both underlying sameness *and* manufactured difference, assign both. Reserve single-label STANDARDIZATION for comments that focus purely on homogeneity without discussing the illusion of variety. Reserve single-label PSEUDO_INDIVIDUALIZATION for comments that focus on manufactured uniqueness without emphasizing the underlying sameness (e.g., "Her whole 'authentic' persona is a brand" -- the focus is on the fabrication, not on what lies beneath it).

### COMMODIFICATION_MARKET_LOGIC vs. REGRESSIVE_LISTENING

**Confusion pattern:** Commodification produces regressive listening (the market trains passive consumers), and regressive listening sustains commodification (passive consumers accept commodified products). Comments that describe one often imply the other.

**Resolution:** Assign based on the comment's primary target. If the comment critiques the *system* (industry, platforms, market metrics), lean COMMODIFICATION. If the comment critiques *audience behavior* (passivity, uncritical acceptance, herd mentality), lean REGRESSIVE_LISTENING. If both are explicitly present, assign both.

### AFFECTIVE_PREPACKAGING vs. STANDARDIZATION

**Confusion pattern:** Formulaic emotional structures (sad verse, uplifting chorus) are a specific type of standardization. The model may assign STANDARDIZATION to what is more precisely AFFECTIVE_PREPACKAGING, or vice versa.

**Resolution:** If the comment focuses on the *emotional manipulation* dimension (the feelings are manufactured, the tears are engineered), assign AFFECTIVE_PREPACKAGING. If the comment focuses on the *structural repetition* dimension (every song follows the same form), assign STANDARDIZATION. If the comment identifies the emotional formula *as* a standardized template, assign both.

### FORMAL_RESISTANCE vs. COMMODIFICATION_MARKET_LOGIC

**Confusion pattern:** Formal resistance is often articulated *against* commodification. A comment praising an artist for "not chasing streams" simultaneously critiques market logic and celebrates resistance.

**Resolution:** Assign both when both dimensions are present. Single-label FORMAL_RESISTANCE applies when the comment focuses on the positive alternative without extensively critiquing the system it resists. Single-label COMMODIFICATION applies when the comment critiques market logic without championing an alternative.

### PSEUDO_INDIVIDUALIZATION vs. AFFECTIVE_PREPACKAGING

**Confusion pattern:** Manufactured authenticity (pseudo-individualization) can include manufactured emotional sincerity (affective prepackaging). "Her whole 'vulnerable' era is a marketing strategy" touches both the fabricated persona and the engineered emotional appeal.

**Resolution:** PSEUDO_INDIVIDUALIZATION focuses on the *identity* dimension (the artist's uniqueness is manufactured). AFFECTIVE_PREPACKAGING focuses on the *emotional* dimension (the listener's feelings are engineered). When the manufactured identity is specifically an emotional one (vulnerability, rawness, pain), consider assigning both.

---

## Linguistic Challenges

### Sarcasm

Sarcasm inverts the literal meaning of a comment, creating a fundamental challenge for text classification.

**Impact:** A sarcastic comment praising standardization ("Wow, another banger that sounds exactly like the last 50, so innovative") is actually a STANDARDIZATION critique. A model trained on literal meaning will misclassify.

**Mitigation strategies:**
- Incorporate sarcasm-detection as a pre-processing step or auxiliary task.
- Collect and label sarcastic examples for each critique label.
- Use contextual features (e.g., the video being commented on, the parent comment in a thread) to disambiguate.
- Accept higher uncertainty on sarcastic comments; route to human review when sarcasm probability exceeds a threshold.

### Code-Switching

YouTube music comments frequently exhibit code-switching between languages, dialects, and registers (e.g., English/Spanish, Standard American English/AAVE, formal/internet slang).

**Impact:** Critique vocabulary may appear in non-standard forms. "bruh the whole industry be recyclin beats fr" is a standardization critique in AAVE/internet slang that a model trained primarily on standard English may miss.

**Mitigation strategies:**
- Ensure training data includes diverse linguistic registers.
- Use multilingual or register-robust embeddings.
- Avoid tokenizers that fragment non-standard vocabulary.
- Include AAVE, internet slang, and common code-switching patterns in annotation guidelines.

### Slang and Neologisms

Music comment culture generates slang rapidly: "slay," "ate," "devoured," "no skips," "rent free," "understood the assignment."

**Impact:** New slang may co-occur with or be confused with critique language. "This song ate the whole industry" could be praise (slang for "excelled") or could be a metaphor for industry critique.

**Mitigation strategies:**
- Maintain a living glossary of music-comment slang with classification-relevant annotations.
- Periodically retrain on freshly collected data to capture slang evolution.
- Default to NONE for ambiguous slang unless clear critique markers are present.

### Non-English Comments

The YouTube music comment space is globally multilingual. Many comment sections include significant non-English content.

**Impact:** A monolingual English model will miss all critique in non-English comments (false negatives) and may produce unpredictable results on non-English input (false positives).

**Mitigation strategies:**
- For the initial model, scope to English-language comments only. Use language detection to filter.
- For multilingual extension, consider multilingual models (e.g., XLM-R) and language-specific annotation.
- Document language-detection errors as a known source of both FP and FN.

---

## Data Distribution Issues

### Class Imbalance

The vast majority of YouTube music comments are not culture-industry critique. Expected distribution:

| Label | Estimated Prevalence |
|-------|---------------------|
| NONE | 75-85% |
| STANDARDIZATION | 5-10% |
| COMMODIFICATION_MARKET_LOGIC | 3-7% |
| REGRESSIVE_LISTENING | 2-5% |
| PSEUDO_INDIVIDUALIZATION | 2-4% |
| AFFECTIVE_PREPACKAGING | 1-3% |
| FORMAL_RESISTANCE | 2-5% |

**Impact:** Severe class imbalance leads to models that learn to predict NONE for everything, achieving high accuracy but zero recall on critique labels. Minority-class decision boundaries are poorly estimated.

**Mitigation strategies:**
- Use stratified sampling for train/validation/test splits.
- Apply class-weighted loss functions (inverse frequency weighting or focal loss).
- Oversample minority classes or use data augmentation (paraphrase, back-translation).
- Evaluate on per-label F1, precision, and recall rather than aggregate accuracy.
- Consider macro-averaged F1 as the primary optimization metric.

### Long-Tail Label Combinations

With 6 binary labels (excluding NONE), there are 63 possible non-NONE label combinations. Most combinations will have very few examples.

**Impact:** The model may perform well on common single-label cases but poorly on multi-label combinations, especially rare ones like PSEUDO_INDIVIDUALIZATION + AFFECTIVE_PREPACKAGING.

**Mitigation strategies:**
- Treat multi-label classification as independent binary classification per label (binary relevance approach) rather than as multi-class over label combinations.
- Monitor performance on multi-label examples separately from single-label examples.
- Collect targeted examples for underrepresented label combinations.

### Source Bias

Comment distributions vary dramatically by:
- **Genre:** Hip-hop comment sections may contain more COMMODIFICATION critique; experimental-music comments may contain more FORMAL_RESISTANCE.
- **Artist:** Comments on major-label pop artists skew toward STANDARDIZATION and PSEUDO_INDIVIDUALIZATION critique; comments on independent artists skew toward FORMAL_RESISTANCE.
- **Video type:** Official music videos vs. lyric videos vs. reaction videos vs. essay videos generate different comment distributions.
- **Temporal context:** Comments spike during album releases, controversies, or trending moments, affecting distribution.

**Impact:** A model trained on comments from one genre or context may generalize poorly to others.

**Mitigation strategies:**
- Stratify training data collection across genres, artist types, and video types.
- Track performance per data source/genre.
- Consider domain-adaptive fine-tuning for specific genre contexts.

---

## Proposed Iteration Plan for Systematic Improvement

### Phase 1: Baseline Establishment (Weeks 1-4)

1. **Collect and annotate** a seed dataset of 2,000 comments from diverse sources (multiple genres, artist types, video types).
2. **Establish inter-annotator agreement** using the annotation guidelines. Target: kappa >= 0.70 per label.
3. **Train baseline model** using a pre-trained language model (e.g., RoBERTa-base) with binary classification heads per label.
4. **Evaluate** on a held-out test set of 500 comments. Report per-label precision, recall, F1, and macro-averaged F1.
5. **Conduct manual error analysis** on all false positives and false negatives. Categorize errors using the failure modes documented above.

### Phase 2: Targeted Data Collection (Weeks 5-8)

1. **Identify** the top 3 failure modes per label from Phase 1 error analysis.
2. **Collect targeted examples** for each failure mode: 50-100 additional comments per failure mode, annotated with ground truth.
3. **Augment** underrepresented labels and label combinations using paraphrase and back-translation.
4. **Retrain** with the expanded dataset.
5. **Re-evaluate** and compare to Phase 1 baseline. Track improvement on previously identified failure modes.

### Phase 3: Linguistic Robustness (Weeks 9-12)

1. **Audit** model performance across linguistic registers: standard English, AAVE, internet slang, code-switched comments.
2. **Collect** 200+ comments per register category for evaluation.
3. **Implement** sarcasm detection as an auxiliary task or pre-processing step.
4. **Add** register-diverse training examples for underperforming categories.
5. **Retrain** and re-evaluate with focus on cross-register consistency.

### Phase 4: Cross-Label Calibration (Weeks 13-16)

1. **Analyze** cross-label confusion using the confusion patterns documented above.
2. **Collect** targeted multi-label examples for commonly confused label pairs.
3. **Experiment** with label-interaction architectures (e.g., classifier chains, label-attention mechanisms) vs. independent binary classifiers.
4. **Calibrate** confidence thresholds per label to optimize the precision-recall tradeoff for each label independently.
5. **Re-evaluate** with attention to multi-label performance.

### Phase 5: Deployment and Monitoring (Weeks 17-20)

1. **Deploy** the model on a sample of live YouTube comments (read-only, no user-facing predictions).
2. **Monitor** prediction distributions for drift from training-data distributions.
3. **Sample** predictions for human review: 50 random predictions per week + all predictions with confidence between 0.4 and 0.6 (uncertainty band).
4. **Log** new failure modes discovered in production data.
5. **Update** this error analysis document and the annotation guidelines based on production findings.

### Ongoing: Continuous Improvement Loop

- **Monthly:** Retrain on accumulated production-validated examples.
- **Quarterly:** Re-run full error analysis. Update failure mode catalog. Revise annotation guidelines if needed.
- **Biannually:** Reassess label taxonomy for completeness. Evaluate whether new critique categories have emerged in the comment data that the current taxonomy does not capture.
- **Annually:** Full model audit including fairness analysis (does the model perform differently on comments from different demographic or linguistic groups?) and concept drift analysis (have the patterns of culture-industry critique evolved?).
