"""
Ranking logic for product candidates.

Implements the heuristic scoring algorithm defined in SolutionDesign.md.
"""

import logging
import math
from models import Requirements, CandidateProduct, RankedProduct
from config import settings

logger = logging.getLogger(__name__)


def rank_candidates(
    requirements: Requirements,
    candidates: list[CandidateProduct]
) -> tuple[RankedProduct | None, list[RankedProduct]]:
    """
    Rank product candidates based on requirements and heuristics.
    
    Scoring formula:
    score = 0.55*similarity + 0.15*normalized_popularity 
            + 0.15*price_affinity + 0.15*availability_factor
    
    Args:
        requirements: Normalized user requirements
        candidates: List of enriched product candidates
        
    Returns:
        Tuple of (primary_recommendation, alternatives_list)
    """
    if not candidates:
        logger.warning("No candidates provided for ranking")
        return None, []
    
    ranked: list[RankedProduct] = []
    
    # Calculate max quantity for normalization
    max_quantity = max((c.quantity_available for c in candidates), default=1)
    
    for candidate in candidates:
        # Apply exclusions first
        excluded_reason = _check_exclusions(candidate, requirements)
        if excluded_reason:
            ranked.append(RankedProduct(
                product_id=candidate.product_id,
                score=0.0,
                excluded_reason=excluded_reason
            ))
            continue
        
        # Calculate score components
        similarity_score = candidate.similarity
        
        # Normalized popularity (0-1 range)
        popularity_score = min(candidate.popularity_score, 1.0)
        
        # Price affinity
        price_affinity = _calculate_price_affinity(
            candidate.price,
            requirements.max_price
        )
        
        # Availability factor using logarithmic scale
        availability_factor = _calculate_availability_factor(
            candidate.quantity_available,
            max_quantity
        )
        
        # Combined score
        total_score = (
            settings.similarity_weight * similarity_score +
            settings.popularity_weight * popularity_score +
            settings.price_weight * price_affinity +
            settings.availability_weight * availability_factor
        )
        
        # Build reason string
        reason = _build_reason(
            candidate,
            similarity_score,
            popularity_score,
            price_affinity,
            availability_factor
        )
        
        ranked.append(RankedProduct(
            product_id=candidate.product_id,
            score=round(total_score, 3),
            reason=reason
        ))
    
    # Sort by score descending
    ranked.sort(key=lambda x: x.score, reverse=True)
    
    # Filter out excluded items and those below threshold
    valid_ranked = [
        r for r in ranked 
        if r.score >= settings.min_similarity_threshold and not r.excluded_reason
    ]
    excluded = [r for r in ranked if r.excluded_reason or r.score < settings.min_similarity_threshold]
    
    primary = valid_ranked[0] if valid_ranked else None
    alternatives = valid_ranked[1:] + excluded
    
    logger.info(
        f"Ranked {len(candidates)} candidates: "
        f"primary={primary.product_id if primary else None}, "
        f"alternatives={len(alternatives)}"
    )
    
    return primary, alternatives


def _check_exclusions(
    candidate: CandidateProduct,
    requirements: Requirements
) -> str | None:
    """
    Check if candidate should be excluded based on requirements.
    
    Returns:
        Exclusion reason or None if not excluded
    """
    # Out of stock
    if candidate.quantity_available == 0:
        return "out_of_stock"
    
    # Price check
    if requirements.max_price and candidate.price > requirements.max_price:
        return f"exceeds_max_price ({candidate.price} > {requirements.max_price})"
    
    # Allergen check (would need product details - placeholder)
    # In production, this would check candidate.tags or attributes
    for allergen in requirements.must_not_include_allergens:
        if allergen.lower() in [tag.lower() for tag in candidate.tags]:
            return f"contains_allergen: {allergen}"
    
    return None


def _calculate_price_affinity(price: float, target_price: float | None) -> float:
    """
    Calculate price affinity score (0-1).
    
    1.0 = perfect match to target
    0.5 = baseline if no target
    0.0 = far from target
    """
    if target_price is None or target_price <= 0:
        return 0.5  # Baseline when no preference
    
    # Calculate normalized distance
    distance = abs(price - target_price) / target_price
    affinity = max(1.0 - distance, 0.0)
    
    return affinity


def _calculate_availability_factor(quantity: int, max_quantity: int) -> float:
    """
    Calculate availability factor using logarithmic scale.
    
    Uses log10(1 + quantity) / log10(1 + max_quantity) for smoothing.
    """
    if max_quantity <= 0:
        return 0.0
    
    return math.log10(1 + quantity) / math.log10(1 + max_quantity)


def _build_reason(
    candidate: CandidateProduct,
    similarity: float,
    popularity: float,
    price_affinity: float,
    availability: float
) -> str:
    """Build human-readable reason string."""
    reasons = []
    
    if similarity > 0.85:
        reasons.append("high similarity")
    if popularity > 0.7:
        reasons.append("popular")
    if candidate.quantity_available > 0:
        reasons.append("in stock")
    if price_affinity > 0.8:
        reasons.append("good price match")
    
    if not reasons:
        reasons.append("matches criteria")
    
    return ", ".join(reasons)
