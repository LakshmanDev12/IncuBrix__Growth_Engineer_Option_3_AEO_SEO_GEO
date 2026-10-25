"""Base interfaces and protocols for observation collectors."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.database.models.question import QuestionModel
from app.schemas.observations import ObservationCreate


class BaseCollector(ABC):
    """Abstract base class for all observation collectors."""

    collector_name: str = "base_collector"

    @abstractmethod
    def collect(
        self,
        question: QuestionModel,
        market: Optional[str] = None,
        location: Optional[str] = None,
    ) -> ObservationCreate:
        """Collect visibility data for a given creator question."""
        pass
