"""
Reply Templates — Cost-saving comment reply system.
Classifies incoming comments by intent and uses keyword-matched templates
before falling back to AI-generated replies.
"""

import random
from backend.logger import get_logger

logger = get_logger("reply_manager.templates")


# Comment classification categories
class CommentIntent:
    QUESTION = "question"
    COMPLIMENT = "compliment"
    AGREEMENT = "agreement"
    DISAGREEMENT = "disagreement"
    SHARE_EXPERIENCE = "share_experience"
    REQUEST = "request"
    SPAM = "spam"
    GENERAL = "general"


# Keyword-based classification rules (free, no API cost)
CLASSIFICATION_RULES = {
    CommentIntent.QUESTION: [
        "how do", "how can", "what is", "what are", "why", "when",
        "could you", "can you", "do you know", "is there", "?",
        "any tips", "any advice", "recommend", "suggest",
    ],
    CommentIntent.COMPLIMENT: [
        "great post", "love this", "amazing", "awesome", "well said",
        "exactly", "brilliant", "spot on", "this is gold", "bookmark",
        "saved", "needed this", "thank you", "thanks for sharing",
        "insightful", "powerful", "inspiring",
    ],
    CommentIntent.AGREEMENT: [
        "agree", "so true", "100%", "facts", "this", "yes",
        "same here", "absolutely", "couldn't agree more", "preach",
    ],
    CommentIntent.DISAGREEMENT: [
        "disagree", "I think differently", "but", "however",
        "not sure about", "counter", "actually", "that's not",
        "wrong", "incorrect",
    ],
    CommentIntent.SHARE_EXPERIENCE: [
        "I had similar", "in my experience", "we did this",
        "at my company", "I tried", "I built", "I shipped",
        "working on", "building", "launching",
    ],
    CommentIntent.SPAM: [
        "follow me", "check my profile", "dm me", "make money",
        "free", "click link", "visit my", "follow back",
        "crypto", "forex", "💰", "🔥 dm",
    ],
}


# Platform-specific reply templates
TEMPLATES = {
    "linkedin": {
        CommentIntent.QUESTION: [
            "Great question! {short_answer} — happy to go deeper if you want to DM about it.",
            "Appreciate the question. {short_answer}. Been thinking about this a lot lately.",
            "{short_answer} — would love to hear how you're approaching it on your end.",
        ],
        CommentIntent.COMPLIMENT: [
            "Appreciate that 🙏 means a lot coming from someone building in this space.",
            "Thank you! Glad this resonated. The real story is always messier than the post 😅",
            "Thanks for the kind words — genuinely motivating to keep sharing these.",
        ],
        CommentIntent.AGREEMENT: [
            "Glad we see it the same way. Have you run into this in your own work?",
            "Right? It's one of those things you don't realize until you're deep in it.",
        ],
        CommentIntent.DISAGREEMENT: [
            "Love the pushback — you might be right. What's been your experience with this?",
            "Fair point. I'd be curious to hear more about your perspective on this.",
            "That's a valid counter. The nuance here is tricky — appreciate you raising it.",
        ],
        CommentIntent.SHARE_EXPERIENCE: [
            "That's a great real-world example — thanks for sharing! How did it turn out?",
            "Love hearing this. The builder perspective is always more valuable than theory.",
        ],
    },
    "instagram_personal": {
        CommentIntent.QUESTION: [
            "Good one! {short_answer} — DM if you want the full breakdown 🤙",
            "{short_answer} 💡 been working through this myself",
        ],
        CommentIntent.COMPLIMENT: [
            "🙏🙏 appreciate you",
            "means a lot fr! glad it hit 💪",
            "thank you! more coming 🔥",
        ],
        CommentIntent.AGREEMENT: [
            "right?? 💯",
            "we move 🤝",
        ],
        CommentIntent.SHARE_EXPERIENCE: [
            "love that you're building too 🔥 what stack?",
            "that's fire 💪 how far along are you?",
        ],
    },
    "instagram_brand": {
        CommentIntent.QUESTION: [
            "Great question! {short_answer} — check our docs for more details 📚",
            "{short_answer} — DM us if you need help getting started!",
        ],
        CommentIntent.COMPLIMENT: [
            "Thank you! We're building something special 🚀",
            "Appreciate the support! Stay tuned for more updates 💪",
        ],
    },
    "facebook": {
        CommentIntent.QUESTION: [
            "Thanks for asking! {short_answer}",
            "{short_answer} — happy to discuss more in DMs.",
        ],
        CommentIntent.COMPLIMENT: [
            "Thank you! Glad this was useful 🙏",
            "Appreciate that! More content like this coming.",
        ],
    },
}


class ReplyTemplateManager:
    """
    Manages comment classification and template-based reply generation.
    Uses keyword matching first (free), falls back to AI for complex comments.
    """

    def classify_comment(self, comment_text: str) -> str:
        """
        Classify a comment by intent using keyword matching.

        Args:
            comment_text: the comment to classify

        Returns:
            CommentIntent string
        """
        text_lower = comment_text.lower().strip()

        # Check each classification category
        scores = {}
        for intent, keywords in CLASSIFICATION_RULES.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[intent] = score

        if not scores:
            return CommentIntent.GENERAL

        # Spam check first (highest priority)
        if CommentIntent.SPAM in scores:
            return CommentIntent.SPAM

        # Return highest scoring intent
        return max(scores, key=scores.get)

    def get_template_reply(
        self,
        comment_text: str,
        platform: str = "linkedin",
        short_answer: str = "",
    ) -> dict:
        """
        Get a template-based reply for a comment.

        Args:
            comment_text: the comment to reply to
            platform: target platform for voice matching
            short_answer: brief answer to inject into question templates

        Returns:
            dict with intent, reply_text, needs_ai (bool), is_spam (bool)
        """
        intent = self.classify_comment(comment_text)

        if intent == CommentIntent.SPAM:
            return {
                "intent": intent,
                "reply_text": "",
                "needs_ai": False,
                "is_spam": True,
                "action": "ignore",
            }

        platform_templates = TEMPLATES.get(platform, TEMPLATES.get("linkedin", {}))
        intent_templates = platform_templates.get(intent, [])

        if not intent_templates:
            # No template for this intent/platform — needs AI
            return {
                "intent": intent,
                "reply_text": "",
                "needs_ai": True,
                "is_spam": False,
                "action": "ai_draft",
            }

        template = random.choice(intent_templates)
        reply_text = template.format(short_answer=short_answer or "Let me think on that")

        return {
            "intent": intent,
            "reply_text": reply_text,
            "needs_ai": False,
            "is_spam": False,
            "action": "send",
        }

    def batch_classify(self, comments: list) -> dict:
        """
        Classify a batch of comments and return summary.

        Args:
            comments: list of comment texts

        Returns:
            dict with per-intent counts and spam count
        """
        results = {}
        spam_count = 0
        for comment in comments:
            intent = self.classify_comment(comment)
            if intent == CommentIntent.SPAM:
                spam_count += 1
            results[intent] = results.get(intent, 0) + 1

        return {
            "total": len(comments),
            "spam": spam_count,
            "needs_reply": len(comments) - spam_count,
            "breakdown": results,
        }
