from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core import integrations
from app.core.deps import check_state, get_engine, not_found
from app.localization.google_cloud import LANGUAGE_NAMES, TTS_LOCALES

router = APIRouter(prefix="/api", tags=["language & voice"])


class AdvisoryIn(BaseModel):
    state: str
    h3_cell: str | None = None


class ApproveIn(BaseModel):
    officer: str = Field(min_length=1)


class TranslateIn(BaseModel):
    texts: list[str]
    target: str
    source: str = "en"


class TtsIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    language: str = "hi"


@router.post("/advisories/generate")
def generate(body: AdvisoryIn):
    return get_engine().generate_advisory(check_state(body.state), body.h3_cell)


@router.post("/advisories/{advisory_id}/approve")
def approve(advisory_id: str, body: ApproveIn):
    try:
        return get_engine().approve_advisory(advisory_id, body.officer)
    except KeyError:
        raise not_found("advisory", advisory_id) from None


@router.get("/advisories")
def list_advisories(state: str | None = None, status: str | None = None):
    rows = [a for a in get_engine().store.all("advisories")
            if (state is None or a["state"] == state) and (status is None or a["status"] == status)]
    return sorted(rows, key=lambda a: a["created_at"], reverse=True)


@router.post("/translate")
def translate(body: TranslateIn):
    if body.target not in LANGUAGE_NAMES:
        raise HTTPException(422, f"supported targets: {sorted(LANGUAGE_NAMES)}")
    if integrations.enabled("translation"):
        try:
            from app.localization.google_cloud import translate_texts

            return {"mode": "real", "engine": "cloud_translation_v3",
                    "translations": translate_texts(body.texts, body.target, body.source)}
        except Exception as exc:  # noqa: BLE001
            integrations.record_fallback("translation", exc)
    return {"mode": "demo", "engine": "none",
            "note": "Cloud Translation not configured; free-text translation unavailable in demo mode "
                    "(advisories use pre-written templates).", "translations": body.texts}


@router.post("/text-to-speech")
def tts(body: TtsIn):
    locale = TTS_LOCALES.get(body.language, "en-IN")
    if integrations.enabled("text_to_speech"):
        try:
            from app.localization.google_cloud import synthesize

            return {"mode": "real", "engine": "cloud_text_to_speech", "mime_type": "audio/mpeg",
                    "audio_base64": synthesize(body.text, body.language), "locale": locale}
        except Exception as exc:  # noqa: BLE001
            integrations.record_fallback("text_to_speech", exc)
    return {"mode": "demo", "engine": "browser_speech_synthesis", "locale": locale, "text": body.text,
            "note": "Cloud Text-to-Speech not configured: play with the browser's built-in voice."}
