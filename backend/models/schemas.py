"""
Pydantic models / schemas used across the application.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ProductCategory(str, Enum):
    LAPTOP = "laptop"
    PHONE = "phone"
    EARBUDS = "earbuds"
    HEADPHONES = "headphones"
    MONITOR = "monitor"
    FURNITURE = "furniture"
    TABLET = "tablet"
    SMARTWATCH = "smartwatch"
    CAMERA = "camera"
    OTHER = "other"


class ParsedQuery(BaseModel):
    """Output of the planner agent: structured intent extracted from the user query."""

    category: str = Field(description="Normalized product category, e.g. 'laptop'")
    budget: Optional[float] = Field(default=None, description="Maximum budget in INR")
    min_budget: Optional[float] = Field(default=None, description="Minimum budget in INR, if any")
    purpose: Optional[str] = Field(default=None, description="Use case, e.g. 'coding', 'gaming'")
    preferences: list[str] = Field(default_factory=list, description="Extra preferences/features requested")
    raw_query: str = Field(description="Original user query")
    search_keywords: str = Field(description="Optimized search keywords for e-commerce search bars")
    sites: list[str] = Field(default_factory=list, description="Sites to search for this category")


class ProductSpec(BaseModel):
    """Normalized scraped product record."""

    source: str
    title: str
    price: Optional[float] = None
    currency: str = "INR"
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    availability: Optional[str] = None
    specifications: dict[str, Any] = Field(default_factory=dict)
    url: Optional[str] = None
    image_url: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class ComparisonRow(BaseModel):
    title: str
    source: str
    price: Optional[float] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    value_for_money_score: Optional[float] = None
    performance_score: Optional[float] = None
    durability_score: Optional[float] = None
    use_case_fit_score: Optional[float] = None
    overall_score: Optional[float] = None
    url: Optional[str] = None


class RecommendationResult(BaseModel):
    best_choice: dict[str, Any] = Field(default_factory=dict)
    budget_choice: dict[str, Any] = Field(default_factory=dict)
    premium_choice: dict[str, Any] = Field(default_factory=dict)
    comparison_table: list[dict[str, Any]] = Field(default_factory=list)
    why_recommended: str = ""


class SearchProductsRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural language shopping query")
    user_id: Optional[str] = Field(default="anonymous", description="Identifier for memory/history")
    max_results_per_site: Optional[int] = Field(default=None, ge=1, le=20)


class SearchProductsResponse(BaseModel):
    parsed_query: ParsedQuery
    products: list[ProductSpec]
    recommendation: RecommendationResult
    session_id: str


class CompareProductsRequest(BaseModel):
    products: list[ProductSpec]
    purpose: Optional[str] = None
    budget: Optional[float] = None


class CompareProductsResponse(BaseModel):
    recommendation: RecommendationResult


class SearchHistoryItem(BaseModel):
    session_id: str
    user_id: str
    query: str
    parsed_query: dict[str, Any]
    created_at: datetime


class SearchHistoryResponse(BaseModel):
    items: list[SearchHistoryItem]


class RecommendationsResponse(BaseModel):
    items: list[dict[str, Any]]
