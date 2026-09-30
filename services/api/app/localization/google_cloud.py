"""Cloud Translation (v3) and Cloud Text-to-Speech (v1) via REST with Application Default Credentials.

Enabled when GOOGLE_CLOUD_PROJECT is set and ADC resolves (GOOGLE_APPLICATION_CREDENTIALS or
`gcloud auth application-default login`). The APIs must be enabled on the project.
"""
import base64

import httpx

from app.config import settings

LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "pa": "Punjabi"}
TTS_LOCALES = {"en": "en-IN", "hi": "hi-IN", "pa": "pa-IN"}


def _token() -> str:
    import google.auth
    import google.auth.transport.requests

    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


def _headers() -> dict:
    return {"Authorization": f"Bearer {_token()}", "x-goog-user-project": settings.google_cloud_project}


def translate_texts(texts: list[str], target: str, source: str = "en") -> list[str]:
    url = (f"https://translation.googleapis.com/v3/projects/{settings.google_cloud_project}"
           f"/locations/global:translateText")
    body = {"contents": texts, "sourceLanguageCode": source, "targetLanguageCode": target,
            "mimeType": "text/plain"}
    res = httpx.post(url, json=body, headers=_headers(), timeout=20)
    res.raise_for_status()
    return [t["translatedText"] for t in res.json()["translations"]]


def synthesize(text: str, language: str) -> str:
    """Return base64 MP3 audio."""
    body = {
        "input": {"text": text},
        "voice": {"languageCode": TTS_LOCALES.get(language, "en-IN")},
        "audioConfig": {"audioEncoding": "MP3"},
    }
    res = httpx.post("https://texttospeech.googleapis.com/v1/text:synthesize", json=body,
                     headers=_headers(), timeout=30)
    res.raise_for_status()
    audio = res.json()["audioContent"]
    base64.b64decode(audio)  # validate
    return audio
