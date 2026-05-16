"""
Onboarding Questions Bank — Agent A Module
Full 180-question bank organized by stage (1-6).

Stage 1: 30 core identity + voice + audience questions
Stage 2: 30 simulation scenarios
Stage 3: 30 tone deep-dive questions
Stage 4: 15 content boundary questions (unlocks at 2 weeks)
Stage 5: 15 audience empathy questions (unlocks after 20 posts)
Stage 6: 10 engagement style questions (unlocks after 50 posts)
"""


QUESTIONS = [
    # ════════════════════════════════════════════════════════
    # STAGE 1: Core Identity & Voice (30 questions)
    # ════════════════════════════════════════════════════════
    {"id": "q1_01", "stage": 1, "question_text": "What is your primary mission with your brand?", "question_type": "open"},
    {"id": "q1_02", "stage": 1, "question_text": "Which phrase best describes your technical approach?", "question_type": "choice",
     "options": ["Move fast and break things", "Systems over hustle", "Perfection is the goal", "Scale from day one"]},
    {"id": "q1_03", "stage": 1, "question_text": "What are you 'standing against' in your industry?", "question_type": "open"},
    {"id": "q1_04", "stage": 1, "question_text": "How formal is your tone on LinkedIn? (1=very casual, 10=very formal)", "question_type": "scale", "min_value": 1, "max_value": 10},
    {"id": "q1_05", "stage": 1, "question_text": "How formal is your tone on Instagram? (1=very casual, 10=very formal)", "question_type": "scale", "min_value": 1, "max_value": 10},
    {"id": "q1_06", "stage": 1, "question_text": "Name 2-3 people or brands whose voice sounds similar to yours.", "question_type": "open"},
    {"id": "q1_07", "stage": 1, "question_text": "What word would your audience NEVER hear you say?", "question_type": "open"},
    {"id": "q1_08", "stage": 1, "question_text": "What words or phrases do you use constantly? (signature vocabulary)", "question_type": "open"},
    {"id": "q1_09", "stage": 1, "question_text": "Do you use emojis in your posts?", "question_type": "choice",
     "options": ["Never", "Rarely (1-2 per post)", "Occasionally", "Frequently"]},
    {"id": "q1_10", "stage": 1, "question_text": "What's your humor style?", "question_type": "choice",
     "options": ["None — always serious", "Dry/deadpan", "Self-deprecating", "Playful", "Sarcastic"]},
    {"id": "q1_11", "stage": 1, "question_text": "Do you ever swear in your content?", "question_type": "choice",
     "options": ["Never", "Rarely (mild)", "Context-dependent", "Freely"]},
    {"id": "q1_12", "stage": 1, "question_text": "What is your elevator pitch — one sentence for a stranger?", "question_type": "open"},
    {"id": "q1_13", "stage": 1, "question_text": "What are your core values? (list 3-5)", "question_type": "open"},
    {"id": "q1_14", "stage": 1, "question_text": "Where is your audience located geographically?", "question_type": "open"},
    {"id": "q1_15", "stage": 1, "question_text": "What age range is your primary audience?", "question_type": "choice",
     "options": ["18-24", "25-34", "35-44", "45+", "Mixed"]},
    {"id": "q1_16", "stage": 1, "question_text": "What does your audience do for a living?", "question_type": "open"},
    {"id": "q1_17", "stage": 1, "question_text": "What's the biggest pain point your audience faces?", "question_type": "open"},
    {"id": "q1_18", "stage": 1, "question_text": "What does your audience come to you for?", "question_type": "open"},
    {"id": "q1_19", "stage": 1, "question_text": "What would make your audience unfollow you?", "question_type": "open"},
    {"id": "q1_20", "stage": 1, "question_text": "What are your 3-4 main content pillars?", "question_type": "open"},
    {"id": "q1_21", "stage": 1, "question_text": "What is one thing you stand for that most people in your space do NOT stand for?", "question_type": "open"},
    {"id": "q1_22", "stage": 1, "question_text": "How do you feel about sharing personal stories publicly?", "question_type": "choice",
     "options": ["Very comfortable — it's my strength", "Comfortable with boundaries", "Only if relevant to a lesson", "Prefer to keep it professional"]},
    {"id": "q1_23", "stage": 1, "question_text": "What's your primary language for content?", "question_type": "choice",
     "options": ["English", "Yoruba", "Igbo", "Hausa", "French", "Arabic", "Other"]},
    {"id": "q1_24", "stage": 1, "question_text": "Do you prefer short punchy sentences or longer narrative?", "question_type": "choice",
     "options": ["Short punchy", "Longer narrative", "Mix of both"]},
    {"id": "q1_25", "stage": 1, "question_text": "What's your preferred sentence fragment style?", "question_type": "choice",
     "options": ["Never use fragments", "Occasionally for emphasis", "Frequently — it's my style"]},
    {"id": "q1_26", "stage": 1, "question_text": "What are your brand's primary and secondary colors? (hex or name)", "question_type": "open"},
    {"id": "q1_27", "stage": 1, "question_text": "What visual aesthetic describes your brand?", "question_type": "choice",
     "options": ["Minimal and clean", "Bold and vibrant", "Dark and moody", "Editorial/magazine", "Warm and approachable"]},
    {"id": "q1_28", "stage": 1, "question_text": "What's the origin story of your brand? (2-3 sentences)", "question_type": "open"},
    {"id": "q1_29", "stage": 1, "question_text": "Are you a personal brand, company, product, or creator?", "question_type": "choice",
     "options": ["Personal brand", "Company", "Product", "Creator"]},
    {"id": "q1_30", "stage": 1, "question_text": "What font style fits your brand?", "question_type": "choice",
     "options": ["Modern sans-serif (Inter, Outfit)", "Classic serif (Georgia, Merriweather)", "Monospace (coding aesthetic)", "Handwritten/casual", "No preference"]},

    # ════════════════════════════════════════════════════════
    # STAGE 2: Simulation Scenarios (30 questions)
    # ════════════════════════════════════════════════════════
    {"id": "q2_01", "stage": 2, "question_text": "A post in your niche is going viral with a hot take you disagree with. What do you do?", "question_type": "choice",
     "options": ["Post my own counterpoint", "Quote-tweet/share with commentary", "Ignore it", "Engage in comments only"], "scenario_type": "trending_post_reaction"},
    {"id": "q2_02", "stage": 2, "question_text": "Someone comments 'How did you build this?' on your post. How do you reply?", "question_type": "open", "scenario_type": "comment_reply_test"},
    {"id": "q2_03", "stage": 2, "question_text": "A carousel format is going viral. Would you use it?", "question_type": "choice",
     "options": ["Yes, immediately", "Yes, but adapted to my style", "Only if it fits my content", "No, I don't follow trends"], "scenario_type": "trend_format_test"},
    {"id": "q2_04", "stage": 2, "question_text": "A brand in your space just got caught in a data breach. Do you comment?", "question_type": "choice",
     "options": ["Post a thoughtful analysis", "Mention it briefly in a broader post", "Stay quiet entirely", "Only if directly asked"], "scenario_type": "controversy_response_test"},
    {"id": "q2_05", "stage": 2, "question_text": "A meme format is everywhere in your niche. Does your brand use it?", "question_type": "choice",
     "options": ["Jump in immediately", "Adapt it tastefully", "Use it but not on LinkedIn", "Never — memes aren't my brand"], "scenario_type": "meme_adaptation_test"},
    {"id": "q2_06", "stage": 2, "question_text": "Your competitor just shipped a feature you've been building. What's your move?", "question_type": "open", "scenario_type": "trending_post_reaction"},
    {"id": "q2_07", "stage": 2, "question_text": "A tech influencer with 500K followers roasts your product. How do you respond?", "question_type": "open", "scenario_type": "controversy_response_test"},
    {"id": "q2_08", "stage": 2, "question_text": "You discover a critical security flaw in a popular open-source library. Do you post about it?", "question_type": "choice",
     "options": ["Immediately share the finding", "Share after responsible disclosure", "Write a detailed breakdown post", "Keep it internal"], "scenario_type": "trending_post_reaction"},
    {"id": "q2_09", "stage": 2, "question_text": "A LinkedIn thought leader posts generic advice that contradicts your experience. Do you engage?", "question_type": "choice",
     "options": ["Respectfully disagree in comments", "Write my own counter-post", "Ignore — not worth the energy", "DM them privately"], "scenario_type": "comment_reply_test"},
    {"id": "q2_10", "stage": 2, "question_text": "Your latest product launch got zero traction. Do you post about it?", "question_type": "choice",
     "options": ["Yes — share the lesson transparently", "Only after I've found the fix", "Never — failure is private", "Yes but framed as a learning moment"], "scenario_type": "trending_post_reaction"},
    {"id": "q2_11", "stage": 2, "question_text": "A thread format with numbered tips is trending. Would you create one?", "question_type": "choice",
     "options": ["Yes, it fits my style", "Only if I have genuine insights", "No, they feel formulaic", "I'd do it differently"], "scenario_type": "trend_format_test"},
    {"id": "q2_12", "stage": 2, "question_text": "Someone tags you in a heated debate about your industry. What do you do?", "question_type": "open", "scenario_type": "controversy_response_test"},
    {"id": "q2_13", "stage": 2, "question_text": "A junior developer asks for career advice in your DMs. How do you respond?", "question_type": "open", "scenario_type": "comment_reply_test"},
    {"id": "q2_14", "stage": 2, "question_text": "A new AI tool threatens to replace a skill you teach. Do you address it?", "question_type": "choice",
     "options": ["Post a nuanced take immediately", "Wait and see how it develops", "Actively test it and share findings", "Ignore it"], "scenario_type": "trending_post_reaction"},
    {"id": "q2_15", "stage": 2, "question_text": "Your post accidentally contains incorrect technical information. What do you do?", "question_type": "choice",
     "options": ["Delete and repost corrected version", "Edit with a correction note", "Reply with correction in comments", "Leave it — minor error"], "scenario_type": "controversy_response_test"},
    {"id": "q2_16", "stage": 2, "question_text": "A brand partnership opportunity requires you to endorse a tool you don't fully believe in. Do you take it?", "question_type": "choice",
     "options": ["Never — authenticity first", "Only if I can be honest about limitations", "Yes if the money is right", "I'd propose a modified deal"], "scenario_type": "controversy_response_test"},
    {"id": "q2_17", "stage": 2, "question_text": "An industry event is happening and everyone's posting about it. You can't attend. What do you do?", "question_type": "choice",
     "options": ["Post my own commentary remotely", "Share curated highlights from others", "Skip it — FOMO posting is weak", "Use it to start a broader conversation"], "scenario_type": "trending_post_reaction"},
    {"id": "q2_18", "stage": 2, "question_text": "Someone copies your exact post format and it outperforms yours. Reaction?", "question_type": "open", "scenario_type": "controversy_response_test"},
    {"id": "q2_19", "stage": 2, "question_text": "A 'day in my life' trend is viral on Instagram. Would you make one?", "question_type": "choice",
     "options": ["Yes — people love behind-the-scenes", "Only if it's authentic, not staged", "No — feels performative", "I'd do a twist on it"], "scenario_type": "meme_adaptation_test"},
    {"id": "q2_20", "stage": 2, "question_text": "You ship a feature at 2AM that prevents a major security breach. Do you post about it?", "question_type": "choice",
     "options": ["Immediately — it's a great story", "Next morning, well-crafted", "Yes but without specifics", "No — security work stays quiet"], "scenario_type": "trending_post_reaction"},
    {"id": "q2_21", "stage": 2, "question_text": "A follower publicly criticizes your code quality. How do you handle it?", "question_type": "open", "scenario_type": "comment_reply_test"},
    {"id": "q2_22", "stage": 2, "question_text": "A tech podcast invites you to talk about a topic you know moderately well. Do you accept?", "question_type": "choice",
     "options": ["Yes — I'll study up", "Only if I can redirect to my expertise", "Decline — I only speak on what I know deeply", "Accept and be transparent about my level"], "scenario_type": "trending_post_reaction"},
    {"id": "q2_23", "stage": 2, "question_text": "You made $10K in a month from your side project. Do you share the number?", "question_type": "choice",
     "options": ["Yes, transparently", "Share the milestone but not the number", "Only on close-network platforms", "Never share revenue publicly"], "scenario_type": "controversy_response_test"},
    {"id": "q2_24", "stage": 2, "question_text": "A 'rate my setup' trend is everywhere. Would you participate?", "question_type": "choice",
     "options": ["Yes, my setup is worth showing", "Only if I add a useful insight", "No — too superficial", "I'd twist it into content about productivity"], "scenario_type": "meme_adaptation_test"},
    {"id": "q2_25", "stage": 2, "question_text": "Your mentor publicly disagrees with your approach. How do you handle it?", "question_type": "open", "scenario_type": "controversy_response_test"},
    {"id": "q2_26", "stage": 2, "question_text": "An old tweet/post resurfaces that doesn't reflect your current views. What do you do?", "question_type": "choice",
     "options": ["Delete it quietly", "Address it publicly — growth is the story", "Ignore unless it becomes an issue", "Pin a correction"], "scenario_type": "controversy_response_test"},
    {"id": "q2_27", "stage": 2, "question_text": "You see someone spreading misinformation about your product. What's your move?", "question_type": "choice",
     "options": ["Correct them publicly with facts", "DM them first", "Have a team member respond", "Ignore — don't feed trolls"], "scenario_type": "comment_reply_test"},
    {"id": "q2_28", "stage": 2, "question_text": "A Nigerian tech community is celebrating a milestone. Do you join the conversation?", "question_type": "choice",
     "options": ["Enthusiastically — it's my community", "Supportively but briefly", "Only if I have something unique to add", "I'd rather not pile on"], "scenario_type": "trending_post_reaction"},
    {"id": "q2_29", "stage": 2, "question_text": "You just failed a product hunt launch. What do you post?", "question_type": "open", "scenario_type": "trending_post_reaction"},
    {"id": "q2_30", "stage": 2, "question_text": "A journalist asks to feature your product but wants you to exaggerate user count. What do you do?", "question_type": "choice",
     "options": ["Decline the feature", "Participate but with honest numbers", "Negotiate a different angle", "Walk away entirely"], "scenario_type": "controversy_response_test"},

    # ════════════════════════════════════════════════════════
    # STAGE 3: Tone Deep-Dive (30 questions)
    # ════════════════════════════════════════════════════════
    {"id": "q3_01", "stage": 3, "question_text": "How do you handle negative/critical comments on your posts?", "question_type": "choice",
     "options": ["Ignore them", "Address the technical point calmly", "Defend my approach passionately", "Delete them"]},
    {"id": "q3_02", "stage": 3, "question_text": "How do you respond to praise?", "question_type": "open"},
    {"id": "q3_03", "stage": 3, "question_text": "What punctuation marks do you overuse?", "question_type": "choice",
     "options": ["Em dashes —", "Ellipses...", "Exclamation marks!", "Periods. Short. Sentences.", "Parentheses (like this)", "None in particular"]},
    {"id": "q3_04", "stage": 3, "question_text": "When you write a hook, do you prefer questions or statements?", "question_type": "choice",
     "options": ["Questions that provoke", "Bold statements", "Contradictions", "Stories that pull in", "Data/numbers"]},
    {"id": "q3_05", "stage": 3, "question_text": "How do you end your posts?", "question_type": "choice",
     "options": ["Strong CTA (follow, share)", "Open question for discussion", "One-liner summary", "No formal ending — just stop", "Subtle nudge"]},
    {"id": "q3_06", "stage": 3, "question_text": "Pick the LinkedIn opening that sounds most like you:", "question_type": "choice",
     "options": [
         "I shipped a feature at 2AM that prevented a security breach. Here's why.",
         "Most developers don't realize their deployment pipeline is a ticking time bomb.",
         "Yesterday I got an email that changed how I think about API security.",
         "Hot take: You don't need Kubernetes. You never did."
     ]},
    {"id": "q3_07", "stage": 3, "question_text": "How do you use hashtags?", "question_type": "choice",
     "options": ["Never", "1-3 relevant ones", "5-10 for reach", "Only on Instagram", "Platform-dependent"]},
    {"id": "q3_08", "stage": 3, "question_text": "How verbose are your IG captions? (1=minimal, 10=essay)", "question_type": "scale", "min_value": 1, "max_value": 10},
    {"id": "q3_09", "stage": 3, "question_text": "Which CTA style fits you best?", "question_type": "choice",
     "options": ["Direct: 'Follow for more'", "Subtle: 'Thoughts?'", "Value-add: 'Save this for later'", "None — CTAs feel fake to me"]},
    {"id": "q3_10", "stage": 3, "question_text": "How do you reference other people in posts?", "question_type": "choice",
     "options": ["By name with @mention", "Vaguely — 'a friend told me'", "Never reference others", "Only mention mutual connections"]},
    {"id": "q3_11", "stage": 3, "question_text": "Do you use first person or third person when talking about your brand?", "question_type": "choice",
     "options": ["Always 'I' and 'me'", "Mix of 'I' and 'we'", "Always 'we' (team voice)", "Depends on platform"]},
    {"id": "q3_12", "stage": 3, "question_text": "How do you handle technical jargon?", "question_type": "choice",
     "options": ["Use it freely — my audience gets it", "Explain briefly when I use it", "Avoid it — accessibility first", "Platform-dependent"]},
    {"id": "q3_13", "stage": 3, "question_text": "Do you use numbered lists in your posts?", "question_type": "choice",
     "options": ["Frequently — they perform well", "Sometimes for structure", "Rarely", "Never — too formulaic"]},
    {"id": "q3_14", "stage": 3, "question_text": "How long should your ideal LinkedIn post be?", "question_type": "choice",
     "options": ["Short (under 200 chars)", "Medium (200-500 chars)", "Long (500-1000 chars)", "Very long (1000+ chars)"]},
    {"id": "q3_15", "stage": 3, "question_text": "When you share a lesson, do you frame it as advice or experience?", "question_type": "choice",
     "options": ["Direct advice: 'Do this, not that'", "Experience: 'Here's what happened to me'", "Question: 'Have you noticed this?'", "Mix depending on topic"]},
    {"id": "q3_16", "stage": 3, "question_text": "How do you feel about using 'thread' or 'carousel' format for long content?", "question_type": "choice",
     "options": ["Love them — great for deep dives", "Use them selectively", "Prefer single posts", "Only for Instagram"]},
    {"id": "q3_17", "stage": 3, "question_text": "Do you use line breaks to create whitespace in posts?", "question_type": "choice",
     "options": ["Yes — every sentence gets its own line", "Moderate — paragraph breaks only", "Minimal — dense text is fine", "Platform-dependent"]},
    {"id": "q3_18", "stage": 3, "question_text": "How do you transition between ideas in a post?", "question_type": "choice",
     "options": ["Smooth connectors (however, therefore)", "Abrupt jumps (new line, new thought)", "Numbered steps", "Storytelling flow"]},
    {"id": "q3_19", "stage": 3, "question_text": "Pick the IG caption that sounds most like you:", "question_type": "choice",
     "options": [
         "built this in 3 hours. sometimes the best code is the code you don't write 🔥",
         "New project update! We've been working hard on this feature and I'm excited to share it with you all.",
         "The gap between 'almost done' and 'shipped' is where most dreams go to die.",
         "Day 47 of building in public. Today's lesson: databases lie."
     ]},
    {"id": "q3_20", "stage": 3, "question_text": "Do you use metaphors or analogies?", "question_type": "choice",
     "options": ["Frequently — they're powerful", "Occasionally when they fit", "Rarely", "Never — I'm direct"]},
    {"id": "q3_21", "stage": 3, "question_text": "How vulnerable are you willing to be in your content?", "question_type": "scale", "min_value": 1, "max_value": 10},
    {"id": "q3_22", "stage": 3, "question_text": "Do you capitalize words for emphasis? (e.g., 'This is NOT okay')", "question_type": "choice",
     "options": ["Yes, for emphasis", "Rarely", "Never — it feels like shouting"]},
    {"id": "q3_23", "stage": 3, "question_text": "How do you handle statistics/data in posts?", "question_type": "choice",
     "options": ["Lead with data — 'According to X...'", "Sprinkle data to support stories", "Rarely use data", "Only real data I've collected"]},
    {"id": "q3_24", "stage": 3, "question_text": "What's your preferred Facebook tone vs other platforms?", "question_type": "open"},
    {"id": "q3_25", "stage": 3, "question_text": "How do you typically open Instagram Brand posts?", "question_type": "open"},
    {"id": "q3_26", "stage": 3, "question_text": "Would you ever post something controversial just for engagement?", "question_type": "choice",
     "options": ["Never", "Only if I genuinely believe it", "Occasionally — engagement matters", "Yes — it's part of the game"]},
    {"id": "q3_27", "stage": 3, "question_text": "How do you handle trending topics outside your niche?", "question_type": "choice",
     "options": ["Ignore completely", "Connect to my niche if possible", "Occasionally comment", "Jump in if interested"]},
    {"id": "q3_28", "stage": 3, "question_text": "Do you use quotes from others to start posts?", "question_type": "choice",
     "options": ["Frequently", "Sometimes", "Rarely", "Never"]},
    {"id": "q3_29", "stage": 3, "question_text": "What's your formatting style for Instagram Brand vs Personal?", "question_type": "open"},
    {"id": "q3_30", "stage": 3, "question_text": "If you had to summarize your 'voice' in 3 words, what would they be?", "question_type": "open"},

    # ════════════════════════════════════════════════════════
    # STAGE 4: Content Boundaries (15 questions — unlocks at 2 weeks)
    # ════════════════════════════════════════════════════════
    {"id": "q4_01", "stage": 4, "question_text": "What is a topic you will NEVER post about?", "question_type": "open"},
    {"id": "q4_02", "stage": 4, "question_text": "What makes your Instagram Brand content different from your Personal Instagram?", "question_type": "open"},
    {"id": "q4_03", "stage": 4, "question_text": "Would you ever post about politics on any platform?", "question_type": "choice",
     "options": ["Never", "Only if it directly affects my industry", "On personal accounts only", "Yes — it's part of who I am"]},
    {"id": "q4_04", "stage": 4, "question_text": "How do you handle religious content?", "question_type": "choice",
     "options": ["Never mention religion", "Acknowledge holidays naturally", "It's part of my identity — I share openly", "Only privately"]},
    {"id": "q4_05", "stage": 4, "question_text": "Would you share personal health or mental health struggles?", "question_type": "choice",
     "options": ["Yes — it's authentic", "Only retrospectively", "Never publicly", "Only if it helps others"]},
    {"id": "q4_06", "stage": 4, "question_text": "How do you handle competitors' products in your content?", "question_type": "choice",
     "options": ["Never mention them", "Acknowledge respectfully", "Compare openly", "Only praise, never criticize"]},
    {"id": "q4_07", "stage": 4, "question_text": "What topics generate backlash you'd rather avoid?", "question_type": "open"},
    {"id": "q4_08", "stage": 4, "question_text": "Would you post about financial struggles or revenue dips?", "question_type": "choice",
     "options": ["Yes — transparency builds trust", "Only after recovery", "Never — it's bad for brand", "Only on Lin kedin"]},
    {"id": "q4_09", "stage": 4, "question_text": "Are there any products or services you'd never promote?", "question_type": "open"},
    {"id": "q4_10", "stage": 4, "question_text": "How close to launch day would you tease a new product?", "question_type": "choice",
     "options": ["Months in advance", "2-3 weeks", "1 week", "Day of", "I don't tease — I just launch"]},
    {"id": "q4_11", "stage": 4, "question_text": "Would you reshare user-generated content?", "question_type": "choice",
     "options": ["Always — it's great social proof", "Selectively", "Only on Instagram", "Rarely"]},
    {"id": "q4_12", "stage": 4, "question_text": "How do you represent team members in your content?", "question_type": "choice",
     "options": ["By name and role", "Anonymously as 'the team'", "Only key leaders", "I'm a solo operation"]},
    {"id": "q4_13", "stage": 4, "question_text": "What's the maximum number of CTAs you'd put in a single post?", "question_type": "choice",
     "options": ["0", "1", "2", "3+"]},
    {"id": "q4_14", "stage": 4, "question_text": "Would you ever use paid promotion/boosting on your posts?", "question_type": "choice",
     "options": ["Yes — it's smart marketing", "Only for major launches", "Never — organic only", "Considering it"]},
    {"id": "q4_15", "stage": 4, "question_text": "How do you feel about crossposting the same content across platforms?", "question_type": "choice",
     "options": ["Same post everywhere", "Adapted for each platform", "Unique content per platform", "Core idea same, format different"]},

    # ════════════════════════════════════════════════════════
    # STAGE 5: Audience Empathy (15 questions — unlocks after 20 posts)
    # ════════════════════════════════════════════════════════
    {"id": "q5_01", "stage": 5, "question_text": "What's the #1 question your audience asks you repeatedly?", "question_type": "open"},
    {"id": "q5_02", "stage": 5, "question_text": "What's the misconception your audience has about your field?", "question_type": "open"},
    {"id": "q5_03", "stage": 5, "question_text": "What keeps your audience up at night professionally?", "question_type": "open"},
    {"id": "q5_04", "stage": 5, "question_text": "What's the aspiration your audience has that you understand deeply?", "question_type": "open"},
    {"id": "q5_05", "stage": 5, "question_text": "What language/phrases does your audience use that outsiders don't?", "question_type": "open"},
    {"id": "q5_06", "stage": 5, "question_text": "When your audience succeeds, what does that look like?", "question_type": "open"},
    {"id": "q5_07", "stage": 5, "question_text": "When your audience fails, what's the typical reason?", "question_type": "open"},
    {"id": "q5_08", "stage": 5, "question_text": "What's the biggest lie your audience has been told about your industry?", "question_type": "open"},
    {"id": "q5_09", "stage": 5, "question_text": "What sub-segment of your audience engages most?", "question_type": "open"},
    {"id": "q5_10", "stage": 5, "question_text": "What type of content makes your audience save (not just like)?", "question_type": "open"},
    {"id": "q5_11", "stage": 5, "question_text": "What type of content makes your audience share?", "question_type": "open"},
    {"id": "q5_12", "stage": 5, "question_text": "What frustrates your audience about typical 'advice' content in your space?", "question_type": "open"},
    {"id": "q5_13", "stage": 5, "question_text": "How does your audience discover you? (platform-specific)", "question_type": "open"},
    {"id": "q5_14", "stage": 5, "question_text": "What value do you provide that no one else in your niche does?", "question_type": "open"},
    {"id": "q5_15", "stage": 5, "question_text": "Based on your recent posts, which content pillar resonated most?", "question_type": "open"},

    # ════════════════════════════════════════════════════════
    # STAGE 6: Engagement Style (10 questions — unlocks after 50 posts)
    # ════════════════════════════════════════════════════════
    {"id": "q6_01", "stage": 6, "question_text": "How quickly do you typically reply to comments?", "question_type": "choice",
     "options": ["Within minutes", "Within hours", "Within a day", "When I get around to it"]},
    {"id": "q6_02", "stage": 6, "question_text": "Do you initiate conversations on other people's posts?", "question_type": "choice",
     "options": ["Frequently — I'm active in the community", "Sometimes", "Rarely", "Only on people I know"]},
    {"id": "q6_03", "stage": 6, "question_text": "How do you handle DMs from strangers?", "question_type": "choice",
     "options": ["Reply to everyone", "Reply selectively", "Ignore most", "Auto-reply with a link"]},
    {"id": "q6_04", "stage": 6, "question_text": "Do you tag people in your posts?", "question_type": "choice",
     "options": ["Frequently — it builds relationships", "Only when relevant", "Rarely", "Never"]},
    {"id": "q6_05", "stage": 6, "question_text": "What automation level do you want for LinkedIn replies?", "question_type": "choice",
     "options": ["Full auto — trust the system", "Semi-auto — I approve each reply", "Manual — I write my own"]},
    {"id": "q6_06", "stage": 6, "question_text": "What automation level do you want for Instagram Personal replies?", "question_type": "choice",
     "options": ["Full auto", "Semi-auto", "Manual"]},
    {"id": "q6_07", "stage": 6, "question_text": "What automation level do you want for Instagram Brand replies?", "question_type": "choice",
     "options": ["Full auto", "Semi-auto", "Manual"]},
    {"id": "q6_08", "stage": 6, "question_text": "What automation level do you want for Facebook replies?", "question_type": "choice",
     "options": ["Full auto", "Semi-auto", "Manual"]},
    {"id": "q6_09", "stage": 6, "question_text": "Do you follow back people who follow you?", "question_type": "choice",
     "options": ["Always", "If they're in my niche", "Selectively", "Never"]},
    {"id": "q6_10", "stage": 6, "question_text": "How do you handle debate or disagreement in comments?", "question_type": "choice",
     "options": ["Engage deeply — I love discourse", "One thoughtful reply then move on", "Acknowledge and redirect", "Ignore unless it's factual"]},
]


def get_questions_for_stage(stage: int) -> list:
    """Get all questions for a specific stage."""
    return [q for q in QUESTIONS if q["stage"] == stage]


def get_all_questions() -> list:
    """Get the entire question bank."""
    return QUESTIONS


def get_stage_info() -> dict:
    """Get summary info about each stage."""
    stages = {}
    for q in QUESTIONS:
        s = q["stage"]
        if s not in stages:
            stages[s] = {"count": 0, "types": set()}
        stages[s]["count"] += 1
        stages[s]["types"].add(q["question_type"])

    return {
        1: {"name": "Core Identity & Voice", "count": stages.get(1, {}).get("count", 0), "unlock": "immediate"},
        2: {"name": "Simulation Scenarios", "count": stages.get(2, {}).get("count", 0), "unlock": "immediate"},
        3: {"name": "Tone Deep-Dive", "count": stages.get(3, {}).get("count", 0), "unlock": "immediate"},
        4: {"name": "Content Boundaries", "count": stages.get(4, {}).get("count", 0), "unlock": "after 2 weeks"},
        5: {"name": "Audience Empathy", "count": stages.get(5, {}).get("count", 0), "unlock": "after 20 posts"},
        6: {"name": "Engagement Style", "count": stages.get(6, {}).get("count", 0), "unlock": "after 50 posts"},
    }


def get_total_question_count() -> int:
    """Get total number of questions in the bank."""
    return len(QUESTIONS)
