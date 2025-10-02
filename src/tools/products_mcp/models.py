"""
Pydantic models for request/response validation.

These models match the API contracts defined in SolutionDesign.md.
"""

from typing import Any
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Standard error response format."""
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Wrapper for error responses."""
    error: ErrorDetail


# User Profile Models
class UserProfile(BaseModel):
    """User profile data model."""
    user_id: str
    allergies: list[str] = Field(default_factory=list)
    preferences: dict[str, Any] = Field(default_factory=dict)
    favorite_categories: list[str] = Field(default_factory=list)
    hobbies: list[str] = Field(default_factory=list)
    last_updated_utc: str | None = None


# Vector Search Models
class VectorSearchRequest(BaseModel):
    """Request model for vector search."""
    query_text: str | None = None
    embedding: list[float] | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    top_k: int = 20

    def model_post_init(self, __context: Any) -> None:
        """Validate that either query_text or embedding is provided."""
        if not self.query_text and not self.embedding:
            raise ValueError("Either query_text or embedding must be provided")


class ProductCandidate(BaseModel):
    """A product candidate from vector search."""
    product_id: str
    similarity: float


class VectorSearchResponse(BaseModel):
    """Response model for vector search."""
    candidates: list[ProductCandidate]


# Pricing Models
class PricingRequest(BaseModel):
    """Request model for pricing lookup."""
    product_ids: list[str]


class PricingItem(BaseModel):
    """Pricing information for a product."""
    product_id: str
    price: float
    currency: str = "USD"


class PricingResponse(BaseModel):
    """Response model for pricing lookup."""
    pricing: list[PricingItem]


# Stock Models
class StockRequest(BaseModel):
    """Request model for stock lookup."""
    product_ids: list[str]


class StockItem(BaseModel):
    """Stock information for a product."""
    product_id: str
    quantity_available: int


class StockResponse(BaseModel):
    """Response model for stock lookup."""
    stock: list[StockItem]


# Ranking Models
class Requirements(BaseModel):
    """Normalized user requirements from Facilitator agent."""
    must_not_include_allergens: list[str] = Field(default_factory=list)
    preferred_categories: list[str] = Field(default_factory=list)
    style_preferences: dict[str, Any] = Field(default_factory=dict)
    max_price: float | None = None
    other_notes: str | None = None


class CandidateProduct(BaseModel):
    """Enriched candidate product for ranking."""
    product_id: str
    similarity: float
    price: float
    quantity_available: int
    popularity_score: float = 0.0
    category: str | None = None
    tags: list[str] = Field(default_factory=list)


class RankingRequest(BaseModel):
    """Request model for ranking candidates."""
    requirements: Requirements
    candidates: list[CandidateProduct]


class RankedProduct(BaseModel):
    """A ranked product result."""
    product_id: str
    score: float
    reason: str | None = None
    excluded_reason: str | None = None


class RankingResponse(BaseModel):
    """Response model for ranking."""
    primary: RankedProduct | None = None
    alternatives: list[RankedProduct] = Field(default_factory=list)
