"""Transparent visibility scoring heuristics.

Important:
This is a transparent heuristic measurement for AEO/SEO/GEO tracking,
not an internal ranking algorithm.
Missing evidence or unavailable states do not penalize scores with false negatives.
"""

from typing import Any, Optional, Union

from app.schemas.common import CitationStatus, CollectionStatus, MentionStatus
from app.schemas.observations import ObservationBase, ObservationCreate


def calculate_visibility_score(
    item: Union[ObservationCreate, ObservationBase, Any],
) -> Optional[int]:
    """Calculate a 0-100 visibility score based on explicit observations.

    Returns None if collection failed, was cancelled, or contains insufficient evidence.
    """
    collection_status = (
        item.collection_status.value
        if hasattr(item.collection_status, "value")
        else str(item.collection_status)
    )
    if collection_status not in (CollectionStatus.SUCCESS.value, "success"):
        return None

    # Base points
    score = 0
    has_evaluated_data = False

    # 1. Search Engine Rank (up to 40 pts)
    if item.rank_position is not None:
        has_evaluated_data = True
        pos = item.rank_position
        if 1 <= pos <= 3:
            score += 40
        elif 4 <= pos <= 10:
            score += max(10, 40 - (pos - 1) * 3)
        elif 11 <= pos <= 20:
            score += 5

    # 2. Featured snippet / Answer box (20 pts)
    if item.answer_box_present is True:
        has_evaluated_data = True
        score += 20
    elif item.answer_box_present is False:
        has_evaluated_data = True

    # 3. IncuBrix Brand Mention (20 pts)
    mention_val = (
        item.incubrix_mentioned.value
        if hasattr(item.incubrix_mentioned, "value")
        else str(item.incubrix_mentioned)
    )
    if mention_val == MentionStatus.MENTIONED.value:
        has_evaluated_data = True
        score += 20
    elif mention_val == MentionStatus.NOT_MENTIONED.value:
        has_evaluated_data = True

    # 4. IncuBrix Direct Citation / Link (20 pts)
    citation_val = (
        item.incubrix_cited.value
        if hasattr(item.incubrix_cited, "value")
        else str(item.incubrix_cited)
    )
    if citation_val == CitationStatus.CITED.value:
        has_evaluated_data = True
        score += 20
    elif citation_val == CitationStatus.NOT_CITED.value:
        has_evaluated_data = True

    if not has_evaluated_data:
        return None

    return min(100, max(0, score))
