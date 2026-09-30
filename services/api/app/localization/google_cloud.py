"""Cloud Translation, Text-to-Speech and Speech-to-Text via REST.

Auth: `GOOGLE_CLOUD_API_KEY` when set (Translation Basic v2, TTS v1, STT v1 all accept API keys),
otherwise Application Default Credentials (service account on Cloud Run, or
GOOGLE_APPLICATION_CREDENTIALS locally) with Translation Advanced v3.
"""
import base64

import httpx

from app.config import settings

LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "pa": "Punjabi"}
TTS_LOCALES = {"en": "en-IN", "hi": "hi-IN", "pa": "pa-IN"}
STT_LOCALES = TTS_LOCALES


def _token() -> str:
    import google.auth
    import google.auth.transport.requests

    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


def _auth() -> tuple[dict, dict]:
    """(headers, query params) for a Google Cloud REST call."""
    if settings.google_cloud_api_key:
        return {}, {"key": settings.google_cloud_api_key}
    return {"Authorization": f"Bearer {_token()}", "x-goog-user-project": settings.google_cloud_project}, {}


def translation_engine() -> str:
    return "cloud_translation_v2" if settings.google_cloud_api_key else "cloud_translation_v3"


def translate_texts(texts: list[str], target: str, source: str = "en") -> list[str]:
    headers, params = _auth()
    if settings.google_cloud_api_key:
        res = httpx.post("https://translation.googleapis.com/language/translate/v2", params=params,
                         headers=headers, timeout=20,
                         json={"q": texts, "source": source, "target": target, "format": "text"})
        res.raise_for_status()
        return [t["translatedText"] for t in res.json()["data"]["translations"]]
    url = (f"https://translation.googleapis.com/v3/projects/{settings.google_cloud_project}"
           f"/locations/global:translateText")
    body = {"contents": texts, "sourceLanguageCode": source, "targetLanguageCode": target,
            "mimeType": "text/plain"}
    res = httpx.post(url, json=body, headers=headers, timeout=20)
    res.raise_for_status()
    return [t["translatedText"] for t in res.json()["translations"]]


def synthesize(text: str, language: str) -> str:
    """Return base64 MP3 audio."""
    headers, params = _auth()
    body = {
        "input": {"text": text},
        "voice": {"languageCode": TTS_LOCALES.get(language, "en-IN")},
        "audioConfig": {"audioEncoding": "MP3"},
    }
    res = httpx.post("https://texttospeech.googleapis.com/v1/text:synthesize", json=body,
                     headers=headers, params=params, timeout=30)
    res.raise_for_status()
    audio = res.json()["audioContent"]
    base64.b64decode(audio)  # validate
    return audio


def transcribe(audio: bytes, language: str, mime_type: str) -> dict:
    """Short voice note (< 60 s) -> text.

    The citizen picks the language in the app (en-IN / hi-IN / pa-IN). Browser MediaRecorder sends
    WebM/Opus (Chrome, Firefox) or OGG/Opus.
    """
    headers, params = _auth()
    config: dict = {"languageCode": STT_LOCALES.get(language, "en-IN"), "enableAutomaticPunctuation": True}
    if "webm" in mime_type:
        config.update({"encoding": "WEBM_OPUS", "sampleRateHertz": 48000})
    elif "ogg" in mime_type:
        config.update({"encoding": "OGG_OPUS", "sampleRateHertz": 48000})
    res = httpx.post("https://speech.googleapis.com/v1/speech:recognize", headers=headers,
                     params=params, timeout=60, json={"config": config, "audio": {"content": base64.b64encode(audio).decode()}})
    res.raise_for_status()
    results = res.json().get("results", [])
    text = " ".join(r["alternatives"][0].get("transcript", "").strip() for r in results if r.get("alternatives"))
    detected = results[0].get("languageCode") if results else None
    conf = results[0]["alternatives"][0].get("confidence") if results and results[0].get("alternatives") else None
    return {"transcript": text.strip(), "language_code": detected or config["languageCode"], "confidence": conf}
