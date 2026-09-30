"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { apiGet } from "@/lib/api";
import type { IntegrationStatus } from "@/lib/types";

const MAPS_KEY = process.env.NEXT_PUBLIC_MAPS_API_KEY ?? "";

/** Visible "Demo mode / sample data" badge + per-integration breakdown (real / demo / fallback). */
export function DemoBadge() {
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [error, setError] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const load = () =>
      apiGet<IntegrationStatus>("/api/config")
        .then((s) => {
          setStatus(s);
          setError(false);
        })
        .catch(() => setError(true));
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, []);

  if (error) return <Badge variant="destructive">API unreachable</Badge>;
  if (!status) return <Badge variant="outline">Checking API…</Badge>;
  const demo = status.demo_mode || !MAPS_KEY;
  return (
    <div className="relative">
      <button type="button" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        {demo ? (
          <Badge className="bg-amber-500 text-black">Demo mode · sample data</Badge>
        ) : (
          <Badge className="bg-emerald-600 text-white">Live integrations</Badge>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-[1000] mt-2 w-96 rounded-lg border bg-background p-3 text-xs shadow-lg">
          <p className="mb-2 font-medium">Integrations (Gemini model: {status.gemini_model})</p>
          <ul className="space-y-1.5">
            {[
              ...status.integrations,
              {
                name: "maps",
                label: "Google Maps (basemap)",
                mode: MAPS_KEY ? "real" : "demo",
                env_vars: ["NEXT_PUBLIC_MAPS_API_KEY"],
                demo_behaviour: "Leaflet + OpenStreetMap tiles",
                last_error: null,
              },
            ].map((i) => (
              <li key={i.name} className="flex items-start justify-between gap-2">
                <span>
                  {i.label}
                  <span className="block text-muted-foreground">
                    {i.mode === "real" ? i.env_vars.join(", ") : `Demo: ${i.demo_behaviour}`}
                    {i.last_error ? ` · last error: ${i.last_error}` : ""}
                  </span>
                </span>
                <Badge variant={i.mode === "real" ? "default" : i.mode === "fallback" ? "destructive" : "outline"}>
                  {i.mode}
                </Badge>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
