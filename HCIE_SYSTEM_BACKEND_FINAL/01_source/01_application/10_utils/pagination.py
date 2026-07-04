"""
Pagination Utilities

Provides standardized pagination support for API endpoints.
"""

from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field
from fastapi import Query

T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Standard pagination parameters.
    """
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=50, ge=1, le=1000, description="Number of items per page")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: Optional[str] = Field(default="asc", regex="^(asc|desc)$", description="Sort order (asc or desc)")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard paginated response format.
    """
    items: List[T] = Field(description="List of items in current page")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_previous: bool = Field(description="Whether there is a previous page")
    
    class Config:
        arbitrary_types_allowed = True


def paginate(
    items: List[T],
    total: int,
    pagination_params: PaginationParams
) -> PaginatedResponse[T]:
    """
    Create a paginated response from a list of items.
    
    Args:
        items: List of items for current page
        total: Total number of items across all pages
        pagination_params: Pagination parameters
    
    Returns:
        PaginatedResponse with pagination metadata
    """
    total_pages = (total + pagination_params.page_size - 1) // pagination_params.page_size
    
    return PaginatedResponse[T](
        items=items,
        total=total,
        page=pagination_params.page,
        page_size=pagination_params.page_size,
        total_pages=total_pages,
        has_next=pagination_params.page < total_pages,
        has_previous=pagination_params.page > 1
    )


async def get_pagination_params(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=1000, description="Items per page"),
    sort_by: Optional[str] = Query(default=None, description="Sort field"),
    sort_order: str = Query(default="asc", regex="^(asc|desc)$", description="Sort order")
) -> PaginationParams:
    """
    FastAPI dependency for pagination parameters.
    """
    return PaginationParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )


class CursorPaginationParams(BaseModel):
    """
    Cursor-based pagination parameters for large datasets.
    More efficient than offset-based pagination for large datasets.
    """
    cursor: Optional[str] = Field(default=None, description="Cursor for next page")
    limit: int = Field(default=50, ge=1, le=1000, description="Number of items per page")
    
    @property
    def has_cursor(self) -> bool:
        """Check if cursor is provided."""
        return self.cursor is not None


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """
    Cursor-based paginated response format.
    """
    items: List[T] = Field(description="List of items in current page")
    next_cursor: Optional[str] = Field(default=None, description="Cursor for next page")
    has_next: bool = Field(description="Whether there is a next page")
    
    class Config:
        arbitrary_types_allowed = True


def cursor_paginate(
    items: List[T],
    next_cursor: Optional[str],
    has_next: bool
) -> CursorPaginatedResponse[T]:
    """
    Create a cursor-based paginated response.
    
    Args:
        items: List of items for current page
        next_cursor: Cursor for next page (if any)
        has_next: Whether there is a next page
    
    Returns:
        CursorPaginatedResponse with cursor pagination metadata
    """
    return CursorPaginatedResponse[T](
        items=items,
        next_cursor=next_cursor,
        has_next=has_next
    )
