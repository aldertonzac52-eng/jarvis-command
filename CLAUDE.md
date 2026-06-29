# JARVIS Command — project guide for Claude Code

This repo is Zac's personal "morning command" dashboard. It is a **static site** that
shows portfolio, watchlist, the daily JARVIS briefing, and today's agenda. It is
designed to be **regenerated and redeployed once per morning** by an agent.

## Architecture (keep it this simple)
- `index.html` — the whole UI. Mobile-first PWA. Reads `data.json` at runtime, and
  also has the same data inlined as a `FALLBACK` so it works offline / via file://.
- `data.json` — the ONLY thing that changes day to day. Plain numbers, no secrets.
- `manifest.webmanifest` + `icon.svg` — "Add to Home Screen" support.
- `netlify.toml` — publish dir + no-cache header for data.json.

There is **no backend and no API key in the site**. The data is baked at build time
by the agent. This keeps Zac's financial figures off any public key/endpoint.

## Data sources (the agent fetches these, the site never does)
- Supabase project `liqfekbcoopnelrnkkox`, schema `portfolio`:
  - `holdings` (units, avg_cost, cost_basis, currency, price_mode)
  - `watchlist`
  - `price_history` (ticker, price, currency, as_of, source) — updated by the briefing
- Live prices: web search (ASX tickers in AUD, US in USD). FX: AUD/USD.
- Agenda: Google Calendar (today, Australia/Melbourne), Gmail unread, ClickUp list
  `901614962846` ("nest possible proposals"), Google Drive recent files.

## Daily regeneration recipe
1. Run the JARVIS morning briefing (it already writes today's prices to
   `portfolio.price_history`).
2. Recompute the numbers below and overwrite **`data.json`** (see schema in the file).
   - WTC.AX: value = units × price; pl = value − cost_basis.
   - NOW (USD): value_aud = (units × price) ÷ audusd; pl_aud = (value−cost_basis) ÷ audusd.
   - V500: estimate only — value_aud = cost_basis × (1 + VOO_daily_pct); flag estimate:true.
   - Totals in AUD.
3. **Voice:** generate the spoken briefing with ElevenLabs (preset voice "Alistair",
   id `d9d5c263-f84e-4752-97b5-3750fcc6fd2f`, model `text2speech_v2_elevenlabs`).
   Take the job's `results.rawUrl` and download it to **`briefing.mp3`** in this folder
   (`curl -L -o briefing.mp3 "<rawUrl>"`). Keep `data.json` → `briefing.audio` =
   `"briefing.mp3"`. The dashboard plays this file; browser TTS is only a fallback.
4. Re-inline the fallback: `python3 build.py` (copies data.json into index.html).
5. Deploy: `./deploy.sh` (or the Netlify MCP deploy-site for site `jarvis-command-zac`).
   Make sure `briefing.mp3` is in the folder so it deploys too.

## Rules
- Never put the Supabase service-role key, or any secret, in `index.html`/`data.json`.
- Keep `data.json` numeric and small. No PII beyond what Zac already sees.
- Don't add a framework. One HTML file is the point.
- Mark any estimated/unverified figure (`estimate:true` or a `note`).
