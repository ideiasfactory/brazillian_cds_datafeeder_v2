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


class FieldInfo(BaseModel):
    """Documentation for a single field in the CDS schema."""
    
    name: str = Field(..., description="Field name")
    type: str = Field(..., description="Data type")
    required: bool = Field(..., description="Whether the field is required")
    description: str = Field(..., description="Field description")
    example: Optional[Any] = Field(None, description="Example value")
    unit: Optional[str] = Field(None, description="Unit of measurement")


class CDSSchemaInfo(BaseModel):
    """Complete schema information for CDS data."""
    
    entity: str = Field("cds_record", description="Entity name")
    description: str = Field(
        "Brazilian CDS 5-year spread historical data in USD",
        description="Entity description"
    )
    fields: List[FieldInfo] = Field(..., description="List of fields in the schema")
    data_source: str = Field("investing.com", description="Primary data source")
    update_frequency: str = Field(
        "Daily at 06:00 UTC (03:00 BRT)",
        description="Data update schedule"
    )
    currency: str = Field("USD", description="Currency for CDS spreads")
    unit: str = Field(
        "Basis points (1 bp = 0.01%)",
        description="Unit of measurement for prices"
    )


class CDSStatisticsInfo(BaseModel):
    """Database statistics for CDS data."""
    
    total_records: int = Field(..., description="Total number of records in database")
    earliest_date: Optional[date] = Field(None, description="Earliest available date")
    latest_date: Optional[date] = Field(None, description="Most recent date")
    last_update: Optional[datetime] = Field(None, description="Last update timestamp")
    sources: List[str] = Field(default_factory=list, description="Data sources used")


class CDSInfoData(BaseModel):
    """Data structure for CDS info endpoint."""
    
    schema_info: CDSSchemaInfo = Field(..., description="Schema documentation", alias="schema")
    statistics: Optional[CDSStatisticsInfo] = Field(
        None, 
        description="Database statistics (only when include_stats=true)"
    )
    related_endpoints: dict = Field(
        default_factory=lambda: {
            "latest": "/api/cds/latest",
            "list": "/api/cds",
            "statistics": "/api/cds/statistics",
            "info": "/api/cds/info"
        },
        description="Related API endpoints"
    )
    
    class Config:
        populate_by_name = True  # Permite usar tanto 'schema' quanto 'schema_info'
