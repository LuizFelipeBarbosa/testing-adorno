# Annotation Guidelines

## Purpose and Audience

This document provides operational guidelines for human annotators tasked with labeling YouTube music comments for culture-industry critique detection. The annotation task supports the training, evaluation, and error analysis of a multi-label text classifier whose label space is defined in the companion document `taxonomy.md`.

**Audience:** Annotators should have a working familiarity with Adorno's culture-industry thesis (a briefing document is provided during onboarding). Deep expertise in critical theory is not required, but annotators must understand the distinction between *taste-based evaluation* ("this is bad") and *structural critique* ("this is bad because of how the industry works"). Prior experience with content annotation for NLP tasks is preferred. Familiarity with YouTube comment culture, music industry terminology, and internet slang is essential.

**Goal:** For each comment, determine which -- if any -- of the six critique labels apply. Prioritize precision (avoid false positives) over recall (tolerate false negatives). A comment must demonstrate identifiable engagement with a culture-industry mechanism to receive a critique label; vague negativity, personal taste, and unelaborated dismissals default to NONE.

---

## Label-by-Label Decision Flowchart

Use the following text-based decision procedure for each comment. Evaluate each label independently; a comment may trigger multiple branches.

```
START
  |
  v
READ the comment in full. Identify the commenter's voice vs. quoted material.
  |
  v
Is the comment spam, self-promotion, emoji-only, or unintelligible?
  YES --> NONE (stop evaluating this comment)
  NO  --> continue
  |
  v
Is the comment a bare evaluative expression with no identifiable mechanism?
  (e.g., "this slaps," "trash," "mid," "banger," "overrated")
  YES --> NONE (stop evaluating this comment)
  NO  --> continue
  |
  v
Does the comment consist solely of quoted lyrics with no commentary?
  YES --> NONE (stop evaluating this comment)
  NO  --> continue
  |
  v
For each of the six labels below, evaluate independently:

--- STANDARDIZATION ---
Does the comment identify homogenization, formulaic production, or convergence
across songs, artists, or the industry?
  YES --> Does it specify a mechanism or pattern (not just "this is unoriginal")?
           YES --> STANDARDIZATION = TRUE
           NO  --> STANDARDIZATION = FALSE
  NO  --> STANDARDIZATION = FALSE

--- PSEUDO_INDIVIDUALIZATION ---
Does the comment identify manufactured uniqueness, artificial branding, or
surface-level differentiation masking underlying sameness?
  YES --> Does it connect the "uniqueness" to industry/marketing mechanisms?
           YES --> PSEUDO_INDIVIDUALIZATION = TRUE
           NO  --> PSEUDO_INDIVIDUALIZATION = FALSE
  NO  --> PSEUDO_INDIVIDUALIZATION = FALSE

--- COMMODIFICATION_MARKET_LOGIC ---
Does the comment critique the reduction of music to market terms (streams,
sales, charts, brand deals) or the subordination of art to commercial logic?
  YES --> Is the critique directed at the system/logic, not just one transaction?
           YES --> COMMODIFICATION_MARKET_LOGIC = TRUE
           NO  --> Consider context; if the specific transaction exemplifies
                   systemic logic, COMMODIFICATION_MARKET_LOGIC = TRUE
  NO  --> COMMODIFICATION_MARKET_LOGIC = FALSE

--- REGRESSIVE_LISTENING ---
Does the comment critique passive, uncritical, or conditioned listening behavior
in audiences?
  YES --> Does it identify a mechanism of conditioning (algorithms, industry
          training, platform design) or a pattern of regression (short attention
          spans, skip culture, herd behavior)?
           YES --> REGRESSIVE_LISTENING = TRUE
           NO  --> Is it snobbery/insult without mechanism?
                    YES --> REGRESSIVE_LISTENING = FALSE
                    NO  --> REGRESSIVE_LISTENING = TRUE (if pattern is clear)
  NO  --> REGRESSIVE_LISTENING = FALSE

--- AFFECTIVE_PREPACKAGING ---
Does the comment critique the engineering or manufacturing of emotional
responses through calculated production techniques?
  YES --> Does it identify specific techniques or the general principle of
          emotional manipulation as an industry practice?
           YES --> AFFECTIVE_PREPACKAGING = TRUE
           NO  --> AFFECTIVE_PREPACKAGING = FALSE
  NO  --> AFFECTIVE_PREPACKAGING = FALSE

--- FORMAL_RESISTANCE ---
Does the comment praise or advocate for music that resists culture-industry
logic through formal innovation, structural challenge, or refusal of
commercial concession?
  YES --> Is the praise framed in opposition to industry norms (not just
          "this is good" but "this is good BECAUSE it resists X")?
           YES --> FORMAL_RESISTANCE = TRUE
           NO  --> FORMAL_RESISTANCE = FALSE
  NO  --> FORMAL_RESISTANCE = FALSE

--- NONE ---
Are ALL six labels above FALSE?
  YES --> NONE = TRUE
  NO  --> NONE = FALSE

END
```

---

## Positive Examples (Comments That Receive Critique Labels)

The following 25 examples illustrate comments that should receive one or more critique labels. Each includes the comment text, assigned label(s), and a brief rationale.

### Example 1
**Comment:** "Every song on the Billboard Hot 100 sounds like it was made by the same AI. Same tempo, same structure, same vibe. There's literally no variety."
**Label(s):** STANDARDIZATION
**Rationale:** Identifies homogenization across the industry (Billboard Hot 100) with specific sonic dimensions (tempo, structure, vibe).

### Example 2
**Comment:** "They market her as this rebellious indie artist but she's signed to Universal and her songs are written by the same team that writes for every other pop star."
**Label(s):** PSEUDO_INDIVIDUALIZATION
**Rationale:** Explicitly identifies the gap between marketed identity ("rebellious indie") and underlying industry reality (major label, shared songwriting team).

### Example 3
**Comment:** "Music isn't art anymore, it's content. Everything is optimized for playlist placement and streaming revenue. The soul got extracted sometime around 2015."
**Label(s):** COMMODIFICATION_MARKET_LOGIC
**Rationale:** Critiques the reduction of music to "content" driven by platform economics (playlist placement, streaming revenue).

### Example 4
**Comment:** "People don't listen to music anymore, they let Spotify's algorithm listen for them. When did we stop choosing what we hear?"
**Label(s):** REGRESSIVE_LISTENING
**Rationale:** Identifies algorithm-mediated passive consumption as a replacement for autonomous listening.

### Example 5
**Comment:** "The way they drop the beat at the chorus and add those swelling strings -- it's so calculated. They're engineering your emotional response like a focus group tested it."
**Label(s):** AFFECTIVE_PREPACKAGING
**Rationale:** Identifies specific production techniques (beat drop, swelling strings) as calculated emotional engineering, with explicit reference to market-testing logic.

### Example 6
**Comment:** "This is the antidote to everything wrong with modern pop. No hooks, no pandering, just pure uncompromising musicianship that asks you to actually pay attention."
**Label(s):** FORMAL_RESISTANCE
**Rationale:** Praises music specifically for its refusal of commercial pop conventions (hooks, pandering) and its demand for active listening.

### Example 7
**Comment:** "The fact that this 12-minute jazz-fusion track exists on YouTube next to all the 2-minute TikTok bait gives me hope. Not everything has to be optimized for the algorithm."
**Label(s):** FORMAL_RESISTANCE, COMMODIFICATION_MARKET_LOGIC
**Rationale:** Praises formal resistance (duration, genre) while critiquing algorithmic optimization as a market-driven constraint.

### Example 8
**Comment:** "Billie, Olivia, Halsey -- different aesthetics, same formula. The industry found a template for 'sad girl pop' and keeps cloning it with different hairstyles."
**Label(s):** STANDARDIZATION, PSEUDO_INDIVIDUALIZATION
**Rationale:** Identifies both the underlying formula (STANDARDIZATION) and the cosmetic differentiation via aesthetics and hairstyles (PSEUDO_INDIVIDUALIZATION).

### Example 9
**Comment:** "Y'all only think this is good because it has 500 million streams. If this exact song had 5,000 plays you'd call it mid."
**Label(s):** REGRESSIVE_LISTENING, COMMODIFICATION_MARKET_LOGIC
**Rationale:** Critiques listeners for substituting stream counts (market metric) for genuine aesthetic judgment (regressive listening enabled by commodification logic).

### Example 10
**Comment:** "The bridge is literally engineered to make you cry. Key change, vocal crack, silence, then the big swell. It's a formula and you're all falling for it."
**Label(s):** AFFECTIVE_PREPACKAGING, REGRESSIVE_LISTENING
**Rationale:** Identifies the emotional formula (AFFECTIVE_PREPACKAGING) and critiques listeners for uncritically responding to it (REGRESSIVE_LISTENING).

### Example 11
**Comment:** "Radio stations, streaming playlists, label A&R -- they all want the same thing: a song that sounds enough like the last hit to feel safe but different enough to seem fresh. That's the whole game."
**Label(s):** STANDARDIZATION, PSEUDO_INDIVIDUALIZATION, COMMODIFICATION_MARKET_LOGIC
**Rationale:** Describes the industry mechanism of safe-but-novel production (standardization with pseudo-individualization) driven by commercial risk aversion (commodification).

### Example 12
**Comment:** "I'm so tired of every rapper having a 'unique flow' that was clearly learned from the same SoundCloud tutorial. The individuality is an illusion."
**Label(s):** PSEUDO_INDIVIDUALIZATION
**Rationale:** Directly names the illusion of individuality and identifies a shared source of ostensibly unique styles.

### Example 13
**Comment:** "This album would never get made today. Labels only want 12 tracks of playlist-friendly singles. No interludes, no experimentation, no risk."
**Label(s):** STANDARDIZATION, COMMODIFICATION_MARKET_LOGIC, FORMAL_RESISTANCE
**Rationale:** Critiques industry-imposed format constraints (STANDARDIZATION) driven by playlist economics (COMMODIFICATION), while implicitly praising the discussed album as resistant (FORMAL_RESISTANCE).

### Example 14
**Comment:** "We've reached the point where 'good production' just means 'sounds like everything else that's popular.' Congratulations, we've standardized taste."
**Label(s):** STANDARDIZATION, REGRESSIVE_LISTENING
**Rationale:** Identifies the conflation of production quality with conformity (STANDARDIZATION) and the internalization of standardized norms as taste (REGRESSIVE_LISTENING).

### Example 15
**Comment:** "The vinyl resurgence is hilarious. People don't actually listen to records -- they buy them as aesthetic objects to photograph for Instagram. Music as home decor."
**Label(s):** COMMODIFICATION_MARKET_LOGIC
**Rationale:** Critiques the transformation of the music-listening object from a medium of aesthetic experience to a commodity of lifestyle branding.

### Example 16
**Comment:** "Notice how every 'emotional' performance on these competition shows uses the exact same formula: sad backstory package, minor key, vocal break, standing ovation. Your feelings are being manufactured."
**Label(s):** AFFECTIVE_PREPACKAGING
**Rationale:** Identifies a systematic formula for engineering emotional audience response across an entire format (competition shows).

### Example 17
**Comment:** "The fact that artists now have to think about 'the skip rate' when they're making music tells you everything about what the industry has become."
**Label(s):** COMMODIFICATION_MARKET_LOGIC
**Rationale:** Identifies a specific market metric (skip rate) that has been internalized into the creative process, subordinating art to platform analytics.

### Example 18
**Comment:** "You can literally swap the verses between any of the top 10 songs right now and nobody would notice. That's not a genre -- that's a factory."
**Label(s):** STANDARDIZATION
**Rationale:** Vivid illustration of interchangeability (a hallmark of Adorno's standardization thesis) with the factory metaphor making the industrial critique explicit.

### Example 19
**Comment:** "At least Radiohead had the guts to follow OK Computer with Kid A. Imagine a band today releasing something that alienating. Their label would drop them."
**Label(s):** FORMAL_RESISTANCE, COMMODIFICATION_MARKET_LOGIC
**Rationale:** Praises a historical act of formal resistance while critiquing the current industry climate that would prevent it (market logic).

### Example 20
**Comment:** "The 'lo-fi beats to study to' phenomenon is the final boss of background music. It's literally designed to not be listened to. Adorno would lose his mind."
**Label(s):** REGRESSIVE_LISTENING, COMMODIFICATION_MARKET_LOGIC
**Rationale:** Identifies music designed for distracted, passive consumption (REGRESSIVE_LISTENING) reduced to a functional commodity ("to study to") rather than an aesthetic object (COMMODIFICATION).

### Example 21
**Comment:** "Her whole persona is corporate astroturfing. The 'authentic' selfies, the 'spontaneous' studio clips -- it's all scripted by a branding team to make you think she's real."
**Label(s):** PSEUDO_INDIVIDUALIZATION
**Rationale:** Identifies the systematic manufacture of an "authentic" persona as a marketing strategy.

### Example 22
**Comment:** "Artists used to make albums that were cohesive artistic statements. Now they make 20-track content dumps designed to maximize streaming royalties. It's not music, it's a business strategy."
**Label(s):** COMMODIFICATION_MARKET_LOGIC, STANDARDIZATION
**Rationale:** Critiques the subordination of album form to revenue maximization (COMMODIFICATION) and the resulting convergence on a bloated format (STANDARDIZATION).

### Example 23
**Comment:** "The way this song refuses to give you a chorus is almost confrontational. In a world of instant hooks, silence and tension are radical."
**Label(s):** FORMAL_RESISTANCE
**Rationale:** Praises a structural refusal (no chorus) as a conscious act of resistance against industry norms (instant hooks).

### Example 24
**Comment:** "Imagine thinking chart position means anything about quality. The charts measure marketing budgets, not artistry."
**Label(s):** COMMODIFICATION_MARKET_LOGIC
**Rationale:** Directly critiques the substitution of market metrics (chart position, marketing budgets) for aesthetic value.

### Example 25
**Comment:** "The industry created 'chill pop' as a genre specifically because it's inoffensive enough to be playlisted everywhere. It's music designed to not bother anyone, which means it's music designed to not mean anything."
**Label(s):** STANDARDIZATION, COMMODIFICATION_MARKET_LOGIC, AFFECTIVE_PREPACKAGING
**Rationale:** Identifies genre creation driven by playlist economics (COMMODIFICATION), the resulting sonic homogeneity (STANDARDIZATION), and the engineering of a specific affective mode -- inoffensiveness -- as a deliberate product feature (AFFECTIVE_PREPACKAGING).

---

## Negative Examples (Comments That Receive NONE)

The following 25 examples illustrate comments that should **not** receive any critique label. Each includes the comment text and a rationale for why no label applies.

### Example 1
**Comment:** "This song is fire."
**Rationale:** Pure evaluative expression with no identifiable critique mechanism.

### Example 2
**Comment:** "Who's listening in 2026?"
**Rationale:** Phatic community-building comment with no critical content.

### Example 3
**Comment:** "I've had this on repeat all week."
**Rationale:** Expression of personal consumption behavior, not a critique of listening modes.

### Example 4
**Comment:** "The guitar tone is incredible. What amp is he using?"
**Rationale:** Technical appreciation and factual inquiry. No culture-industry critique.

### Example 5
**Comment:** "This is trash, worst song she's ever made."
**Rationale:** Negative taste judgment without identification of any structural, industrial, or systemic mechanism.

### Example 6
**Comment:** "First!"
**Rationale:** Phatic comment with no substantive content.

### Example 7
**Comment:** "I cried the first time I heard this. Takes me back to summer 2019."
**Rationale:** Sincere emotional response and personal association. No critique of the mechanism producing the emotion.

### Example 8
**Comment:** "'And I will always love you' -- chills every time."
**Rationale:** Quoted lyric with affective response. No commentary on industrial mechanisms.

### Example 9
**Comment:** "She needs to collab with Drake ASAP."
**Rationale:** Fan desire for a collaboration. No critique content.

### Example 10
**Comment:** "Underrated tbh."
**Rationale:** Evaluative claim about recognition without identifying why something is underrated or connecting to industry mechanisms.

### Example 11
**Comment:** "This album is a masterpiece from start to finish."
**Rationale:** Positive aesthetic judgment without framing it as resistance to industry norms.

### Example 12
**Comment:** "The bass drop at 2:47 goes crazy."
**Rationale:** Appreciation of a specific musical moment. No critique of production as manipulation.

### Example 13
**Comment:** "I miss the old Kanye."
**Rationale:** Nostalgia for a prior artistic phase. Without elaboration on what changed and why (industry pressure, commodification, etc.), this is a taste statement.

### Example 14
**Comment:** "Stream 'Midnight Rain' for clear skin."
**Rationale:** Humorous fan promotion. No critique content.

### Example 15
**Comment:** "This is overrated. I don't get the hype."
**Rationale:** Contrarian taste judgment without identifying what produces the "hype" or connecting it to industry mechanisms.

### Example 16
**Comment:** "Anyone know the sample in the intro?"
**Rationale:** Factual inquiry about production. No critique.

### Example 17
**Comment:** "Not her best work but still solid. 7/10."
**Rationale:** Evaluative scoring with no critique of industrial mechanisms.

### Example 18
**Comment:** "The music video is stunning. The cinematography is next level."
**Rationale:** Aesthetic appreciation of visual production. No critique of the production as manipulation or commodification.

### Example 19
**Comment:** "I only listen to this genre ironically lol."
**Rationale:** Self-deprecating humor about taste. No critique of industry mechanisms despite the word "ironically."

### Example 20
**Comment:** "This song is so catchy it's been stuck in my head for days."
**Rationale:** Report of earworm experience. While Adorno would analyze catchiness as a tool of standardization, the commenter is not making that critique -- they are simply reporting an experience.

### Example 21
**Comment:** "R.I.P. to a legend. Gone too soon."
**Rationale:** Tribute comment with no critical content.

### Example 22
**Comment:** "The transition from track 3 to track 4 is seamless. Beautiful sequencing."
**Rationale:** Appreciation of album craft. No industry critique.

### Example 23
**Comment:** "I don't usually like pop but this is actually good."
**Rationale:** Personal taste exception. No critique of pop as a system.

### Example 24
**Comment:** "Can someone make a 1-hour loop of this?"
**Rationale:** Consumption request. While a loop request could theoretically relate to distracted listening, the comment itself contains no critique.

### Example 25
**Comment:** "Saw them live last month. Even better in person."
**Rationale:** Concert experience report with no critical content.

---

## Ambiguous Cases and Tiebreakers

### General Principles

1. **When in doubt, choose NONE.** The classifier's precision is more important than recall in this application. A false positive (labeling a non-critical comment as critique) is more damaging to model training than a false negative (missing a genuine critique).

2. **The mechanism test.** The single most important question for every label is: *Does the comment identify a mechanism?* Standardization requires identification of *what* is standardized. Commodification requires identification of *what* is being commodified or *which* market logic is at work. A comment that expresses dissatisfaction without identifying a mechanism defaults to NONE.

3. **Scope test.** Many labels require a systemic or structural scope. A complaint about a single song's quality is not STANDARDIZATION. A complaint about one artist's shift in direction is not necessarily COMMODIFICATION. Look for language that generalizes beyond the individual case: "the industry," "everyone," "always," "all music now."

4. **Intent vs. effect.** Annotate based on what the comment *says*, not what Adorno *would say* about the topic. If a comment reports being moved to tears, it is NONE -- even though Adorno might analyze the tears as a product of affective prepackaging. The commenter must be the one making the critique.

### Specific Tiebreaker Rules

| Ambiguity | Resolution |
|-----------|------------|
| Comment critiques an artist without generalizing to the industry | NONE unless the artist is explicitly framed as exemplifying an industry pattern |
| Comment says "this is generic" without elaboration | NONE -- "generic" is evaluative, not mechanistic |
| Comment says "sell out" without context | NONE -- too ambiguous |
| Comment praises an artist's uniqueness without irony | NONE -- not a critique of pseudo-individualization |
| Comment says "the industry is dead" without specifics | NONE -- too vague |
| Comment expresses nostalgia ("music was better in the 90s") without mechanism | NONE |
| Comment critiques algorithms but only says "the algorithm sucks" | NONE -- no mechanism specified |
| Comment critiques algorithms and says "the algorithm rewards sameness" | STANDARDIZATION and/or COMMODIFICATION_MARKET_LOGIC |
| Two annotators disagree on a label | Route to a third annotator; majority rules; if 3-way split, default to NONE |

---

## Special Case Handling

### Sarcasm and Irony

Sarcasm is pervasive in YouTube comments and poses a significant annotation challenge.

**Detection cues:**
- Explicit markers: "/s," "lol," "lmao," "obviously"
- Exaggerated praise for something clearly being criticized
- Contradiction between literal content and context (e.g., praising a widely mocked song)
- Absurd exaggeration ("Wow, using the same four chords? Revolutionary.")

**Annotation procedure:**
1. If sarcasm is detected with high confidence and the sarcastic reading constitutes a critique, assign the relevant label(s) with a `sarcasm=true` flag.
2. If sarcasm is suspected but uncertain, assign NONE and flag for adjudication (`ambiguous_sarcasm=true`).
3. Never assign a critique label based on a sarcastic reading unless you are confident the sarcasm inverts the literal meaning into a critique.

**Example:** *"Wow another pop song with a four-chord progression and a drop chorus, truly groundbreaking."* -- Assign STANDARDIZATION with `sarcasm=true`.

### Irony Without Sarcasm

Some comments use irony structurally (e.g., juxtaposition, understatement) without the mocking tone of sarcasm.

**Example:** *"In a world of infinite musical possibilities, it's remarkable how every song on the radio manages to sound the same."* -- The irony is structural (juxtaposing "infinite possibilities" with "sound the same"). This qualifies as STANDARDIZATION without a sarcasm flag.

### Multilingual Comments

- If the comment is entirely in a language the annotator does not speak, mark as `needs_translation=true` and skip.
- If the comment is code-switched (e.g., English/Spanish), annotate based on the portions you can understand. If the understood portion qualifies for a label, assign it. If the untranslated portion might change the interpretation, flag for review.
- Machine-translated comments should be annotated with reduced confidence and flagged.

### Emoji-Only Comments

- Comments consisting entirely of emojis receive NONE.
- Emojis used alongside text should be interpreted as modifiers of the text (e.g., a clown emoji after a statement may indicate sarcasm).
- Do not infer critique from emojis alone. A skull emoji does not indicate a critique of anything; it typically indicates amusement or emphasis.

### Spam and Self-Promotion

- Comments that are clearly spam (phishing links, irrelevant promotion, bot-generated text) receive NONE.
- Comments that are self-promotion ("Check out my new single!") receive NONE.
- If a spam or self-promotional comment incidentally contains critique language, still assign NONE -- the primary communicative intent is not critique.

### Quoted Lyrics

- **Lyrics only, no commentary:** NONE. The commenter is quoting, not critiquing.
- **Lyrics with commentary:** Annotate the commentary. Ignore the lyrics as an object of annotation (they are context, not the commenter's voice).
- **Lyrics used as evidence for a critique:** Annotate normally. Example: *"'I'm different, yeah I'm different' -- is he though? This sounds exactly like every other trap song."* Assign STANDARDIZATION and/or PSEUDO_INDIVIDUALIZATION based on the commenter's argument.

---

## Quality Control Procedures

### Annotator Training

1. **Onboarding session (2 hours):** Overview of Adorno's culture-industry thesis, walkthrough of the taxonomy document, and guided annotation of 20 practice comments.
2. **Calibration round:** Each new annotator independently labels 50 pre-annotated comments. Annotators must achieve >= 80% agreement with the gold-standard labels before proceeding to production annotation.
3. **Ongoing calibration:** Every 500 comments, annotators complete a 25-comment calibration set. Annotators falling below 75% agreement are retrained.

### Inter-Annotator Agreement

- Every comment is annotated by at least **two** independent annotators.
- Agreement is measured per-label using **Cohen's kappa**.
- Target: kappa >= 0.70 for each label.
- Comments with annotator disagreement are routed to a **third adjudicator** (a senior annotator or domain expert).
- If kappa drops below 0.60 for any label across a batch, the annotation team convenes to discuss and re-calibrate on that label.

### Adjudication Protocol

1. Disagreements are presented to the adjudicator without revealing which annotator chose which label.
2. The adjudicator assigns the final label(s) with a brief written rationale.
3. Adjudication decisions are logged and periodically reviewed to update these guidelines with new edge cases.

### Data Quality Checks

- **Annotation speed monitoring:** Flag annotations completed in under 3 seconds per comment (likely insufficient engagement).
- **Label distribution monitoring:** If any annotator's label distribution deviates by more than 2 standard deviations from the group mean, review their annotations for systematic bias.
- **NONE overuse check:** If an annotator assigns NONE to more than 95% of comments, review for under-engagement. (The expected NONE rate is approximately 70-85% depending on the comment source.)
- **Critique overuse check:** If an annotator assigns critique labels to more than 40% of comments, review for over-interpretation.

### Feedback Loop

- Annotators may flag comments as "unclear" or "needs discussion" at any time.
- Flagged comments are reviewed weekly by the annotation lead.
- Guideline updates resulting from flagged cases are documented with a version number and changelog.
- All annotators are notified of guideline updates and provided with examples illustrating the change.

### Version Control

This document is versioned. The current version is **v1.0**. All changes are tracked in the changelog below.

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-02-17 | Initial release |
