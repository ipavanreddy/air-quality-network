"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ago, label } from "@/lib/api";
import type { Alert, Factor, Forecast, Freshness, ModelCard } from "@/lib/types";

const FACTOR_LABEL: Record<string, string> = {
  sensor_anomaly: "Sensor anomaly",
  satellite: "Satellite signal",
  citizen_reports: "Citizen reports",
  weather: "Weather plausibility",
};

export function bandClass(band: string) {
  return band === "High" ? "bg-red-600 text-white" : band === "Medium" ? "bg-orange-500 text-white" : "bg-gray-300 text-black";
}

export function ConfidenceBreakdown({ confidence, band, factors, threshold }: {
  confidence: number;
  band: string;
  factors: Factor[];
  threshold?: number;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-end gap-3">
        <div className="text-4xl font-semibold tabular-nums">{confidence.toFixed(0)}</div>
        <div className="pb-1 text-muted-foreground">/ 100</div>
        <Badge className={bandClass(band)}>{band}</Badge>
        {threshold !== undefined && <span className="pb-1 text-xs text-muted-foreground">alert threshold {threshold}</span>}
      </div>
      <ul className="space-y-1.5">
        {factors.map((f) => (
          <li key={f.name}>
            <div className="flex justify-between text-xs">
              <span className="font-medium">
                {FACTOR_LABEL[f.name] ?? f.name} × {Math.round(f.weight * 100)}%
              </span>
              <span className="tabular-nums">
                {f.score.toFixed(0)} → +{f.contribution.toFixed(1)}
              </span>
            </div>
            <div className="h-1.5 rounded bg-muted">
              <div className="h-1.5 rounded bg-foreground/70" style={{ width: `${Math.min(100, f.score)}%` }} />
            </div>
            <p className="text-[11px] text-muted-foreground">{f.detail}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function FreshnessList({ items }: { items: Freshness[] }) {
  return (
    <ul className="space-y-1 text-xs">
      {items.map((f) => (
        <li key={f.signal} className="flex justify-between gap-2">
          <span>
            {f.signal}
            <span className="block text-[11px] text-muted-foreground">{f.source}</span>
          </span>
          <span className="shrink-0 text-right tabular-nums">
            {ago(f.observed_at)}
            {f.is_sample && (
              <Badge variant="outline" className="ml-1 h-4 px-1 text-[10px]">
                sample
              </Badge>
            )}
          </span>
        </li>
      ))}
    </ul>
  );
}

const STATUS_STYLE: Record<Alert["status"], string> = {
  pending_review: "bg-red-600 text-white",
  acknowledged: "bg-amber-500 text-black",
  action_taken: "bg-blue-600 text-white",
  closed: "bg-gray-300 text-black",
};

export function StatusBadge({ status }: { status: Alert["status"] }) {
  return <Badge className={STATUS_STYLE[status]}>{label(status)}</Badge>;
}

export function AlertInbox({ alerts, selected, onSelect }: {
  alerts: Alert[];
  selected: string | null;
  onSelect: (a: Alert) => void;
}) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Alert inbox</CardTitle>
        <CardDescription>Routed to this jurisdiction. Every action needs your approval.</CardDescription>
      </CardHeader>
      <CardContent className="max-h-[440px] space-y-2 overflow-y-auto">
        {alerts.length === 0 && <p className="text-muted-foreground">No alerts. Waiting for evidence…</p>}
        {alerts.map((a) => (
          <button
            key={a.alert_id}
            type="button"
            onClick={() => onSelect(a)}
            className={`w-full rounded-lg border p-2 text-left transition hover:bg-muted ${selected === a.alert_id ? "border-foreground" : ""}`}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-mono text-xs">{a.alert_id}</span>
              <StatusBadge status={a.status} />
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-1 text-xs">
              {a.kind === "cross_boundary" && <Badge className="bg-purple-600 text-white">Cross-boundary from {a.origin_jurisdiction_id}</Badge>}
              {a.fast_path && <Badge variant="outline">fast path</Badge>}
              <Badge className={bandClass(a.band)}>{a.confidence.toFixed(0)}/100</Badge>
              {a.is_sample_data && <Badge variant="outline">sample data</Badge>}
            </div>
            <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{a.action_brief.summary}</p>
            <p className="text-[11px] text-muted-foreground">{ago(a.sent_at)}</p>
          </button>
        ))}
      </CardContent>
    </Card>
  );
}

export function ForecastCard({ forecast, horizon }: { forecast: Forecast | null; horizon: number }) {
  if (!forecast) return null;
  const max = Math.max(...forecast.horizons.map((h) => h.pm25_high), forecast.pm25_now) * 1.1;
  return (
    <Card>
      <CardHeader>
        <CardTitle>72-hour corridor forecast</CardTitle>
        <CardDescription>
          {forecast.location_id} · model <span className="font-mono">{forecast.model_id}</span>
          {forecast.is_sample_data && " · sample data"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2 text-xs">
        <div>
          Now (24h mean): <b>{forecast.pm25_now} µg/m³</b> · {forecast.category_now}
        </div>
        {forecast.horizons.map((h) => (
          <div key={h.horizon_hours} className={h.horizon_hours === horizon ? "rounded bg-muted p-1" : "p-1"}>
            <div className="flex justify-between">
              <span className="font-medium">+{h.horizon_hours}h: {h.category}</span>
              <span className="tabular-nums">
                ~{h.pm25_expected} ({h.pm25_low}–{h.pm25_high})
              </span>
            </div>
            <div className="relative mt-1 h-2 rounded bg-muted-foreground/10">
              <div
                className="absolute h-2 rounded bg-orange-400/60"
                style={{ left: `${(h.pm25_low / max) * 100}%`, width: `${((h.pm25_high - h.pm25_low) / max) * 100}%` }}
              />
              <div className="absolute h-2 w-0.5 bg-black" style={{ left: `${(h.pm25_expected / max) * 100}%` }} />
            </div>
            <p className="text-[11px] text-muted-foreground">Drivers: {h.drivers.join("; ")}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export function ModelRegistry({ models, state }: { models: ModelCard[]; state: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Shared model registry</CardTitle>
        <CardDescription>Models are shared across state configurations via the canonical schema.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-xs">
        {models.map((m) => {
          const metrics = (m.card.metrics_mae_vs_persistence ?? m.card.metrics_mae) as
            | Record<string, Record<string, { model_mae: number; persistence_mae: number }>>
            | undefined;
          const mine = metrics?.[state];
          return (
            <div key={m.id} className="rounded border p-2">
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono">{m.id}</span>
                <Badge variant={m.used_by.includes(state) ? "default" : "outline"}>{m.type}</Badge>
              </div>
              <p className="text-muted-foreground">{m.name}</p>
              <p>Used by: {m.used_by.join(", ")}</p>
              {mine && (
                <p>
                  Backtest MAE (model vs persistence):{" "}
                  {Object.entries(mine)
                    .map(([h, v]) => `${h} ${v.model_mae} vs ${v.persistence_mae}`)
                    .join(" · ")}
                </p>
              )}
              {Array.isArray(m.card.limitations) && (
                <p className="text-muted-foreground">Limitations: {(m.card.limitations as string[]).join("; ")}</p>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
