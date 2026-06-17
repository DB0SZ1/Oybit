"""
Oybit Persona Engine — Question Bank
Each platform has its own 60-question set.
Questions are grouped into 7 layers with progressive unlock rules.
"""

LINKEDIN_QUESTIONS = [
    # ── Layer 01: Who You Are (Q1-Q10) — Core onboarding ──
    {
        "id": "q1", "layer": 1, "number": 1,
        "question": "What's your professional title or role, and how do you want people to introduce you?",
        "why": "Sets the anchor for every post's authorial voice.",
        "type": "text",
        "field": "identity.title"
    },
    {
        "id": "q2", "layer": 1, "number": 2,
        "question": "How many years of experience do you have in your field?",
        "why": "Calibrates authority level and how you frame expertise.",
        "type": "text",
        "field": "identity.experience_years"
    },
    {
        "id": "q3", "layer": 1, "number": 3,
        "question": "Name the 3 biggest professional wins you've had in the last 2 years.",
        "why": "Source material for proof-driven storytelling.",
        "type": "textarea",
        "field": "identity.wins"
    },
    {
        "id": "q4", "layer": 1, "number": 4,
        "question": "What problem do you solve for the world? One sentence.",
        "why": "The core positioning statement that flavors all content.",
        "type": "text",
        "field": "identity.problem_solved"
    },
    {
        "id": "q5", "layer": 1, "number": 5,
        "question": "How did you get into your field — what's the origin story?",
        "why": "The 'why I'm here' narrative for authenticity posts.",
        "type": "textarea",
        "field": "identity.origin_story"
    },
    {
        "id": "q6", "layer": 1, "number": 6,
        "question": "Are you a solo founder, part of a team, or building something on the side?",
        "why": "Frames the builder angle and content perspective.",
        "type": "choice",
        "options": ["Solo founder", "Part of a team", "Building on the side", "Corporate professional"],
        "field": "identity.builder_type"
    },
    {
        "id": "q7", "layer": 1, "number": 7,
        "question": "What companies, institutions, or brands have shaped your professional identity?",
        "why": "Social proof signals and affiliation framing.",
        "type": "text",
        "field": "identity.affiliations"
    },
    {
        "id": "q8", "layer": 1, "number": 8,
        "question": "Do you primarily lead people, build products, sell things, or create ideas?",
        "why": "Determines which content archetypes fit you naturally.",
        "type": "choice",
        "options": ["Lead people", "Build products", "Sell things", "Create ideas", "All of the above"],
        "field": "identity.primary_mode"
    },
    {
        "id": "q9", "layer": 1, "number": 9,
        "question": "What's the thing you know that most people in your space genuinely don't?",
        "why": "The 'secret insight' that makes your POV worth following.",
        "type": "textarea",
        "field": "identity.secret_insight"
    },
    {
        "id": "q10", "layer": 1, "number": 10,
        "question": "If someone followed you on LinkedIn for 3 months, what would they say you're known for?",
        "why": "The intended brand impression — quality check on the full persona.",
        "type": "textarea",
        "field": "identity.brand_impression"
    },

    # ── Layer 02: Voice & Tone (Q11-Q20) — Unlocks after 3 posts ──
    {
        "id": "q11", "layer": 2, "number": 11,
        "question": "Pick 3 adjectives that describe exactly how you want to sound on LinkedIn.",
        "why": "Primary tone parameters for the AI prompt builder.",
        "type": "text",
        "field": "voice.adjectives"
    },
    {
        "id": "q12", "layer": 2, "number": 12,
        "question": "Are you more formal & authoritative, or casual & relatable — or somewhere in between?",
        "why": "Baseline register calibration.",
        "type": "scale",
        "scale_labels": ["Very Casual", "Casual", "Balanced", "Authoritative", "Very Formal"],
        "field": "voice.formality"
    },
    {
        "id": "q13", "layer": 2, "number": 13,
        "question": "Do you use humor? If yes — dry wit, self-deprecating, playful, or sharp?",
        "why": "Humor type affects sentence structure and timing.",
        "type": "choice",
        "options": ["No humor", "Dry wit", "Self-deprecating", "Playful", "Sharp/sarcastic"],
        "field": "voice.humor_style"
    },
    {
        "id": "q14", "layer": 2, "number": 14,
        "question": "How do you feel about using slang or internet language in professional posts?",
        "why": "Code-switching threshold.",
        "type": "choice",
        "options": ["Never — keep it professional", "Rarely, only when it fits", "Sometimes, I like staying current", "Often — it's part of my voice"],
        "field": "voice.slang_tolerance"
    },
    {
        "id": "q15", "layer": 2, "number": 15,
        "question": "How long do your sentences naturally run — short punchy lines or longer structured paragraphs?",
        "why": "Rhythm fingerprint — controls formatting decisions.",
        "type": "choice",
        "options": ["Short punchy lines", "Medium — mix of both", "Longer structured paragraphs"],
        "field": "voice.sentence_length"
    },
    {
        "id": "q16", "layer": 2, "number": 16,
        "question": "Do you prefer telling stories or sharing frameworks?",
        "why": "Narrative vs. analytical content split.",
        "type": "choice",
        "options": ["Stories — I use narrative", "Frameworks — I use structure", "Both equally"],
        "field": "voice.story_vs_framework"
    },
    {
        "id": "q17", "layer": 2, "number": 17,
        "question": "When someone reads your post, what emotion do you want them to feel?",
        "why": "Emotional intent shapes word choice and pacing.",
        "type": "text",
        "field": "voice.target_emotion"
    },
    {
        "id": "q18", "layer": 2, "number": 18,
        "question": "Name 2–3 LinkedIn creators whose writing style you admire — and why.",
        "why": "Style reference anchors for pattern matching.",
        "type": "textarea",
        "field": "voice.style_references"
    },
    {
        "id": "q19", "layer": 2, "number": 19,
        "question": "What LinkedIn writing habits genuinely annoy you — buzzwords, phrases, styles?",
        "why": "The negative voice space — what Oybit must avoid for you.",
        "type": "textarea",
        "field": "voice.anti_patterns"
    },
    {
        "id": "q20", "layer": 2, "number": 20,
        "question": "Do you write in first person naturally, or does it feel uncomfortable to you?",
        "why": "Affects how direct and personal the content can be.",
        "type": "choice",
        "options": ["Yes — I write in first person naturally", "Sometimes — depends on the topic", "No — it feels uncomfortable"],
        "field": "voice.first_person_comfort"
    },

    # ── Layer 03: Content Pillars (Q21-Q30) — Unlocks after 3 posts ──
    {
        "id": "q21", "layer": 3, "number": 21,
        "question": "List 5 topics you could talk about for hours without notes.",
        "why": "Primary content pillars — the main topic rotation.",
        "type": "textarea",
        "field": "pillars.core_topics"
    },
    {
        "id": "q22", "layer": 3, "number": 22,
        "question": "What's the most controversial opinion you hold in your industry?",
        "why": "Hot-take and debate-starter content source.",
        "type": "textarea",
        "field": "pillars.hot_take"
    },
    {
        "id": "q23", "layer": 3, "number": 23,
        "question": "What do most people in your field get completely wrong?",
        "why": "The 'myth-buster' angle that drives high engagement.",
        "type": "textarea",
        "field": "pillars.common_misconception"
    },
    {
        "id": "q24", "layer": 3, "number": 24,
        "question": "What topic do you wish more people talked about in your niche?",
        "why": "Underserved angle for thought leadership differentiation.",
        "type": "textarea",
        "field": "pillars.underserved_topic"
    },
    {
        "id": "q25", "layer": 3, "number": 25,
        "question": "What recent experience — win, loss, or lesson — do you want to write about?",
        "why": "Timely story content that feels current, not evergreen.",
        "type": "textarea",
        "field": "pillars.recent_story"
    },
    {
        "id": "q26", "layer": 3, "number": 26,
        "question": "Are you currently building something? What's update-worthy about where you are now?",
        "why": "Build-in-public material and proof of motion.",
        "type": "textarea",
        "field": "pillars.building_in_public"
    },
    {
        "id": "q27", "layer": 3, "number": 27,
        "question": "What tools, workflows, or systems have genuinely changed how you work?",
        "why": "Tactical recommendation content — high saves, high shares.",
        "type": "textarea",
        "field": "pillars.tools_and_workflows"
    },
    {
        "id": "q28", "layer": 3, "number": 28,
        "question": "What books, podcasts, or ideas have shaped your thinking this year?",
        "why": "Intellectual influence mapping for associative credibility.",
        "type": "textarea",
        "field": "pillars.intellectual_influences"
    },
    {
        "id": "q29", "layer": 3, "number": 29,
        "question": "What mistakes have you made that others in your space could learn from?",
        "why": "Vulnerability-based content — strongest trust signal on LinkedIn.",
        "type": "textarea",
        "field": "pillars.mistakes_and_lessons"
    },
    {
        "id": "q30", "layer": 3, "number": 30,
        "question": "What advice do you give people who are 2–3 years behind you in your field?",
        "why": "Mentorship-tone posts — drives followers and comments.",
        "type": "textarea",
        "field": "pillars.advice_to_junior"
    },

    # ── Layer 04: Your Audience (Q31-Q38) — Unlocks after 7 posts ──
    {
        "id": "q31", "layer": 4, "number": 31,
        "question": "Who do you most want to reach — job title, industry, career stage?",
        "why": "The primary reader avatar for every content decision.",
        "type": "textarea",
        "field": "audience.primary_target"
    },
    {
        "id": "q32", "layer": 4, "number": 32,
        "question": "Are you writing for beginners, intermediate practitioners, or peer-level experts?",
        "why": "Jargon threshold and explanation depth calibration.",
        "type": "choice",
        "options": ["Beginners — explain everything", "Intermediate — assume some knowledge", "Peer experts — no hand-holding"],
        "field": "audience.expertise_level"
    },
    {
        "id": "q33", "layer": 4, "number": 33,
        "question": "What is your audience's biggest professional frustration right now?",
        "why": "Empathy hook material.",
        "type": "textarea",
        "field": "audience.biggest_frustration"
    },
    {
        "id": "q34", "layer": 4, "number": 34,
        "question": "What does your audience want but doesn't know how to ask for?",
        "why": "The 'aha moment' content angle.",
        "type": "textarea",
        "field": "audience.unspoken_desire"
    },
    {
        "id": "q35", "layer": 4, "number": 35,
        "question": "What type of LinkedIn content does your audience already engage with?",
        "why": "Existing behavior baseline — don't fight the format.",
        "type": "textarea",
        "field": "audience.existing_engagement"
    },
    {
        "id": "q36", "layer": 4, "number": 36,
        "question": "What's the biggest misconception your audience has about your field or what you do?",
        "why": "Correction-narrative content — authority-builder.",
        "type": "textarea",
        "field": "audience.misconception"
    },
    {
        "id": "q37", "layer": 4, "number": 37,
        "question": "Would you describe your ideal reader as skeptical, aspirational, or a peer?",
        "why": "Determines whether to prove, inspire, or challenge.",
        "type": "choice",
        "options": ["Skeptical — I need to prove things", "Aspirational — I inspire them", "Peer — we talk as equals"],
        "field": "audience.reader_mindset"
    },
    {
        "id": "q38", "layer": 4, "number": 38,
        "question": "What kind of person do you NOT want to attract on LinkedIn — and why?",
        "why": "Anti-audience signals.",
        "type": "textarea",
        "field": "audience.anti_audience"
    },

    # ── Layer 05: Story & Narrative (Q39-Q46) — Unlocks after 14 posts ──
    {
        "id": "q39", "layer": 5, "number": 39,
        "question": "What's the hardest professional moment you've had, and what did it teach you?",
        "why": "The core adversity story — strongest performing content type.",
        "type": "textarea",
        "field": "narrative.hardest_moment"
    },
    {
        "id": "q40", "layer": 5, "number": 40,
        "question": "What's a clear before-and-after from your career that people should know?",
        "why": "Transformation arc — drives comments and saves.",
        "type": "textarea",
        "field": "narrative.transformation"
    },
    {
        "id": "q41", "layer": 5, "number": 41,
        "question": "Is there a moment you almost quit or pivoted significantly? What happened?",
        "why": "Tension and resolution narrative — high relatability.",
        "type": "textarea",
        "field": "narrative.almost_quit"
    },
    {
        "id": "q42", "layer": 5, "number": 42,
        "question": "What's something personal about you that genuinely shapes how you work?",
        "why": "Character humanization.",
        "type": "textarea",
        "field": "narrative.personal_trait"
    },
    {
        "id": "q43", "layer": 5, "number": 43,
        "question": "What do people always ask you about at networking events or in DMs?",
        "why": "Social proof that validates your expertise positioning.",
        "type": "textarea",
        "field": "narrative.frequently_asked"
    },
    {
        "id": "q44", "layer": 5, "number": 44,
        "question": "If you wrote a book right now, what would the title be?",
        "why": "Crystallizes your intellectual brand in a single phrase.",
        "type": "text",
        "field": "narrative.book_title"
    },
    {
        "id": "q45", "layer": 5, "number": 45,
        "question": "What belief do you hold that used to be unpopular but is now going mainstream?",
        "why": "'I said it first' content — positions you as ahead of the curve.",
        "type": "textarea",
        "field": "narrative.ahead_of_curve"
    },
    {
        "id": "q46", "layer": 5, "number": 46,
        "question": "What legacy do you want to leave in your field in 10 years?",
        "why": "Vision framing for mission-driven content.",
        "type": "textarea",
        "field": "narrative.legacy"
    },

    # ── Layer 06: Engagement Style (Q47-Q54) — Unlocks after 14 posts ──
    {
        "id": "q47", "layer": 6, "number": 47,
        "question": "Do you reply to every comment, most comments, or let conversations run naturally?",
        "why": "Engagement rate targeting and response scope.",
        "type": "choice",
        "options": ["Every comment — I reply to all", "Most comments — I'm selective", "Let it run — I chime in occasionally"],
        "field": "engagement.reply_style"
    },
    {
        "id": "q48", "layer": 6, "number": 48,
        "question": "How do you handle pushback or disagreement in your comments?",
        "why": "Conflict response tone.",
        "type": "choice",
        "options": ["Lean in — I love a debate", "Engage calmly and move on", "Stay neutral and factual", "Deflect gracefully"],
        "field": "engagement.conflict_handling"
    },
    {
        "id": "q49", "layer": 6, "number": 49,
        "question": "Do you tag companies or people in posts, or keep it purely idea-driven?",
        "why": "Tagging strategy affects reach and political risk.",
        "type": "choice",
        "options": ["Tag freely — it builds relationships", "Rarely — only when essential", "Never — ideas speak for themselves"],
        "field": "engagement.tagging_policy"
    },
    {
        "id": "q50", "layer": 6, "number": 50,
        "question": "Do you want to post on a consistent schedule or only when something's worth saying?",
        "why": "Posting cadence mode.",
        "type": "choice",
        "options": ["Consistent schedule — routine builds trust", "Only when I have something real to say", "Mostly consistent with some reactive posts"],
        "field": "engagement.cadence_preference"
    },
    {
        "id": "q51", "layer": 6, "number": 51,
        "question": "How personal are you willing to get — strictly professional or share life context too?",
        "why": "Personal disclosure threshold.",
        "type": "choice",
        "options": ["Strictly professional", "Mostly professional with personal hints", "Openly personal — I share my real life"],
        "field": "engagement.personal_disclosure"
    },
    {
        "id": "q52", "layer": 6, "number": 52,
        "question": "Do you want to reshare and comment on others' posts as part of your presence?",
        "why": "Network activation vs. pure broadcast approach.",
        "type": "choice",
        "options": ["Yes — community engagement matters", "Sometimes — when it adds value", "No — focus on original content only"],
        "field": "engagement.reshare_policy"
    },
    {
        "id": "q53", "layer": 6, "number": 53,
        "question": "How do you feel about polls, open questions, or obvious engagement prompts?",
        "why": "Engagement mechanics permission scope.",
        "type": "choice",
        "options": ["Love them — they drive conversation", "Use sparingly — feels forced otherwise", "Avoid them — feels manipulative"],
        "field": "engagement.prompts_policy"
    },
    {
        "id": "q54", "layer": 6, "number": 54,
        "question": "What's one type of post you would never make on LinkedIn — and why?",
        "why": "Hard content boundary for the negative constraint layer.",
        "type": "textarea",
        "field": "engagement.hard_never"
    },

    # ── Layer 07: Goals (Q55-Q60) — Unlocks after 21 posts ──
    {
        "id": "q55", "layer": 7, "number": 55,
        "question": "What do you want LinkedIn to do for you — leads, hiring, brand, community, or investors?",
        "why": "Primary objective — determines content-to-CTA ratio and framing.",
        "type": "choice",
        "options": ["Generate leads / clients", "Build my personal brand", "Attract investors", "Build a community", "Find talent / hiring", "All of the above"],
        "field": "goals.primary_objective"
    },
    {
        "id": "q56", "layer": 7, "number": 56,
        "question": "What's your current follower count and where do you want it in 12 months?",
        "why": "Growth target for scheduling cadence and volume decisions.",
        "type": "text",
        "field": "goals.follower_target"
    },
    {
        "id": "q57", "layer": 7, "number": 57,
        "question": "Are you optimizing for likes and comments, profile views, DMs, or off-platform conversions?",
        "why": "Success metric calibration for the feedback loop.",
        "type": "choice",
        "options": ["Likes & comments (engagement)", "Profile views (visibility)", "DMs (direct relationships)", "Off-platform conversions (revenue)"],
        "field": "goals.success_metric"
    },
    {
        "id": "q58", "layer": 7, "number": 58,
        "question": "What doors do you specifically want LinkedIn to open for you this year?",
        "why": "Concrete outcome framing.",
        "type": "textarea",
        "field": "goals.doors_to_open"
    },
    {
        "id": "q59", "layer": 7, "number": 59,
        "question": "How much time per week can you realistically put into LinkedIn content?",
        "why": "Workload constraint — sets automation depth requirement.",
        "type": "choice",
        "options": ["Less than 1 hour — fully automate", "1-2 hours — light review", "2-4 hours — active involvement", "4+ hours — hands-on"],
        "field": "goals.time_budget"
    },
    {
        "id": "q60", "layer": 7, "number": 60,
        "question": "What does 'LinkedIn working' actually look like for you? Name the specific signal.",
        "why": "The north star signal that Oybit's analytics loop optimizes toward.",
        "type": "textarea",
        "field": "goals.north_star"
    },
]

# Unlock thresholds per layer (based on published post count)
LAYER_UNLOCK_THRESHOLDS = {
    1: 0,   # Core — available immediately
    2: 3,   # Voice & Tone — after 3 posts
    3: 3,   # Content Pillars — after 3 posts
    4: 7,   # Audience — after 7 posts
    5: 14,  # Narrative — after 14 posts
    6: 14,  # Engagement Style — after 14 posts
    7: 21,  # Goals — after 21 posts
}


def get_questions(platform: str = "linkedin", layer: int = None):
    """Return questions for a given platform, optionally filtered by layer."""
    if platform == "linkedin":
        questions = LINKEDIN_QUESTIONS
    else:
        # Other platforms default to LinkedIn questions until their own are built
        questions = LINKEDIN_QUESTIONS

    if layer is not None:
        return [q for q in questions if q["layer"] == layer]
    return questions


def get_available_questions(platform: str, published_post_count: int, layer: int = None):
    """Return only the questions whose layer has been unlocked based on post count."""
    all_questions = get_questions(platform, layer)
    return [
        q for q in all_questions
        if LAYER_UNLOCK_THRESHOLDS.get(q["layer"], 999) <= published_post_count
    ]
