# Critique Label Taxonomy

## Introduction

This taxonomy defines the label space for a multi-label classifier that detects critique of the culture industry within YouTube music comments. The theoretical foundation is Theodor W. Adorno's analysis of mass-produced cultural commodities, principally as articulated in *Dialectic of Enlightenment* (with Max Horkheimer, 1944) and the essay "On Popular Music" (1941). Adorno argued that the culture industry operates through mechanisms of standardization, pseudo-individualization, and the conversion of aesthetic experience into fungible market units, producing listeners whose capacity for critical engagement has been systematically eroded. This taxonomy operationalizes those mechanisms as discrete, detectable critique labels that can be assigned to naturally occurring YouTube comments.

Each comment is evaluated against all six critique labels independently. A comment may carry zero, one, or several labels simultaneously. The label NONE is assigned if and only if no critique label applies.

---

## Labels

---

### 1. STANDARDIZATION

**Definition:** The comment identifies, criticizes, or laments the homogenization of musical output -- the observation that songs, artists, production techniques, or industry practices converge on a narrow set of interchangeable templates. The commenter perceives that ostensibly different products are structurally or aesthetically identical.

**Adorno Concept:** Maps to Adorno's concept of *standardization* in "On Popular Music," where he argues that popular music follows rigid, pre-given structural schemas (verse-chorus form, 32-bar AABA, predictable harmonic progressions) such that "the whole is pre-given and pre-accepted, before the actual experience of the music starts." Also relates to the broader culture-industry thesis in *Dialectic of Enlightenment*, Chapter 4: "The Culture Industry: Enlightenment as Mass Deception," where Horkheimer and Adorno write that "the same thing is offered to everybody by the standardized production of consumption goods."

**Inclusion Criteria:**
- The comment explicitly claims that songs, artists, albums, or genres sound the same, follow the same formula, or are interchangeable.
- The comment criticizes the music industry for enforcing uniformity, e.g., labels pushing a "sound," algorithms rewarding sameness, or producers recycling templates.
- The comment notes convergence in production techniques (e.g., "every pop song uses the same four chords and Auto-Tune").
- The comment frames the observation critically or with frustration -- mere neutral description of genre conventions can qualify if the tone conveys that sameness is a deficiency.

**Exclusion Criteria:**
- The comment praises consistency or reliability of an artist's sound without framing it as a deficiency ("She always delivers the same quality" is not a critique of standardization).
- The comment notes similarity between two specific songs without generalizing to an industry-wide or genre-wide pattern (this may be simple comparison, not a critique of systemic homogenization).
- The comment describes genre conventions approvingly ("I love how all synthwave has that retro feel").

**Edge Cases:**
1. *"This sounds like every other Drake song."* -- If the comment stops here, it may be a simple observation or mild complaint about a single artist's lack of variety. This qualifies as STANDARDIZATION only if the comment implies the repetition is symptomatic of broader industry forces or formulaic production. If it reads as personal disappointment with one artist, label NONE. **Resolution:** Look for industry-level language ("the industry," "every song on the radio," "they all"). If absent and the scope is a single artist, default to NONE unless the comment explicitly frames the artist as a product of the system.
2. *"Pop music peaked in the 90s, everything now is garbage."* -- Nostalgia-driven dismissal without identifying a mechanism of homogenization. **Resolution:** This is NONE. A vague quality judgment is not a critique of standardization unless the commenter specifies *what* is standardized.
3. *"They literally copy-pasted the beat from [other song] and called it new."* -- Direct accusation of formulaic recycling between specific tracks. **Resolution:** This qualifies as STANDARDIZATION because the commenter is identifying a concrete mechanism of homogenization (beat recycling), even if the scope is two songs, because the framing ("called it new") implies systemic deception.

**Example Qualifying Comments:**
1. "Every top 40 hit this year has the same trap hi-hats, the same 808 pattern, and the same melodic flow. It's like they're all made in the same factory."
2. "The algorithm is literally training artists to make the same song over and over. Spotify rewards sameness."
3. "I swear major labels have a template they hand out. Verse, hook, verse, hook, bridge that goes nowhere, hook again. Rinse and repeat for every release."

---

### 2. PSEUDO_INDIVIDUALIZATION

**Definition:** The comment identifies or critiques the illusion of uniqueness, originality, or personal expression within a fundamentally standardized product. The commenter perceives that surface-level differences (branding, aesthetic styling, minor musical flourishes) disguise the underlying sameness of the cultural commodity.

**Adorno Concept:** Directly maps to Adorno's concept of *pseudo-individualization* in "On Popular Music," defined as "endowing cultural mass production with the halo of free choice or open market on the basis of standardization itself." Adorno argues that the industry permits -- indeed engineers -- superficial variation precisely to mask the standardized core, giving listeners the false impression of meaningful diversity and personal taste.

**Inclusion Criteria:**
- The comment argues that an artist's "unique" image or style is manufactured, curated, or imposed by management, labels, or marketing teams.
- The comment claims that apparent musical or aesthetic differences between artists are cosmetic, concealing identical underlying structures.
- The comment critiques branding, aesthetic packaging, or identity construction as a marketing strategy rather than genuine artistic expression.
- The comment notes that "indie" or "alternative" positioning is itself a market category, a commodified form of rebellion.

**Exclusion Criteria:**
- The comment accuses an artist of plagiarism or copying without connecting it to a systemic mechanism of manufactured difference (this may be STANDARDIZATION or simple criticism).
- The comment praises an artist's unique style without irony or critique.
- The comment dismisses an artist as "unoriginal" purely as a taste judgment without identifying the mechanism by which originality is simulated.

**Edge Cases:**
1. *"She's supposed to be the 'alternative' one but her music sounds exactly like mainstream pop with a filter on it."* -- This directly identifies the mechanism: a surface marker ("alternative" branding, a sonic "filter") masking underlying conformity. **Resolution:** Qualifies as PSEUDO_INDIVIDUALIZATION. May also qualify as STANDARDIZATION if the comment emphasizes the underlying sameness.
2. *"Every rapper has their own 'thing' now -- one does the baby voice, one does the mumble, one does the screamo thing -- but strip that away and it's all the same beats."* -- Explicitly describes surface variation over standardized production. **Resolution:** Qualifies as both PSEUDO_INDIVIDUALIZATION and STANDARDIZATION.
3. *"This artist is so manufactured."* -- Vague accusation without specifying the mechanism by which individuality is simulated. **Resolution:** Borderline. If context (e.g., the video being discussed, other comments in the thread) clarifies that "manufactured" refers to a constructed image of uniqueness, it qualifies. In isolation, lean toward NONE, since the comment could mean many things.

**Example Qualifying Comments:**
1. "They gave her a 'quirky' persona and some colored hair and suddenly she's supposed to be different from every other pop star. Same writers, same producers, same chord progressions."
2. "The whole 'bedroom pop' aesthetic is a brand now. Labels literally manufacture artists to look DIY and independent while giving them the same major-label push."
3. "Funny how every K-pop group has a 'unique concept' but they're all coming out of the same trainee pipeline with the same songwriting camps."

---

### 3. COMMODIFICATION_MARKET_LOGIC

**Definition:** The comment critiques the reduction of music, musical experience, or artistic value to market terms -- sales figures, streaming counts, chart positions, brand deals, or monetary value. The commenter perceives that music is treated primarily as a commodity rather than an aesthetic or expressive object.

**Adorno Concept:** Central to the culture-industry thesis in *Dialectic of Enlightenment*: "The culture industry perpetually cheats its consumers of what it perpetually promises... the pleasure of the work of art... is replaced by... exchange value." Adorno argues that when aesthetic objects enter the commodity form, their use-value (genuine aesthetic experience) is subordinated to exchange-value (market performance), and listeners internalize market metrics as proxies for quality.

**Inclusion Criteria:**
- The comment criticizes the conflation of commercial success with artistic merit (e.g., "Just because it went platinum doesn't mean it's good").
- The comment objects to music being discussed primarily in terms of sales, streams, chart positions, or revenue.
- The comment critiques artists for prioritizing commercial viability over artistic integrity, or labels for making decisions based purely on market logic.
- The comment identifies sponsorship, product placement, brand integration, or monetization strategies as corrupting the music.
- The comment laments that music has become "content" for platforms, reduced to a delivery mechanism for advertising or engagement metrics.

**Exclusion Criteria:**
- The comment simply celebrates or reports commercial success without critique ("10 million streams! Deserved!").
- The comment discusses the business of music neutrally or approvingly.
- The comment criticizes an artist for "selling out" purely as a betrayal of subcultural identity, without connecting it to the broader commodification of art (this is closer to fan gatekeeping than Adornoian critique).

**Edge Cases:**
1. *"This song only exists because TikTok needed a new 15-second trend."* -- Identifies the subordination of the musical work to platform-driven commercial logic. **Resolution:** Qualifies as COMMODIFICATION_MARKET_LOGIC. The comment frames the song's existence as dictated by market/platform demands rather than artistic intent.
2. *"She sold out."* -- Ambiguous. Could mean "abandoned artistic principles for money" (potentially qualifying) or "sold out a concert venue" (not qualifying) or simply express betrayal of a fanbase. **Resolution:** Without additional context specifying a critique of market logic, this is NONE.
3. *"Why do people care about streams? Just enjoy the music."* -- Directly critiques the substitution of market metrics for aesthetic experience. **Resolution:** Qualifies as COMMODIFICATION_MARKET_LOGIC.

**Example Qualifying Comments:**
1. "Nobody talks about whether the album is actually good anymore. It's all 'first week sales,' 'chart position,' 'did it go number one.' We turned art into a stock market."
2. "This song was clearly designed for sync licensing. It's not music, it's a jingle waiting for a commercial."
3. "They chopped the album into 20 two-minute tracks because that's how you game the streaming algorithm. The art is secondary to the business model."

---

### 4. REGRESSIVE_LISTENING

**Definition:** The comment identifies or critiques a mode of listening in which audiences consume music passively, distractedly, or as a vehicle for pre-programmed emotional responses rather than engaging critically or attentively with the work. The commenter perceives that listeners have been conditioned to accept rather than evaluate.

**Adorno Concept:** Maps to Adorno's concept of *regressive listening* from "On the Fetish-Character in Music and the Regression of Listening" (1938), where he argues that mass-produced music trains listeners to respond to isolated, pre-digested stimuli (a catchy hook, a familiar chord change) rather than apprehending the work as an integrated whole. Listeners regress to "infantile" modes of engagement -- recognition replaces cognition, comfort replaces challenge.

**Inclusion Criteria:**
- The comment criticizes audiences for uncritical consumption, herd behavior, or inability to distinguish quality from popularity.
- The comment argues that listeners have been conditioned or dumbed down by the industry, algorithms, or social media.
- The comment critiques the reduction of listening to passive background activity, mood regulation, or playlist fodder.
- The comment observes that audiences demand comfort and familiarity, rejecting anything challenging or unfamiliar.
- The comment laments the shortening of attention spans, skip culture, or the inability to engage with a full album.

**Exclusion Criteria:**
- The comment expresses personal preference for accessible music without framing it as a systemic problem ("I just like catchy songs" is not a critique of regressive listening).
- The comment insults other listeners' taste without identifying a mechanism of conditioning or regression ("You have bad taste" is not REGRESSIVE_LISTENING; it is an insult).
- The comment critiques a specific listener or fan without generalizing to a systemic pattern.

**Edge Cases:**
1. *"People only listen to whatever TikTok tells them to."* -- Identifies algorithm-driven passive consumption but could also be simple gatekeeping. **Resolution:** Qualifies as REGRESSIVE_LISTENING if the comment frames the behavior as a loss of autonomous judgment. If it reads as pure snobbery without identifying a mechanism, lean toward NONE.
2. *"Nobody listens to full albums anymore. It's all playlists and singles. Music is just background noise now."* -- Directly identifies the shift from active, engaged listening to passive, fragmented consumption. **Resolution:** Qualifies as REGRESSIVE_LISTENING. May also qualify as COMMODIFICATION_MARKET_LOGIC if the comment connects the shift to industry or platform strategy.
3. *"The fans will eat up anything she releases."* -- Could be a critique of uncritical consumption or simply an expression of frustration with a fanbase. **Resolution:** Qualifies if the framing implies that the fanbase has been conditioned to accept any product regardless of quality. Does not qualify if the tone is merely jealous or dismissive.

**Example Qualifying Comments:**
1. "We've been so conditioned by playlists and algorithms that nobody even knows how to sit with an album anymore. People skip a track if it doesn't hook them in 5 seconds."
2. "The comments here are just 'this is a vibe' and 'this heals me.' Nobody's actually listening to the music -- they're just consuming a mood."
3. "It's scary how the industry has trained a whole generation to equate familiarity with quality. If it doesn't sound like something you've already heard, people reject it instantly."

---

### 5. AFFECTIVE_PREPACKAGING

**Definition:** The comment identifies or critiques the engineering of emotional responses through calculated musical, visual, or narrative techniques -- the perception that the listener's feelings are being manufactured, manipulated, or pre-determined by the production rather than arising from genuine aesthetic encounter.

**Adorno Concept:** Relates to Adorno's argument in *Dialectic of Enlightenment* that the culture industry "pre-digests" experience for the consumer: "The culture industry not so much adapts to the reactions of its customers as it dictates them." The emotional trajectory of the commodity is scripted in advance; the listener's affective response is a product of the industrial process, not of authentic engagement. Also connects to the discussion of "emotional stimuli" as plug-in components in "On Popular Music," where Adorno describes how musical effects are designed to trigger automatic emotional responses.

**Inclusion Criteria:**
- The comment accuses a song, video, or performance of emotional manipulation -- using calculated techniques (key changes, swelling strings, children's choirs, slow-motion video) to force a specific emotional response.
- The comment argues that the emotional content of the music is manufactured or insincere -- "designed to make you cry" rather than expressing genuine feeling.
- The comment identifies formulaic emotional structures (e.g., "sad verse, uplifting chorus, triumphant bridge" as a template for generating feeling).
- The comment critiques the use of music in contexts designed to manufacture affect (e.g., reality TV audition edits, trailer music, "reaction" content).

**Exclusion Criteria:**
- The comment describes being emotionally moved by the music without framing the emotion as manufactured ("This made me cry" is not a critique of affective prepackaging; it is a sincere emotional response).
- The comment critiques a song as emotionally flat or unmoving without identifying a mechanism of manipulation (this is an aesthetic judgment, not a critique of prepackaging).
- The comment praises emotional effectiveness ("This song really knows how to hit you in the feels") without any sense that the manipulation is problematic.

**Edge Cases:**
1. *"The key change at 3:12 is so manipulative. They know exactly what they're doing."* -- Identifies a specific production technique deployed for calculated emotional effect. **Resolution:** Qualifies as AFFECTIVE_PREPACKAGING. The word "manipulative" combined with the identification of a specific technique signals a critique of engineered affect.
2. *"This is emotional porn. It's designed to make you feel something so you share it."* -- Explicitly frames the emotional content as manufactured for engagement. **Resolution:** Qualifies as AFFECTIVE_PREPACKAGING. May also qualify as COMMODIFICATION_MARKET_LOGIC if the sharing/engagement dimension is emphasized.
3. *"This is so sad."* -- Pure emotional response with no critique of the mechanism producing the emotion. **Resolution:** NONE.

**Example Qualifying Comments:**
1. "They added the children's choir and the key change at the end because they knew it would go viral as a 'reaction' clip. It's not art, it's emotional engineering."
2. "Every ballad follows the same formula: start quiet and vulnerable, build through the second verse, hit the big note in the bridge. Your tears are being manufactured."
3. "This whole 'stripped-back acoustic version' trend is calculated. They release the pop version for streams, then the acoustic version to seem 'real' and 'emotional.' Both versions are equally produced."

---

### 6. FORMAL_RESISTANCE

**Definition:** The comment praises, advocates for, or identifies music or musical practices that resist culture-industry logic -- art that challenges standardization, refuses commodification, demands active listening, or breaks from formulaic emotional structures. The commenter positions certain music as a genuine alternative to the administered culture.

**Adorno Concept:** Rooted in Adorno's valorization of autonomous art in *Aesthetic Theory* (1970) and his championing of composers like Schoenberg who, through formal innovation (atonality, twelve-tone technique), refused to capitulate to the demands of the market. For Adorno, genuine art resists by maintaining its formal integrity, demanding active intellectual engagement, and refusing to provide the easy pleasures that the culture industry trains consumers to expect. Note: this label captures *the commenter's perception* of resistance, not a judgment about whether the music objectively achieves Adornoian autonomy.

**Inclusion Criteria:**
- The comment praises music specifically for its refusal to conform to industry formulas, trends, or commercial pressures.
- The comment frames an artist as resisting commodification, maintaining artistic integrity despite market incentives.
- The comment advocates for experimental, challenging, or formally innovative music as an antidote to the culture industry.
- The comment identifies specific formal choices (unconventional structures, dissonant harmonies, rejection of hooks, extended duration) as acts of resistance against standardization.
- The comment critiques the culture industry while simultaneously championing an alternative.

**Exclusion Criteria:**
- The comment praises music purely on aesthetic grounds without connecting the praise to resistance against industry logic ("This album is a masterpiece" is not FORMAL_RESISTANCE unless the praise is framed in opposition to the culture industry).
- The comment engages in hipster gatekeeping or elitism without articulating a critique of industry mechanisms ("You guys wouldn't understand real music" is snobbery, not resistance).
- The comment praises underground or independent music solely for its obscurity rather than for any formal or structural resistance.

**Edge Cases:**
1. *"This is what happens when an artist doesn't care about streaming numbers and just makes art."* -- Frames artistic production as resistance to market logic. **Resolution:** Qualifies as FORMAL_RESISTANCE. Also potentially COMMODIFICATION_MARKET_LOGIC (the inverse critique is implied).
2. *"Finally an album that doesn't follow the 3-minute-single formula. Every track is 7+ minutes and demands your attention."* -- Praises formal choices (duration, complexity) as a counter to standardized formats. **Resolution:** Qualifies as FORMAL_RESISTANCE.
3. *"This band is so underground, you've definitely never heard of them."* -- Obscurity as social capital, not as resistance to industry logic. **Resolution:** NONE.

**Example Qualifying Comments:**
1. "This is the kind of album the industry doesn't want you to hear. No singles, no hooks, no concessions. Just 50 minutes of music that trusts the listener to pay attention."
2. "She could've gone the easy route and made radio-friendly pop but instead she made something genuinely challenging. That's real artistry."
3. "The fact that this has no chorus is exactly the point. Not every song needs to be optimized for Spotify's 30-second skip threshold."

---

### 7. NONE

**Definition:** The comment does not contain any identifiable critique of culture-industry mechanisms. It may express personal taste, emotional responses, factual observations, fan appreciation, humor, spam, or any other content that does not engage -- even implicitly -- with the dynamics of standardization, pseudo-individualization, commodification, regressive listening, affective prepackaging, or formal resistance.

**Adorno Concept:** N/A. This is the default label indicating the absence of culture-industry critique.

**Inclusion Criteria:**
- Pure expressions of taste or preference: "I love this song," "This is trash," "Not my thing."
- Emotional responses without critique of the mechanism producing them: "This made me cry," "Goosebumps at 2:34."
- Factual observations: "This was recorded in Abbey Road Studios," "The bassist is [name]."
- Fan discourse: "Stream [song]!," "We need a collab with [artist]," "Who's here in 2026?"
- Humor, memes, copypasta, or irrelevant content.
- Spam, self-promotion, or off-topic comments.
- Emoji-only comments.
- Quoted lyrics without commentary.
- Vague quality judgments without any identifiable critical mechanism: "This slaps," "Banger," "Mid," "Trash."

**Exclusion Criteria:**
- Any comment that qualifies for one or more of the six critique labels above.

**Edge Cases:**
1. *"This slaps."* -- Pure affect, no critique. **Resolution:** NONE.
2. *"Why doesn't anyone make music like this anymore?"* -- Potentially implies standardization critique but is too vague to qualify. **Resolution:** NONE, unless additional context clarifies a critique of specific industry mechanisms.
3. *"I only listen to vinyl."* -- Format preference that *could* imply resistance to digital commodification but, in isolation, is a lifestyle statement. **Resolution:** NONE.

**Example Qualifying Comments:**
1. "This is the best song of 2025, no debate."
2. "Who else is watching this at 3am?"
3. "The guitar solo at 4:12 is insane."

---

## Multi-Label Policy

### Mutual Exclusivity of NONE

NONE is assigned **if and only if** all six critique labels (STANDARDIZATION, PSEUDO_INDIVIDUALIZATION, COMMODIFICATION_MARKET_LOGIC, REGRESSIVE_LISTENING, AFFECTIVE_PREPACKAGING, FORMAL_RESISTANCE) are **false** for the comment. If any critique label is true, NONE must be false. Conversely, if NONE is true, all critique labels must be false. NONE functions as a logical complement: `NONE = NOT (L1 OR L2 OR L3 OR L4 OR L5 OR L6)`.

### Multi-Label Assignment

Comments may carry **multiple critique labels** simultaneously. Culture-industry critique is frequently multidimensional: a comment might identify standardization *and* pseudo-individualization in the same breath, or critique commodification while advocating for formal resistance. Each label is evaluated independently. Common co-occurrences include:

- **STANDARDIZATION + PSEUDO_INDIVIDUALIZATION:** "Every artist sounds the same but they all have a 'unique aesthetic' to distract you." The comment identifies both the underlying sameness and the surface-level differentiation.
- **COMMODIFICATION_MARKET_LOGIC + REGRESSIVE_LISTENING:** "People just stream whatever the algorithm pushes. Music is a product now and listeners are consumers, not audiences." The comment critiques both the commodity form and the passive reception it produces.
- **AFFECTIVE_PREPACKAGING + FORMAL_RESISTANCE:** "Unlike every other ballad designed to make you cry on cue, this song earns its emotion through genuine musical development." The comment critiques prepackaged affect while praising a specific work's resistance to it.
- **COMMODIFICATION_MARKET_LOGIC + FORMAL_RESISTANCE:** "This is what happens when an artist doesn't chase playlists." Both the critique and the counter-model are present.

### Sarcasm and Irony

Sarcastic or ironic comments require careful treatment:

- **Detection:** Look for markers such as "/s," "lol," absurd exaggeration, contradiction between literal content and apparent intent, or context (e.g., a comment praising the exact thing the video critiques).
- **If sarcasm is detected and the sarcastic reading constitutes a critique:** Assign the relevant critique label(s) but **reduce confidence** by one tier (e.g., from "high" to "medium") and **flag for human review**.
- **If sarcasm is ambiguous:** Assign NONE and flag for review. Do not guess.
- **Example:** *"Wow, so original, nobody's ever done a trap beat with Auto-Tune before."* -- Sarcastic; the genuine meaning is a critique of standardization. Assign STANDARDIZATION with reduced confidence and a review flag.

### Vague Affect and Dismissals

Comments consisting solely of vague affective language or dismissals **without** identifying any culture-industry mechanism default to NONE:

- "This slaps" => NONE
- "Trash" => NONE
- "Mid" => NONE
- "Banger" => NONE
- "Not it" => NONE
- "Overrated" => NONE (unless followed by a reason that invokes a critique mechanism)

The threshold for a critique label is the identification -- however implicit -- of a *mechanism* (standardization, manufactured individuality, market logic, conditioned listening, engineered emotion, or formal resistance). A bare evaluative word does not cross this threshold.

### Quoted Lyrics vs. Commenter Voice

When a comment includes quoted lyrics, distinguish between the lyric content and the commenter's own voice:

- **Quoted lyrics alone** (e.g., a user posting a favorite line) => NONE. The lyrics are the artist's text, not the commenter's critique.
- **Quoted lyrics with commentary** => Evaluate the commentary for critique labels. The lyrics serve as context but are not themselves the unit of analysis.
- **Commenter paraphrasing or referencing lyrics to make a critical point** => Evaluate normally. The commenter is deploying the lyrics rhetorically.
- **Example:** *"'I'm not like the other girls' -- yeah right, your whole image was designed by a marketing team."* The quoted lyric is context; the commenter's voice critiques pseudo-individualization. Assign PSEUDO_INDIVIDUALIZATION.
