"""
Basic validation tests for the MCP server structure.

Tests that don't require actual Cosmos DB connection.
"""

import pytest
from pydantic import ValidationError


def test_settings_loads():
    """Test that settings can be loaded."""
    from config import settings
    assert settings.cosmos_db_name == "appdb"
    assert settings.vector_top_k == 20


def test_user_profile_model():
    """Test UserProfile model validation."""
    from models import UserProfile
    
    profile = UserProfile(
        user_id="test-123",
        allergies=["nuts", "dairy"],
        preferences={"flavor": "spicy"},
        favorite_categories=["outdoor"],
        hobbies=["hiking"]
    )
    
    assert profile.user_id == "test-123"
    assert len(profile.allergies) == 2


def test_vector_search_request_validation():
    """Test VectorSearchRequest requires embedding or query_text."""
    from models import VectorSearchRequest
    
    # Should work with embedding
    req = VectorSearchRequest(embedding=[0.1] * 1536)
    assert req.embedding is not None
    
    # Should work with query_text
    req = VectorSearchRequest(query_text="test query")
    assert req.query_text == "test query"
    
    # Should fail without either
    with pytest.raises(ValueError):
        VectorSearchRequest()


def test_ranking_request_model():
    """Test RankingRequest model validation."""
    from models import RankingRequest, Requirements, CandidateProduct
    
    req = RankingRequest(
        requirements=Requirements(
            must_not_include_allergens=["nuts"],
            max_price=100.0
        ),
        candidates=[
            CandidateProduct(
                product_id="p1",
                similarity=0.9,
                price=50.0,
                quantity_available=5,
                popularity_score=0.8
            )
        ]
    )
    
    assert len(req.candidates) == 1
    assert req.requirements.max_price == 100.0


def test_error_response_model():
    """Test ErrorResponse structure."""
    from models import ErrorResponse, ErrorDetail
    
    err = ErrorResponse(
        error=ErrorDetail(
            code="NotFound",
            message="Resource not found",
            details={"resource_id": "123"}
        )
    )
    
    assert err.error.code == "NotFound"
    assert err.error.details["resource_id"] == "123"


def test_ranking_logic_exclusions():
    """Test ranking exclusion logic."""
    from ranking import _check_exclusions
    from models import Requirements, CandidateProduct
    
    requirements = Requirements(
        must_not_include_allergens=["nuts"],
        max_price=50.0
    )
    
    # Out of stock
    candidate = CandidateProduct(
        product_id="p1",
        similarity=0.9,
        price=30.0,
        quantity_available=0,
        popularity_score=0.8
    )
    assert _check_exclusions(candidate, requirements) == "out_of_stock"
    
    # Exceeds max price
    candidate = CandidateProduct(
        product_id="p2",
        similarity=0.9,
        price=75.0,
        quantity_available=5,
        popularity_score=0.8
    )
    assert "exceeds_max_price" in _check_exclusions(candidate, requirements)
    
    # Contains allergen
    candidate = CandidateProduct(
        product_id="p3",
        similarity=0.9,
        price=30.0,
        quantity_available=5,
        popularity_score=0.8,
        tags=["nuts", "organic"]
    )
    assert "contains_allergen" in _check_exclusions(candidate, requirements)
    
    # Valid candidate
    candidate = CandidateProduct(
        product_id="p4",
        similarity=0.9,
        price=30.0,
        quantity_available=5,
        popularity_score=0.8,
        tags=["organic"]
    )
    assert _check_exclusions(candidate, requirements) is None


def test_ranking_score_calculation():
    """Test ranking score calculation."""
    from ranking import rank_candidates
    from models import Requirements, CandidateProduct
    
    requirements = Requirements(max_price=100.0)
    
    candidates = [
        CandidateProduct(
            product_id="p1",
            similarity=0.95,
            price=50.0,
            quantity_available=10,
            popularity_score=0.9,
            tags=[]
        ),
        CandidateProduct(
            product_id="p2",
            similarity=0.80,
            price=75.0,
            quantity_available=5,
            popularity_score=0.7,
            tags=[]
        )
    ]
    
    primary, alternatives = rank_candidates(requirements, candidates)
    
    assert primary is not None
    assert primary.product_id == "p1"  # Higher similarity should win
    assert len(alternatives) == 1
    assert alternatives[0].product_id == "p2"
