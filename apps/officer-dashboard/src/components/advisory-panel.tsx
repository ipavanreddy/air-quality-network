"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiPost } from "@/lib/api";
import type { Advisory } from "@/lib/types";

const LANGS: [string, string][] = [
  ["en", "English"],
  ["hi", "हिन्दी"],
  ["pa", "ਪੰਜਾਬੀ"],
];

export function AdvisoryPanel({ state, officer, advisories, onChanged }: {
  state: string;
  officer: string;
  advisories: Advisory[];
  onChanged: () => void;
}) {
  const [lang, setLang] = useState("hi");
  const [busy, setBusy] = useState(false);
  const latest = advisories[0];

  async function generate() {
    setBusy(true);
    try {
      await apiPost("/api/advisories/generate", { state });
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  async function approve(id: string) {
    setBusy(true);
    try {
      await apiPost(`/api/advisories/${id}/approve`, { officer });
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  const t = latest?.translations[lang];
  return (
    <Card>
      <CardHeader>
        <CardTitle>Citizen health advisory</CardTitle>
        <CardDescription>Generated once, localised to English / Hindi / Punjabi. Published only after your approval.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="flex flex-wrap gap-2">
          <Button size="sm" disabled={busy} onClick={generate}>
            Generate advisory draft
          </Button>
          {LANGS.map(([code, name]) => (
            <Button key={code} size="sm" variant={lang === code ? "secondary" : "ghost"} onClick={() => setLang(code)}>
              {name}
            </Button>
          ))}
        </div>
        {!latest && <p className="text-muted-foreground">No advisory yet for this state.</p>}
        {latest && t && (
          <div className="space-y-1 rounded-lg border p-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className={latest.status === "approved" ? "bg-emerald-600 text-white" : "bg-amber-500 text-black"}>
                {latest.status === "approved" ? `published · approved by ${latest.approved_by}` : "draft · awaiting approval"}
              </Badge>
              <Badge variant="outline">{latest.category}</Badge>
              <Badge variant="outline">translation: {t.translation.engine} ({t.translation.mode})</Badge>
            </div>
            <p className="font-medium">{t.headline}</p>
            <p>{t.summary}</p>
            <ul className="list-disc pl-5 text-xs">
              {t.protective_steps.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
            <p className="text-xs text-muted-foreground">{t.sensitive_groups}</p>
            <p className="text-[11px] text-muted-foreground">
              {latest.provenance.model_name} · {latest.provenance.prompt_version} · {latest.provenance.mode}
            </p>
            {latest.status === "draft" && (
              <Button size="sm" disabled={busy} onClick={() => approve(latest.advisory_id)}>
                Approve &amp; publish to citizens
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
