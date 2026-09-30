"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { AdvisoryPanel } from "@/components/advisory-panel";
import { AlertDetail } from "@/components/alert-detail";
import { DemoBadge } from "@/components/demo-badge";
import { type ColorBy, HexMap } from "@/components/hex-map";
import { AlertInbox, ConfidenceBreakdown, ForecastCard, FreshnessList, ModelRegistry } from "@/components/panels";
import { ago, apiGet, apiPost } from "@/lib/api";
import type {
  Advisory,
  Alert,
  Analytics,
  City,
  Factor,
  Forecast,
  Grid,
  GridCell,
  ModelCard,
  Report,
} from "@/lib/types";

type CellDetail = { confidence_breakdown: { confidence: number; band: string; factors: Factor[] } };

const HORIZONS = [0, 24, 48, 72];
const OFFICERS: Record<string, string> = { "delhi-ncr": "officer.dpcc", punjab: "officer.ppcb", maharashtra: "officer.mpcb" };

export function Dashboard() {
  const [cities, setCities] = useState<City[]>([]);
  const [state, setState] = useState("delhi-ncr");
  const [officer, setOfficer] = useState(OFFICERS["delhi-ncr"]);
  const [grid, setGrid] = useState<Grid | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [advisories, setAdvisories] = useState<Advisory[]>([]);
  const [models, setModels] = useState<ModelCard[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedCell, setSelectedCell] = useState<GridCell | null>(null);
  const [cellDetail, setCellDetail] = useState<CellDetail | null>(null);
  const [colorBy, setColorBy] = useState<ColorBy>("confidence");
  const [horizon, setHorizon] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const city = cities.find((c) => c.id === state);
  const jurisdiction = city?.jurisdiction.id;

  const refresh = useCallback(async () => {
    if (!jurisdiction) return;
    try {
      const [g, a, r, an, adv] = await Promise.all([
        apiGet<Grid>(`/api/grid?city=${state}`),
        apiGet<Alert[]>(`/api/alerts?jurisdiction=${jurisdiction}`),
        apiGet<Report[]>(`/api/reports?state=${state}`),
        apiGet<Analytics>(`/api/cities/${state}/analytics`),
        apiGet<Advisory[]>(`/api/advisories?state=${state}`),
      ]);
      setGrid(g);
      setAlerts(a);
      setReports(r);
      setAnalytics(an);
      setAdvisories(adv);
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, [state, jurisdiction]);

  useEffect(() => {
    apiGet<City[]>("/api/cities").then(setCities).catch((e) => setError((e as Error).message));
    apiGet<ModelCard[]>("/api/models").then(setModels).catch(() => {});
  }, []);

  useEffect(() => {
    let live = true;
    const tick = () => {
      if (live) void refresh();
    };
    tick();
    const t = setInterval(tick, 4000);
    return () => {
      live = false;
      clearInterval(t);
    };
  }, [refresh]);

  useEffect(() => {
    let live = true;
    apiGet<Forecast>(`/api/cities/${state}/forecast`)
      .then((f) => live && setForecast(f))
      .catch(() => {});
    return () => {
      live = false;
    };
  }, [state]);

  useEffect(() => {
    if (!selectedCell) return;
    let live = true;
    apiGet<CellDetail>(`/api/cells/${selectedCell.h3_cell}`)
      .then((d) => live && setCellDetail(d))
      .catch(() => {});
    return () => {
      live = false;
    };
  }, [selectedCell]);

  function switchState(id: string) {
    setState(id);
    setOfficer(OFFICERS[id] ?? "officer");
    setSelectedId(null);
    setSelectedCell(null);
    setCellDetail(null);
    setGrid(null);
  }

  async function resetDemo() {
    await apiPost("/api/demo/reset", {});
    setSelectedId(null);
    await refresh();
  }

  const selected = alerts.find((a) => a.alert_id === selectedId) ?? null;
  const hotspotCells = grid?.cells.filter((c) => c.hotspot_id).map((c) => c.h3_cell) ?? [];
  const h = forecast?.horizons.find((x) => x.horizon_hours === horizon);
  const pmRatio = h && forecast ? h.pm25_expected / Math.max(1, forecast.pm25_now) : 1;
  const pending = analytics?.alerts_by_status.pending_review ?? 0;

  return (
    <main className="mx-auto flex w-full max-w-[1400px] flex-col gap-4 p-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">VayuDrishti</h1>
            <Badge variant="secondary">Environmental Officer</Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            {city ? `${city.jurisdiction.name} · ${city.corridor}` : "Federated hyper-local air quality"}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            aria-label="Jurisdiction"
            className="h-8 rounded-lg border bg-background px-2 text-sm"
            value={state}
            onChange={(e) => switchState(e.target.value)}
          >
            {cities.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.jurisdiction.id})
              </option>
            ))}
          </select>
          <Input aria-label="Officer" className="h-8 w-36" value={officer} onChange={(e) => setOfficer(e.target.value)} />
          <DemoBadge />
          <Button size="sm" variant="ghost" onClick={resetDemo}>
            Reset demo
          </Button>
        </div>
      </header>

      {error && <p className="rounded bg-red-50 p-2 text-sm text-red-700">API error: {error}</p>}

      <section className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        <Kpi label="Active hotspots" value={analytics?.active_hotspots ?? "…"} />
        <Kpi label="Alerts awaiting review" value={pending} highlight={pending > 0} />
        <Kpi
          label="Acknowledged / closed"
          value={`${(analytics?.alerts_by_status.acknowledged ?? 0) + (analytics?.alerts_by_status.action_taken ?? 0)} / ${analytics?.alerts_by_status.closed ?? 0}`}
        />
        <Kpi label="Citizen reports" value={`${analytics?.citizen_reports ?? 0} (${analytics?.verified_reports ?? 0} verified)`} />
        <Kpi label="Cross-boundary in / out" value={`${analytics?.cross_boundary_in ?? 0} / ${analytics?.cross_boundary_out ?? 0}`} />
        <Kpi
          label={`Official station${grid?.station.is_sample ? " (sample)" : ""}`}
          value={grid ? `${Math.round(grid.station.pm25)} µg/m³` : "…"}
          sub={grid ? `${grid.station.name} · ${ago(grid.station.observed_at)}` : ""}
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Hyper-local grid (H3 res 8, ~1 km cells)</CardTitle>
            <CardDescription className="flex flex-wrap items-center gap-3">
              <span>
                Colour:{" "}
                <select
                  aria-label="Colour by"
                  className="rounded border bg-background px-1"
                  value={colorBy}
                  onChange={(e) => setColorBy(e.target.value as ColorBy)}
                >
                  <option value="confidence">Hotspot Confidence</option>
                  <option value="pm25">PM2.5 (calibrated)</option>
                </select>
              </span>
              <span className="flex items-center gap-2">
                Forecast:
                <input
                  aria-label="Forecast horizon"
                  type="range"
                  min={0}
                  max={3}
                  step={1}
                  value={HORIZONS.indexOf(horizon)}
                  onChange={(e) => {
                    setHorizon(HORIZONS[Number(e.target.value)]);
                    setColorBy("pm25");
                  }}
                />
                <b>{horizon === 0 ? "now" : `+${horizon}h`}</b>
              </span>
              {grid?.is_sample_data && <Badge variant="outline">sample / simulated data</Badge>}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[480px]">
              {grid ? (
                <HexMap
                  grid={grid}
                  reports={reports}
                  selectedCells={selected ? hotspotCellsFor(grid, selected.hotspot_id) : hotspotCells}
                  colorBy={colorBy}
                  pmRatio={horizon === 0 ? 1 : pmRatio}
                  horizonLabel={horizon === 0 ? "(now)" : `(+${horizon}h forecast, corridor ratio)`}
                  onSelectCell={setSelectedCell}
                />
              ) : (
                <div className="flex h-full items-center justify-center text-muted-foreground">Loading grid…</div>
              )}
            </div>
          </CardContent>
        </Card>
        <AlertInbox alerts={alerts} selected={selectedId} onSelect={(a) => setSelectedId(a.alert_id)} />
      </section>

      {selected && <AlertDetail key={selected.alert_id} alert={selected} officer={officer} onChanged={refresh} />}

      <section className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Cell inspector</CardTitle>
            <CardDescription>{selectedCell ? selectedCell.h3_cell : "Click a grid cell on the map"}</CardDescription>
          </CardHeader>
          <CardContent>
            {selectedCell && cellDetail ? (
              <ConfidenceBreakdown
                confidence={cellDetail.confidence_breakdown.confidence}
                band={cellDetail.confidence_breakdown.band}
                factors={cellDetail.confidence_breakdown.factors}
                threshold={grid?.threshold}
              />
            ) : (
              <p className="text-sm text-muted-foreground">Factor breakdown appears here.</p>
            )}
          </CardContent>
        </Card>
        <ForecastCard forecast={forecast} horizon={horizon} />
        <Card>
          <CardHeader>
            <CardTitle>Data freshness</CardTitle>
            <CardDescription>Is this hotspot based on current data or the latest satellite pass?</CardDescription>
          </CardHeader>
          <CardContent>{grid && <FreshnessList items={grid.freshness} />}</CardContent>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <AdvisoryPanel state={state} officer={officer} advisories={advisories} onChanged={refresh} />
        <ModelRegistry models={models} state={state} />
      </section>

      <footer className="pb-4 text-xs text-muted-foreground">
        Likely sources guide inspection; they are not findings of fault. Low-cost sensor values are calibrated and
        indicative. Sample/simulated data is labelled.
      </footer>
    </main>
  );
}

function hotspotCellsFor(grid: Grid, hotspotId: string) {
  return grid.cells.filter((c) => c.hotspot_id === hotspotId).map((c) => c.h3_cell);
}

function Kpi({ label, value, sub, highlight }: { label: string; value: string | number; sub?: string; highlight?: boolean }) {
  return (
    <Card size="sm" className={highlight ? "ring-2 ring-red-500" : ""}>
      <CardContent>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-xl font-semibold tabular-nums">{value}</p>
        {sub && <p className="truncate text-[11px] text-muted-foreground">{sub}</p>}
      </CardContent>
    </Card>
  );
}
