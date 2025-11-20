"""Models for CDS API endpoints."""

from datetime import date, datetime
from typing import Optional, List, Any, Literal
from pydantic import BaseModel, Field
import uuid


class StandardResponse(BaseModel):
    """Base model for standardized API responses."""
    
    status: Literal["success", "error", "client_error"] = Field(
        ..., 
        description="Response status: success, error (5xx), or client_error (4xx)"
    )
    correlation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for tracking this request across the system"
    )
    data: Optional[Any] = Field(None, description="Response data (only present on success)")
    error_message: Optional[str] = Field(None, description="Error message (only present on errors)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class CDSRecordResponse(BaseModel):
    """Response model for a single CDS record."""
    
    date: date
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    change_pct: Optional[float] = None
    
    class Config:
        from_attributes = True


class CDSListResponse(BaseModel):
    """Response model for list of CDS records."""
    
    total: int = Field(..., description="Total number of records")
    records: List[CDSRecordResponse] = Field(..., description="List of CDS records")
    date_range: Optional[dict] = Field(None, description="Date range of records")


class CDSListData(BaseModel):
    """Data structure for CDS list endpoint."""
    
    total: int = Field(..., description="Total number of records")
    records: List[CDSRecordResponse] = Field(..., description="List of CDS records")
    date_range: Optional[dict] = Field(None, description="Date range of records")


class CDSLatestResponse(BaseModel):
    """Response model for latest CDS record."""
    
    record: Optional[CDSRecordResponse] = Field(None, description="Latest CDS record")
    message: Optional[str] = Field(None, description="Message if no data available")


class CDSLatestData(BaseModel):
    """Data structure for latest CDS endpoint."""
    
    record: Optional[CDSRecordResponse] = Field(None, description="Latest CDS record")
    message: Optional[str] = Field(None, description="Message if no data available")


class CDSStatisticsResponse(BaseModel):
    """Response model for CDS statistics."""
    
    total_records: int
    earliest_date: Optional[date]
    latest_date: Optional[date]
    sources: List[str]


class CDSStatisticsData(BaseModel):
    """Data structure for CDS statistics endpoint."""
    
    total_records: int
    earliest_date: Optional[date]
    latest_date: Optional[date]
    sources: List[str]
