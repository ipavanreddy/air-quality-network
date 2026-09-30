"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { DemoBadge } from "@/components/demo-badge";
import { API_URL, apiGet, apiPost, apiPostForm } from "@/lib/api";
import { LANGS, type Lang, t } from "@/lib/i18n";

type Place = { label: string; lat: number; lon: number };
const PRESETS: Place[] = [
  { label: "East Delhi (Patparganj)", lat: 28.628, lon: 77.295 },
  { label: "Sangrur, Punjab", lat: 30.2458, lon: 75.8421 },
  { label: "Panvel, Maharashtra", lat: 18.9894, lon: 73.1175 },
];

type Locate = {
  in_pilot_area: boolean;
  state?: string;
  name?: string;
  corridor?: string;
  jurisdiction?: { id: string; name: string };
  h3_cell: string;
  in_demo_grid?: boolean;
  default_language?: Lang;
};

type Forecast = {
  pm25_now: number;
  category_now: string;
  basis: string;
  horizons: { horizon_hours: number; pm25_low: number; pm25_expected: number; pm25_high: number; category: string }[];
  is_sample_data: boolean;
};

type Verification = {
  is_pollution_event: boolean;
  source_type: string;
  visual_severity: number;
  observed_indicators: string[];
  confidence: number;
  image_quality_ok: boolean;
  requires_human_review: boolean;
  explanation: string;
};

type Report = {
  report_id: string;
  status: string;
  created_at: string;
  verification: Verification | null;
  provenance: { model_name: string; prompt_version: string; mode: string; note?: string | null } | null;
  impact?: {
    cell_confidence_before: number | null;
    cell_confidence_after: number | null;
    alert_id: string | null;
    threshold: number;
  };
  note?: string;
};

type Advisory = {
  advisory_id: string;
  translations: Record<Lang, { headline: string; summary: string; protective_steps: string[]; sensitive_groups: string }>;
  approved_by: string;
  approved_at: string;
};

type SamplePhoto = { name: string; url: string };

const STORAGE_KEY = "vayudrishti.reports";
const REPORTER_KEY = "vayudrishti.reporter";

function readStored(): string[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
  } catch {
    return [];
  }
}

function reporterId(): string {
  try {
    let id = localStorage.getItem(REPORTER_KEY);
    if (!id) {
      id = `anon-${crypto.randomUUID().slice(0, 8)}`;
      localStorage.setItem(REPORTER_KEY, id);
    }
    return id;
  } catch {
    return "anonymous";
  }
}

const STATUS_STYLE: Record<string, string> = {
  verified: "bg-emerald-600 text-white",
  needs_review: "bg-amber-500 text-black",
  rejected: "bg-gray-400 text-black",
  outside_pilot_area: "bg-gray-400 text-black",
};

export function CitizenApp() {
  const [lang, setLang] = useState<Lang>("hi");
  const [place, setPlace] = useState<Place>(PRESETS[0]);
  const [loc, setLoc] = useState<Locate | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [advisory, setAdvisory] = useState<Advisory | null>(null);
  const [samples, setSamples] = useState<SamplePhoto[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Report | null>(null);
  const [mine, setMine] = useState<Report[]>([]);
  const [voiceNote, setVoiceNote] = useState<string | null>(null);

  useEffect(() => {
    apiGet<SamplePhoto[]>("/api/samples/photos").then(setSamples).catch(() => {});
  }, []);

  useEffect(() => {
    let live = true;
    (async () => {
      try {
        const l = await apiGet<Locate>(`/api/locate?lat=${place.lat}&lon=${place.lon}`);
        if (!live) return;
        setLoc(l);
        if (!l.in_pilot_area || !l.state) {
          setForecast(null);
          setAdvisory(null);
          return;
        }
        const [f, advs] = await Promise.all([
          apiGet<Forecast>(l.in_demo_grid ? `/api/cells/${l.h3_cell}/forecast` : `/api/cities/${l.state}/forecast`),
          apiGet<Advisory[]>(`/api/advisories?state=${l.state}&status=approved`),
        ]);
        if (!live) return;
        setForecast(f);
        setAdvisory(advs[0] ?? null);
      } catch (e) {
        if (live) setError((e as Error).message);
      }
    })();
    return () => {
      live = false;
    };
  }, [place]);

  const loadMine = useCallback(async () => {
    const ids = readStored();
    const rows = await Promise.all(ids.map((id) => apiGet<Report>(`/api/reports/${id}`).catch(() => null)));
    setMine(rows.filter((r): r is Report => r !== null));
  }, []);

  useEffect(() => {
    let live = true;
    const tick = () => {
      if (live) void loadMine();
    };
    tick();
    const timer = setInterval(tick, 10000);
    return () => {
      live = false;
      clearInterval(timer);
    };
  }, [loadMine]);

  function choose(f: File) {
    setFile(f);
    setPreview((old) => {
      if (old) URL.revokeObjectURL(old);
      return URL.createObjectURL(f);
    });
    setResult(null);
  }

  async function pickSample(s: SamplePhoto) {
    const blob = await (await fetch(`${API_URL}${s.url}`)).blob();
    choose(new File([blob], s.name, { type: "image/png" }));
  }

  function locateMe() {
    navigator.geolocation?.getCurrentPosition(
      (p) => setPlace({ label: "My location", lat: p.coords.latitude, lon: p.coords.longitude }),
      () => setError("Location permission denied; choose a place instead."),
    );
  }

  async function submit() {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("photo", file);
      form.append("lat", String(place.lat));
      form.append("lon", String(place.lon));
      form.append("description", description);
      form.append("language", lang);
      form.append("reporter_id", reporterId());
      const r = await apiPostForm<Report>("/api/reports", form);
      setResult(r);
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify([r.report_id, ...readStored()].slice(0, 20)));
      } catch {
        /* storage unavailable: report still submitted */
      }
      void loadMine();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function listen() {
    if (!advisory) return;
    const tr = advisory.translations[lang];
    const text = [tr.headline, tr.summary, ...tr.protective_steps].join(". ");
    const res = await apiPost<{ mode: string; audio_base64?: string; mime_type?: string; locale: string }>(
      "/api/text-to-speech",
      { text, language: lang },
    );
    if (res.mode === "real" && res.audio_base64) {
      setVoiceNote("Cloud Text-to-Speech");
      await new Audio(`data:${res.mime_type};base64,${res.audio_base64}`).play();
      return;
    }
    if ("speechSynthesis" in window) {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = res.locale;
      const voice = speechSynthesis.getVoices().find((v) => v.lang.replace("_", "-") === res.locale);
      if (voice) u.voice = voice;
      speechSynthesis.cancel();
      speechSynthesis.speak(u);
      setVoiceNote(
        `Demo mode: browser voice (${res.locale}${voice ? "" : ", no matching voice installed - may read with default voice"})`,
      );
    } else {
      setVoiceNote("Audio playback is not supported in this browser.");
    }
  }

  const v = result?.verification;
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-col gap-4 p-4">
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">VayuDrishti</h1>
            <Badge variant="secondary">Citizen Reporter</Badge>
          </div>
          <p className="text-sm text-muted-foreground">{t("subtitle", lang)}</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            aria-label="Language"
            className="h-8 rounded-lg border bg-background px-2 text-sm"
            value={lang}
            onChange={(e) => setLang(e.target.value as Lang)}
          >
            {LANGS.map((l) => (
              <option key={l.code} value={l.code}>
                {l.name}
              </option>
            ))}
          </select>
          <DemoBadge />
        </div>
      </header>

      {error && <p className="rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>}

      <Card>
        <CardHeader>
          <CardTitle>{t("where", lang)}</CardTitle>
          <CardDescription>
            {place.label} · {place.lat.toFixed(4)}, {place.lon.toFixed(4)}
            {loc?.in_pilot_area ? ` · ${loc.corridor} (${loc.jurisdiction?.id})` : loc ? " · outside pilot area" : ""}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {PRESETS.map((p) => (
            <Button key={p.label} size="sm" variant={place.label === p.label ? "secondary" : "outline"} onClick={() => setPlace(p)}>
              {p.label}
            </Button>
          ))}
          <Button size="sm" variant="ghost" onClick={locateMe}>
            {t("useMyLocation", lang)}
          </Button>
        </CardContent>
      </Card>

      {forecast && (
        <Card>
          <CardHeader>
            <CardTitle>{t("localAir", lang)}</CardTitle>
            <CardDescription>
              {forecast.basis}
              {forecast.is_sample_data && " · sample / simulated data"} · low-cost sensor values are indicative
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-4 gap-2 text-center text-xs">
            <div className="rounded-lg bg-muted p-2">
              <div className="text-muted-foreground">Now</div>
              <div className="text-lg font-semibold">{forecast.pm25_now}</div>
              <div>{forecast.category_now}</div>
            </div>
            {forecast.horizons.map((h) => (
              <div key={h.horizon_hours} className="rounded-lg border p-2">
                <div className="text-muted-foreground">+{h.horizon_hours}h</div>
                <div className="text-lg font-semibold">{h.pm25_expected}</div>
                <div>{h.category}</div>
                <div className="text-[10px] text-muted-foreground">
                  {h.pm25_low}–{h.pm25_high}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{t("photo", lang)}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <label className="block">
            <span className="text-sm">{t("takePhoto", lang)}</span>
            <input
              type="file"
              accept="image/*"
              capture="environment"
              className="mt-1 block w-full text-sm"
              onChange={(e) => e.target.files?.[0] && choose(e.target.files[0])}
            />
          </label>
          {samples.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="text-muted-foreground">{t("orSample", lang)}</span>
              {samples.map((s) => (
                <button key={s.name} type="button" onClick={() => pickSample(s)} className="overflow-hidden rounded border">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={`${API_URL}${s.url}`} alt={s.name} className="h-12 w-16 object-cover" />
                </button>
              ))}
            </div>
          )}
          {preview && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={preview} alt="Selected" className="max-h-60 rounded-lg border object-contain" />
          )}
          <Textarea placeholder={t("describe", lang)} value={description} onChange={(e) => setDescription(e.target.value)} />
          <Button disabled={!file || busy} onClick={submit} className="w-full">
            {busy ? t("submitting", lang) : t("submit", lang)}
          </Button>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {t("result", lang)} <span className="font-mono text-sm">{result.report_id}</span>
              <Badge className={STATUS_STYLE[result.status] ?? ""}>{result.status.replaceAll("_", " ")}</Badge>
            </CardTitle>
            {result.provenance && (
              <CardDescription>
                AI photo check: {result.provenance.model_name} · {result.provenance.prompt_version}
                {result.provenance.mode !== "gemini" && ` · ${result.provenance.note ?? "demo mode"}`}
              </CardDescription>
            )}
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {result.note && <p>{result.note}</p>}
            {v && (
              <>
                <p>
                  {v.is_pollution_event ? "Pollution event detected" : "No pollution event detected"} ·{" "}
                  <b>{v.source_type.replaceAll("_", " ")}</b> · severity {v.visual_severity}/5 · confidence{" "}
                  {(v.confidence * 100).toFixed(0)}%
                </p>
                {v.observed_indicators.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {v.observed_indicators.map((i) => (
                      <Badge key={i} variant="outline">
                        {i}
                      </Badge>
                    ))}
                  </div>
                )}
                <p className="text-xs text-muted-foreground">{v.explanation}</p>
                {!v.image_quality_ok && <p className="text-xs text-red-600">Image quality too low: please retake.</p>}
                {v.requires_human_review && <p className="text-xs text-amber-700">Flagged for human review.</p>}
              </>
            )}
            {result.impact && v?.is_pollution_event && (
              <div className="rounded-lg bg-muted p-2 text-xs">
                <p>{t("thanks", lang)}</p>
                <p>
                  Hotspot Confidence here: {result.impact.cell_confidence_before?.toFixed(0)} →{" "}
                  <b>{result.impact.cell_confidence_after?.toFixed(0)}</b> / 100 (alert threshold {result.impact.threshold})
                </p>
                {result.impact.alert_id && (
                  <p className="font-medium text-emerald-700">
                    ✓ {t("sentToOfficer", lang)} ({loc?.jurisdiction?.name})
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{t("advisory", lang)}</CardTitle>
          {advisory && (
            <CardDescription>
              Approved by {advisory.approved_by} · generated once, shown in your language
            </CardDescription>
          )}
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {!advisory && <p className="text-muted-foreground">{t("noAdvisory", lang)}</p>}
          {advisory && (
            <>
              <p className="font-medium">{advisory.translations[lang].headline}</p>
              <p>{advisory.translations[lang].summary}</p>
              <ul className="list-disc pl-5">
                {advisory.translations[lang].protective_steps.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
              <p className="text-xs text-muted-foreground">{advisory.translations[lang].sensitive_groups}</p>
              <Button size="sm" onClick={listen}>
                🔊 {t("listen", lang)}
              </Button>
              {voiceNote && <p className="text-xs text-muted-foreground">{voiceNote}</p>}
            </>
          )}
        </CardContent>
      </Card>

      {mine.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{t("myReports", lang)}</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1 text-sm">
              {mine.map((r) => (
                <li key={r.report_id} className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs">{r.report_id}</span>
                  <span className="text-xs text-muted-foreground">{new Date(r.created_at).toLocaleString()}</span>
                  <Badge className={STATUS_STYLE[r.status] ?? ""}>{r.status.replaceAll("_", " ")}</Badge>
                  {r.impact?.alert_id && <Badge variant="outline">sent to officer</Badge>}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <footer className="pb-4 text-xs text-muted-foreground">
        Reports are pseudonymous. Photos are checked by AI and reviewed by officers; a likely source is not an
        accusation.
      </footer>
    </main>
  );
}
