# Deploying the two Next.js apps to Vercel

Each app is its own Vercel project and builds on its own from its folder. Neither app has workspace
dependencies. Each app folder has its own `pnpm-lock.yaml` and a settings-only `pnpm-workspace.yaml`
(`allowBuilds`), so `pnpm install && pnpm build` works there without the monorepo root.

| | Citizen Reporter | Environmental Officer |
|---|---|---|
| Vercel project | `air-quality-network-citizen` (suggested) | `air-quality-network-officer` (suggested) |
| Root Directory | `apps/citizen-web` | `apps/officer-dashboard` |
| Framework preset | Next.js | Next.js |
| Install command | `pnpm install` | `pnpm install` |
| Build command | `pnpm build` (`next build`) | `pnpm build` (`next build`) |
| Output | default (`.next`), **no** `output: "standalone"`, no Docker | same |
| Node.js | 20.x or 22.x (Next.js 16 needs ≥ 20.9) | same |
| Live URL | _to be filled by lead_ | _to be filled by lead_ |

## Environment variables (set in Vercel, never committed)

| Variable | Citizen | Officer | Value |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | required | required | `https://air-quality-network-api-847963771142.asia-south1.run.app` (no trailing slash) |
| `NEXT_PUBLIC_MAPS_API_KEY` | not used | optional | Browser Maps JavaScript API key (HTTP-referrer restricted) |

`NEXT_PUBLIC_*` values are inlined at **build** time, so redeploy after changing them.

**Maps key referrer:** the browser key is currently restricted to `localhost` and `https://*.run.app`.
Add `https://*.vercel.app/*` (or the exact production domains) to the key's HTTP-referrer allow-list, or the
officer map shows "Maps key rejected" and falls back to Leaflet + OpenStreetMap (the demo still works).

## CLI deploy (from each app folder)

```bash
cd apps/citizen-web
vercel link                                  # once: create/link the project
vercel env add NEXT_PUBLIC_API_URL production
vercel --prod

cd ../officer-dashboard
vercel link
vercel env add NEXT_PUBLIC_API_URL production
vercel env add NEXT_PUBLIC_MAPS_API_KEY production   # optional
vercel --prod
```

With the Git integration instead, create two projects from `ipavanreddy/air-quality-network` and set
**Root Directory** as in the table. Leave "Include files outside the Root Directory" off.

## After the first Vercel deploy: allow the origins on the API

The API only accepts browser calls from allowed origins. Redeploy it with the final URLs (the regex also
allows preview deployments):

```bash
CORS_ORIGINS="https://<citizen>.vercel.app,https://<officer>.vercel.app" \
CORS_ORIGIN_REGEX='https://.*\.vercel\.app' \
infrastructure/cloud-run/deploy.sh api
```

## Smoke test

1. Open the officer app: the header badge reads "N/M live · rest sample data". Click it to see which
   integrations are live (Gemini, Translation, TTS, STT, Maps, BigQuery, Cloud Storage) and which are sample.
2. Open the citizen app, choose *East Delhi (Patparganj)*, pick the chimney sample photo and submit. Gemini
   verifies it (about 10–25 s) and the officer inbox shows the alert within a few seconds.
