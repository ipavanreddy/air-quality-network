"""Structured Gemini outputs (PRD §33). JSON Schema copies live in ai/schemas/ (see `export`).

Run `uv run python -m app.ai.schemas` to regenerate ai/schemas/*.schema.json.
"""
import json
from typing import Literal

from pydantic import BaseModel, Field

from app.config import REPO_ROOT

SourceType = Literal["crop_residue_burning", "waste_burning", "industrial_emission", "construction_dust",
                     "traffic", "other_unknown"]


class PhotoVerification(BaseModel):
    is_pollution_event: bool
    source_type: SourceType
    visual_severity: int = Field(ge=0, le=5, description="0 = none, 5 = extreme")
    observed_indicators: list[str]
    confidence: float = Field(ge=0, le=1)
    image_quality_ok: bool
    requires_human_review: bool
    explanation: str


class LikelySource(BaseModel):
    type: SourceType
    confidence: float = Field(ge=0, le=1)
    rationale: str


class EvidenceItem(BaseModel):
    signal: str
    value: str
    source: str
    observed: str


class RecommendedAction(BaseModel):
    action_id: str
    action: str
    priority: Literal["high", "medium", "low"]


class ActionBrief(BaseModel):
    summary: str
    risk_level: Literal["low", "medium", "high", "severe"]
    likely_sources: list[LikelySource]
    evidence: list[EvidenceItem]
    forecast_outlook: str
    recommended_actions: list[RecommendedAction]
    uncertainties: list[str]
    confidence: float = Field(ge=0, le=1)
    requires_human_review: bool


class HealthAdvisory(BaseModel):
    headline: str
    category: str
    summary: str
    protective_steps: list[str]
    sensitive_groups: str


class TranslatedAdvisory(BaseModel):
    headline: str
    summary: str
    protective_steps: list[str]
    sensitive_groups: str


SCHEMAS = {
    "photo_verification_v1": PhotoVerification,
    "action_brief_v1": ActionBrief,
    "health_advisory_v1": HealthAdvisory,
    "translated_advisory_v1": TranslatedAdvisory,
}
SCHEMA_DIR = REPO_ROOT / "ai" / "schemas"


def export() -> None:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    for name, model in SCHEMAS.items():
        (SCHEMA_DIR / f"{name}.schema.json").write_text(
            json.dumps(model.model_json_schema(), indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    export()
