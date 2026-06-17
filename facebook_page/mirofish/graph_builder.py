"""
MiroFish Graph Builder — Agent A Module

Takes seed documents → runs entity + relationship extraction.
Extracts: companies, people, events, concepts, trends.
Maps relationships between entities.
Detects community clusters.
Output: structured knowledge graph JSON.
"""

import re
import json
from dataclasses import dataclass, field, asdict


@dataclass
class Entity:
    name: str
    type: str  # company, person, event, concept, trend
    relevance_score: float = 0.0
    mentions: int = 1


@dataclass  
class Relationship:
    source_entity: str
    target_entity: str
    relationship_type: str  # mentions, related_to, caused, contradicts, etc.
    weight: float = 1.0


@dataclass
class Community:
    name: str
    entities: list = field(default_factory=list)
    theme: str = ""


@dataclass
class KnowledgeGraph:
    entities: list = field(default_factory=list)
    relationships: list = field(default_factory=list)
    communities: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "entities": [asdict(e) for e in self.entities],
            "relationships": [asdict(r) for r in self.relationships],
            "communities": [asdict(c) for c in self.communities],
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# Entity extraction patterns
COMPANY_PATTERNS = [
    r'\b(OpenAI|Google|Meta|Microsoft|Apple|Amazon|Paystack|Flutterwave|Stripe|Shopify|Vercel|Netlify|GitHub|GitLab|Railway|Supabase|Firebase|AWS|Azure|Anthropic|Mistral|Hugging\s*Face)\b',
    r'\b([A-Z][a-z]+(?:\.(?:ai|io|co|com)))\b',
]

PERSON_PATTERNS = [
    r'\b(Elon Musk|Sam Altman|Mark Zuckerberg|Satya Nadella|Jensen Huang|Andrej Karpathy)\b',
    r'\b(CEO|founder|CTO|creator)\s+(?:of\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
]

EVENT_PATTERNS = [
    r'\b(launched?|released?|announced?|acquired?|raised?\s+\$[\d.]+[MBK]?|IPO|merger|partnership|breach|outage|hack)\b',
]

CONCEPT_KEYWORDS = [
    "artificial intelligence", "machine learning", "deep learning", "neural network",
    "large language model", "LLM", "API", "microservice", "serverless",
    "blockchain", "cryptocurrency", "web3", "devops", "CI/CD",
    "open source", "SaaS", "fintech", "edtech", "healthtech",
    "automation", "no-code", "low-code", "cloud computing",
]

TREND_KEYWORDS = [
    "trending", "viral", "rising", "growing", "emerging",
    "hot topic", "breaking", "new release", "just launched",
]


def _extract_entities(seed_docs: list) -> list:
    """Extract entities from seed documents."""
    entity_map = {}  # name -> Entity
    
    for doc in seed_docs:
        text = f"{doc.title} {doc.content}" if hasattr(doc, 'title') else str(doc.get("title", "")) + " " + str(doc.get("content", ""))
        
        # Extract companies
        for pattern in COMPANY_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.strip() if isinstance(match, str) else match[0].strip()
                if len(name) > 2:
                    key = name.lower()
                    if key in entity_map:
                        entity_map[key].mentions += 1
                        entity_map[key].relevance_score = min(1.0, entity_map[key].relevance_score + 0.1)
                    else:
                        entity_map[key] = Entity(
                            name=name, type="company",
                            relevance_score=0.3, mentions=1
                        )
        
        # Extract events
        for pattern in EVENT_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Create event entity from context
                event_name = match.strip()
                # Try to get surrounding context
                idx = text.lower().find(event_name.lower())
                if idx >= 0:
                    start = max(0, idx - 30)
                    end = min(len(text), idx + len(event_name) + 30)
                    context = text[start:end].strip()
                    key = f"event_{event_name.lower()}"
                    if key not in entity_map:
                        entity_map[key] = Entity(
                            name=context[:60], type="event",
                            relevance_score=0.4, mentions=1
                        )
        
        # Extract concepts
        text_lower = text.lower()
        for concept in CONCEPT_KEYWORDS:
            if concept.lower() in text_lower:
                key = concept.lower()
                if key in entity_map:
                    entity_map[key].mentions += 1
                    entity_map[key].relevance_score = min(1.0, entity_map[key].relevance_score + 0.1)
                else:
                    entity_map[key] = Entity(
                        name=concept, type="concept",
                        relevance_score=0.3, mentions=1
                    )
        
        # Extract trends
        for trend_kw in TREND_KEYWORDS:
            if trend_kw.lower() in text_lower:
                # The surrounding content is the trend
                idx = text_lower.find(trend_kw.lower())
                start = max(0, idx - 10)
                end = min(len(text), idx + len(trend_kw) + 40)
                trend_text = text[start:end].strip()
                key = f"trend_{trend_text[:30].lower()}"
                if key not in entity_map:
                    entity_map[key] = Entity(
                        name=trend_text[:60], type="trend",
                        relevance_score=0.5, mentions=1
                    )
    
    return list(entity_map.values())


def _extract_relationships(entities: list, seed_docs: list) -> list:
    """Extract relationships between entities."""
    relationships = []
    entity_names = {e.name.lower(): e for e in entities}
    
    for doc in seed_docs:
        text = f"{doc.title} {doc.content}" if hasattr(doc, 'title') else str(doc.get("title", "")) + " " + str(doc.get("content", ""))
        text_lower = text.lower()
        
        # Find co-occurring entities in the same document
        present_entities = []
        for name, entity in entity_names.items():
            if name in text_lower:
                present_entities.append(entity)
        
        # Create relationships between co-occurring entities
        for i, e1 in enumerate(present_entities):
            for e2 in present_entities[i+1:]:
                # Determine relationship type based on entity types
                if e1.type == "company" and e2.type == "concept":
                    rel_type = "works_with"
                elif e1.type == "event" and e2.type == "company":
                    rel_type = "involves"
                elif e1.type == "concept" and e2.type == "concept":
                    rel_type = "related_to"
                else:
                    rel_type = "co_mentioned"
                
                relationships.append(Relationship(
                    source_entity=e1.name,
                    target_entity=e2.name,
                    relationship_type=rel_type,
                ))
    
    # Deduplicate
    seen = set()
    unique_rels = []
    for r in relationships:
        key = (r.source_entity.lower(), r.target_entity.lower(), r.relationship_type)
        if key not in seen:
            seen.add(key)
            unique_rels.append(r)
    
    return unique_rels


def _detect_communities(entities: list, relationships: list) -> list:
    """Detect community clusters from entity relationships."""
    # Simple clustering: group entities by type and relationship proximity
    type_groups = {}
    for entity in entities:
        if entity.type not in type_groups:
            type_groups[entity.type] = []
        type_groups[entity.type].append(entity.name)
    
    communities = []
    
    # Create communities from type groups
    theme_map = {
        "company": "Industry players",
        "concept": "Technical concepts",
        "trend": "Emerging trends",
        "event": "Recent events",
        "person": "Key people",
    }
    
    for etype, names in type_groups.items():
        if names:
            communities.append(Community(
                name=f"{theme_map.get(etype, etype)} cluster",
                entities=names[:10],
                theme=theme_map.get(etype, etype),
            ))
    
    # Create cross-type community from highly connected entities
    connected = set()
    for r in relationships:
        connected.add(r.source_entity)
        connected.add(r.target_entity)
    
    if connected:
        communities.append(Community(
            name="Interconnected topics",
            entities=list(connected)[:10],
            theme="Cross-domain connections",
        ))
    
    return communities


def build_graph(seed_docs: list) -> KnowledgeGraph:
    """
    Build knowledge graph from seed documents.
    
    Args:
        seed_docs: list of SeedDocument objects or dicts with title/content/source/timestamp
        
    Returns:
        KnowledgeGraph with entities, relationships, and communities
    """
    if not seed_docs:
        return KnowledgeGraph()
    
    entities = _extract_entities(seed_docs)
    relationships = _extract_relationships(entities, seed_docs)
    communities = _detect_communities(entities, relationships)
    
    return KnowledgeGraph(
        entities=entities,
        relationships=relationships,
        communities=communities,
    )
