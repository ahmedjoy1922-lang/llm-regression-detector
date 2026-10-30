from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


# Restrict classification to the support team's approved labels.
class Label(StrEnum):
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"


# Store one fictional ticket and its human-approved answer.
class TicketCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^case-[0-9]{3}$")
    text: str = Field(min_length=10, max_length=500)
    expected_label: Label
    slice: str = Field(min_length=2, max_length=40)


# Validate the structured answer returned by the model.
class Prediction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: Label
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(min_length=3, max_length=200)