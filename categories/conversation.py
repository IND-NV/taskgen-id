"""Kategori percakapan dan bantuan interpersonal TaskGen-ID."""

CATEGORY = {
    "id": "conversation",
    "name": "Conversation",
    "domains": [
        {"name": "Debate", "subdomains": ["formal", "casual", "philosophical", "scientific", "political", "ethical"]},
        {"name": "Advice", "subdomains": ["career", "relationship", "academic", "financial", "health", "technical"]},
        {"name": "Interview", "subdomains": ["job", "podcast", "journalistic", "research", "behavioral", "technical_interview"]},
        {"name": "Teaching", "subdomains": ["socratic", "mentoring", "tutoring", "lecture_qa", "feedback", "study_guidance"]},
        {"name": "Roleplay", "subdomains": ["historical_figure", "professional", "customer_service", "therapy", "negotiation", "collaborative"]},
    ],
}
