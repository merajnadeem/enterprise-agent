from typing import Literal

from pydantic import BaseModel, Field


SourceType = Literal["documentation", "jira", "metrics"]


class InvestigationRequest(BaseModel):

    question: str = Field(min_length=5, max_length=3000)

    sources: list[SourceType] = Field(default_factory=lambda: ["documentation", "jira"], min_length=1, max_length=3)

    require_human_approval: bool = True


class InvestigationResponse(BaseModel):

    job_id: str
    status: str
    message: str


class InvestigationStatusResponse(BaseModel):

    job_id: str
    status: str
    created_at: str
