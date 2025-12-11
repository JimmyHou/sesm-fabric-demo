from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Literal
from uuid import uuid4
from pydantic import BaseModel


MemoryType = Literal["episodic", "knowledge"]


class MemoryItem(BaseModel):
    id: str
    content: str
    type: MemoryType
    ttl_seconds: Optional[int] = None
    created_at: datetime
    last_mentioned_at: datetime
    mentions: int
    trust: float


class MemoryStore:
    """
    Simple in memory store that behaves like a Redis backed design.
    You can swap this later with a real Redis client while keeping the same API.
    """

    def __init__(self):
        self._items: Dict[str, MemoryItem] = {}

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _recompute_trust(self, mentions: int) -> float:
        # Simple scoring: each mention adds 0.2 trust up to 1.0
        trust = 0.2 * mentions
        return 1.0 if trust > 1.0 else trust

    def _find_by_content(self, content: str) -> Optional[MemoryItem]:
        for item in self._items.values():
            if item.content == content:
                return item
        return None

    def write_event(self, content: str, ttl_seconds: int = 60) -> MemoryItem:
        """
        Write an event into episodic memory.
        If it has been mentioned before within a short window,
        we reinforce it and possibly promote to knowledge.
        """
        now = self._now()
        existing = self._find_by_content(content)

        # New episodic memory
        if existing is None:
            item = MemoryItem(
                id=str(uuid4()),
                content=content,
                type="episodic",
                ttl_seconds=ttl_seconds,
                created_at=now,
                last_mentioned_at=now,
                mentions=1,
                trust=self._recompute_trust(1),
            )
            self._items[item.id] = item
            return item

        # Existing knowledge memory
        if existing.type == "knowledge":
            existing.mentions += 1
            existing.last_mentioned_at = now
            existing.trust = self._recompute_trust(existing.mentions)
            self._items[existing.id] = existing
            return existing

        # Existing episodic memory
        existing.mentions += 1
        existing.last_mentioned_at = now
        existing.trust = self._recompute_trust(existing.mentions)

        # Promotion rule: 2 or more mentions within 120 seconds
        window = now - existing.created_at
        if existing.mentions >= 2 and window <= timedelta(seconds=120):
            existing.type = "knowledge"
            existing.ttl_seconds = None

        self._items[existing.id] = existing
        return existing

    def _is_expired(self, item: MemoryItem) -> bool:
        if item.type != "episodic":
            return False
        if item.ttl_seconds is None:
            return False
        now = self._now()
        age = (now - item.created_at).total_seconds()
        return age > item.ttl_seconds

    def cleanup_expired(self) -> None:
        to_delete = [item_id for item_id, item in self._items.items() if self._is_expired(item)]
        for item_id in to_delete:
            del self._items[item_id]

    def list_episodic(self) -> List[MemoryItem]:
        self.cleanup_expired()
        episodic = [item for item in self._items.values() if item.type == "episodic"]
        episodic.sort(key=lambda x: x.created_at, reverse=True)
        return episodic

    def list_knowledge(self) -> List[MemoryItem]:
        knowledge = [item for item in self._items.values() if item.type == "knowledge"]
        knowledge.sort(key=lambda x: x.trust, reverse=True)
        return knowledge

    def list_all(self) -> List[MemoryItem]:
        self.cleanup_expired()
        items = list(self._items.values())
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items


store = MemoryStore()
