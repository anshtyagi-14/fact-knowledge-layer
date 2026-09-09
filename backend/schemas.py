from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import date

class TimeContext(BaseModel):
    period_type: str = Field(description="fiscal_year | quarter | as_of_date | range | unspecified")
    raw: str = Field(description="Raw time context, e.g. FY24")
    start_date: Optional[str] = Field(None, description="Start date if inferable (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date if inferable (YYYY-MM-DD)")

class Scope(BaseModel):
    consolidation: str = Field(description="consolidated | standalone | unspecified")
    segment: str = Field(description="Specific business segment, 'company-wide', or null if unspecified")

class ExtractedFact(BaseModel):
    subject: str = Field(description="The entity this fact is about, e.g., 'Delhivery Limited' or 'India'")
    predicate: str = Field(description="The metric or relationship, e.g., 'revenue_from_services'")
    object: Optional[str] = Field(None, description="The object of the relationship if semantic, else null")
    raw_value: str = Field(description="The exact value as stated in text, e.g., '₹8,142 Cr' or '6.5 percent'")
    value_type: str = Field(description="numeric | categorical | boolean | temporal | textual")
    time_context: TimeContext
    scope: Scope
    evidence_text: str = Field(description="The exact, verbatim substring from the text that proves this fact")
    confidence_score: float = Field(description="Extraction confidence between 0.0 and 1.0")

class FactExtractionResponse(BaseModel):
    facts: List[ExtractedFact]
