"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { apiGet } from "@/lib/api";

type Status = {
  demo_mode: boolean;
  integrations: { name: string; label: string; mode: string; demo_behaviour: string }[];
};

/** Always-visible label when any fallback / simulated data is in use. */
export function DemoBadge() {
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    apiGet<Status>("/api/config")
      .then(setStatus)
      .catch(() => setError(true));
  }, []);

  if (error) return <Badge variant="destructive">Service unreachable</Badge>;
  if (!status) return <Badge variant="outline">Connecting…</Badge>;
  if (!status.demo_mode) return <Badge className="bg-emerald-600 text-white">Live data</Badge>;
  const live = status.integrations.filter((i) => i.mode === "real");
  return (
    <div className="relative">
      <button type="button" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        <Badge className="bg-amber-500 text-black">
          {live.length ? `Partly live · some sample data` : "Demo mode · sample data"}
        </Badge>
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-72 rounded-lg border bg-background p-3 text-xs shadow-lg">
          {live.length > 0 && (
            <>
              <p className="mb-1 font-medium">Live:</p>
              <ul className="mb-2 list-disc space-y-0.5 pl-4">
                {live.map((i) => (
                  <li key={i.name}>{i.label}</li>
                ))}
              </ul>
            </>
          )}
          <p className="mb-1 font-medium">Using demo fallbacks for:</p>
          <ul className="list-disc space-y-0.5 pl-4">
            {status.integrations
              .filter((i) => i.mode !== "real")
              .map((i) => (
                <li key={i.name}>
                  {i.label}: <span className="text-muted-foreground">{i.demo_behaviour}</span>
                </li>
              ))}
          </ul>
        </div>
      )}
    </div>
  );
}
