"use client";

import { useEffect, useRef, useState } from "react";
import type { Grid, GridCell, Report } from "@/lib/types";

const MAPS_KEY = process.env.NEXT_PUBLIC_MAPS_API_KEY ?? "";

export type ColorBy = "pm25" | "confidence";

const PM_COLORS: [number, string][] = [
  [30, "#00b050"],
  [60, "#92d050"],
  [90, "#e6d200"],
  [120, "#ff9900"],
  [250, "#ff0000"],
  [Infinity, "#8b0000"],
];

export function pmColor(pm: number | null): string {
  if (pm === null) return "#9ca3af";
  return PM_COLORS.find(([lim]) => pm <= lim)![1];
}

export function confColor(c: number): string {
  if (c >= 75) return "#b91c1c";
  if (c >= 60) return "#f97316";
  if (c >= 45) return "#facc15";
  return "#d1d5db";
}

type Shape = {
  cell: GridCell;
  color: string;
  opacity: number;
  outline: boolean;
  tooltip: string;
};

type Dot = { lat: number; lon: number; color: string; radius: number; tooltip: string };

type Props = {
  grid: Grid;
  reports: Report[];
  selectedCells: string[];
  colorBy: ColorBy;
  pmRatio: number;
  horizonLabel: string;
  onSelectCell?: (cell: GridCell) => void;
};

function buildLayers({ grid, reports, selectedCells, colorBy, pmRatio, horizonLabel }: Props) {
  const selected = new Set(selectedCells);
  const shapes: Shape[] = grid.cells.map((c) => {
    const pm = c.pm25 === null ? null : Math.round(c.pm25 * pmRatio);
    return {
      cell: c,
      color: colorBy === "pm25" ? pmColor(pm) : confColor(c.confidence),
      opacity: colorBy === "pm25" && pm === null ? 0.12 : 0.45,
      outline: selected.has(c.h3_cell) || !!c.hotspot_id,
      tooltip:
        `${c.h3_cell}<br/>PM2.5 ${pm ?? "n/a"} µg/m³ ${horizonLabel}` +
        `<br/>Hotspot Confidence ${c.confidence.toFixed(0)} (${c.band})` +
        `<br/>Land use: ${c.land_use ?? "n/a"}${c.report_count ? `<br/>${c.report_count} citizen report(s)` : ""}`,
    };
  });
  const dots: Dot[] = [
    ...grid.sensors.map((s) => ({
      lat: s.lat,
      lon: s.lon,
      color: "#1d4ed8",
      radius: 5,
      tooltip: `${s.sensor_id}${s.is_simulated ? " (simulated)" : ""}<br/>PM2.5 ${s.pm25_calibrated} calibrated (raw ${s.pm25_raw}) · indicative`,
    })),
    ...reports
      .filter((r) => r.state === grid.state)
      .map((r) => ({
        lat: r.location.lat,
        lon: r.location.lon,
        color: "#9333ea",
        radius: 8,
        tooltip: `Citizen report ${r.report_id}${r.is_sample ? " (sample)" : ""}<br/>${r.status} · ${r.source_type ?? ""}`,
      })),
  ];
  return { shapes, dots };
}

/** Leaflet + OpenStreetMap fallback (no key needed). */
function LeafletMap(props: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const state = useRef<{ L: typeof import("leaflet"); map: import("leaflet").Map; layer: import("leaflet").LayerGroup } | null>(null);
  const propsRef = useRef(props);

  useEffect(() => {
    propsRef.current = props;
  });

  useEffect(() => {
    let cancelled = false;
    let map: import("leaflet").Map | undefined;
    (async () => {
      const mod = await import("leaflet");
      const L = (mod as unknown as { default?: typeof mod }).default ?? mod;
      if (cancelled || !ref.current) return;
      map = L.map(ref.current, { zoomControl: true }).setView(propsRef.current.grid.center, 13);
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(map);
      state.current = { L, map, layer: L.layerGroup().addTo(map) };
      draw(propsRef.current);
    })();
    return () => {
      cancelled = true;
      map?.remove();
      state.current = null;
    };
  }, []);

  function draw(p: Props) {
    const s = state.current;
    if (!s) return;
    const { L, layer } = s;
    layer.clearLayers();
    const { shapes, dots } = buildLayers(p);
    for (const sh of shapes) {
      const poly = L.polygon(sh.cell.boundary, {
        color: sh.outline ? "#111827" : sh.color,
        weight: sh.outline ? 2 : 0.5,
        fillColor: sh.color,
        fillOpacity: sh.opacity,
      }).bindTooltip(sh.tooltip);
      poly.on("click", () => p.onSelectCell?.(sh.cell));
      poly.addTo(layer);
    }
    for (const d of dots) {
      L.circleMarker([d.lat, d.lon], { radius: d.radius, color: "#fff", weight: 1.5, fillColor: d.color, fillOpacity: 1 })
        .bindTooltip(d.tooltip)
        .addTo(layer);
    }
  }

  useEffect(() => {
    draw(props);
  });

  useEffect(() => {
    state.current?.map.setView(props.grid.center, 13);
  }, [props.grid.state, props.grid.center]);

  return <div ref={ref} className="h-full w-full" />;
}

// ---- Google Maps JS API (used when NEXT_PUBLIC_MAPS_API_KEY is set) ------------------------------
type LatLng = { lat: number; lng: number };
type GOverlay = { setMap(m: GMap | null): void; addListener(ev: string, fn: () => void): void };
type GMap = { setCenter(c: LatLng): void };
type GMaps = {
  Map: new (el: HTMLElement, opts: object) => GMap;
  Polygon: new (opts: object) => GOverlay;
  Circle: new (opts: object) => GOverlay;
  InfoWindow: new (opts: object) => { open(opts: object): void; close(): void };
};

let gmapsPromise: Promise<GMaps> | null = null;
function loadGoogleMaps(): Promise<GMaps> {
  const w = window as unknown as { google?: { maps: GMaps } };
  if (w.google?.maps) return Promise.resolve(w.google.maps);
  gmapsPromise ??= new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(MAPS_KEY)}&v=weekly`;
    s.async = true;
    s.onload = () => resolve((window as unknown as { google: { maps: GMaps } }).google.maps);
    s.onerror = reject;
    document.head.appendChild(s);
  });
  return gmapsPromise;
}

function GoogleMap(props: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const state = useRef<{ g: GMaps; map: GMap; overlays: GOverlay[] } | null>(null);
  const propsRef = useRef(props);

  useEffect(() => {
    propsRef.current = props;
  });

  function draw(p: Props) {
    const s = state.current;
    if (!s) return;
    s.overlays.forEach((o) => o.setMap(null));
    s.overlays = [];
    const info = new s.g.InfoWindow({});
    const { shapes, dots } = buildLayers(p);
    for (const sh of shapes) {
      const poly = new s.g.Polygon({
        paths: sh.cell.boundary.map(([lat, lng]) => ({ lat, lng })),
        strokeColor: sh.outline ? "#111827" : sh.color,
        strokeWeight: sh.outline ? 2 : 0.5,
        fillColor: sh.color,
        fillOpacity: sh.opacity,
        map: s.map,
      });
      poly.addListener("click", () => {
        p.onSelectCell?.(sh.cell);
        info.close();
        const [lat, lng] = [sh.cell.lat, sh.cell.lon];
        const box = new s.g.InfoWindow({ content: sh.tooltip, position: { lat, lng } });
        box.open({ map: s.map });
      });
      s.overlays.push(poly);
    }
    for (const d of dots) {
      s.overlays.push(
        new s.g.Circle({
          center: { lat: d.lat, lng: d.lon },
          radius: d.radius * 12,
          fillColor: d.color,
          fillOpacity: 1,
          strokeColor: "#fff",
          strokeWeight: 1,
          map: s.map,
        }),
      );
    }
  }

  useEffect(() => {
    let cancelled = false;
    loadGoogleMaps().then((g) => {
      if (cancelled || !ref.current) return;
      const [lat, lng] = propsRef.current.grid.center;
      const map = new g.Map(ref.current, { center: { lat, lng }, zoom: 13, mapTypeControl: false });
      state.current = { g, map, overlays: [] };
      draw(propsRef.current);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    draw(props);
  });

  useEffect(() => {
    const [lat, lng] = props.grid.center;
    state.current?.map.setCenter({ lat, lng });
  }, [props.grid.state, props.grid.center]);

  return <div ref={ref} className="h-full w-full" />;
}

export function HexMap(props: Props) {
  const w = props.grid.weather;
  // If the key is rejected (e.g. the domain is not in its HTTP-referrer allow-list), Google calls
  // window.gm_authFailure; fall back to Leaflet + OSM instead of showing a broken map.
  const [googleFailed, setGoogleFailed] = useState(false);
  useEffect(() => {
    if (!MAPS_KEY) return;
    (window as unknown as { gm_authFailure?: () => void }).gm_authFailure = () => setGoogleFailed(true);
  }, []);
  const useGoogle = !!MAPS_KEY && !googleFailed;
  const windTo = (w.wind_dir_deg + 180) % 360;
  return (
    <div className="relative h-full w-full overflow-hidden rounded-lg border">
      {useGoogle ? <GoogleMap {...props} /> : <LeafletMap {...props} />}
      <div className="pointer-events-none absolute top-2 right-2 z-[500] rounded-md bg-background/90 px-2 py-1 text-xs shadow">
        <div className="flex items-center gap-2">
          <span className="inline-block text-lg leading-none" style={{ transform: `rotate(${windTo}deg)` }} aria-hidden>
            ↑
          </span>
          <span>
            Wind {w.wind_speed_ms} m/s from {w.wind_dir_deg}°
            <br />
            BLH {w.boundary_layer_m ?? "n/a"} m · RH {w.humidity}%
          </span>
        </div>
      </div>
      <div className="pointer-events-none absolute bottom-2 left-2 z-[500] rounded-md bg-background/90 px-2 py-1 text-[11px] shadow">
        <span className="mr-2 inline-block size-2 rounded-full bg-blue-700" /> sensor
        <span className="mr-2 ml-3 inline-block size-2 rounded-full bg-purple-600" /> citizen report
        <span className="ml-3">▭ bold outline = hotspot</span>
        {!useGoogle && (
          <span className="ml-3 text-muted-foreground">
            Basemap: OpenStreetMap (Leaflet fallback{googleFailed ? ": Maps key rejected for this domain" : ""})
          </span>
        )}
      </div>
    </div>
  );
}
