# JARVIS Premarket Analyst — the loop

Adapted from Humbled Trader's free "AI Premarket Analyst" tutorial (Claude + Codex,
humbledtrader.com/blog/claude-codex-ai-premarket-analyst), rebuilt for Zac's stack
and extended with loop-engineering practice (state file, verifier, lessons writeback).

## The machine
```
REPORT_TEMPLATE.md  (the shape)
        |
scan.py -> packet.json -> Brain A (Claude)   -.
                       -> Brain B (blind)     -+-> merge -> REPORT.md -> HTML
        ^                                                       |
   WATCHLIST_CRITERIA.md                              STATE.md + LESSONS.md
   (rules, encoded as flags)                          (memory, self-improvement)
```

## The six loop pieces, mapped
1. **Automation** — the `jarvis-premarket-analyst` scheduled task (daily, before the US open).
2. **Skill** — WATCHLIST_CRITERIA.md + the three prompt files are the procedure manual.
3. **State file** — STATE.md survives between runs; every run reads it first, appends after.
4. **Verifier** — two layers: deterministic pass/fail flags in scan.py (the rules), and
   Brain B, a blind second AI pass that never sees Brain A's reasoning. Never average.
5. **Isolation** — Brain B runs as a separate fresh agent with no shared context.
6. **Connectors** — Yahoo (keyless), ForexFactory calendar, RSS, and Zac's own
   jarvis-lookup edge function for the Your Book overlay.

## Execution policy — read this
This system is decision support. It NEVER places real orders and never will from here.
Verified picks can be logged as paper trades (STATE.md run log) and the JARVIS
dashboard already runs live A$10k paper sims (sim-trade edge function) for forward
track records. Zac makes any real trade himself, in his own broker.

## Daily run (what the scheduled task does)
1. `python3 scan.py` → packet.json (data only, zero opinions)
2. Brain A: follow prompt_brain_a.md against packet.json → claude_view.md
3. Brain B: fresh blind agent gets ONLY prompt_brain_b.md + packet.json → codex_view.md
4. Merge: follow prompt_merge.md → REPORT.md (never average the brains)
5. `python3 render_report.py REPORT.md` → reports/premarket_YYYY-MM-DD.html
6. Append run log to STATE.md; write any due lessons to LESSONS.md

## Swap in a true cross-vendor Brain B later
Install OpenAI's Codex CLI (`npm i -g @openai/codex`, `codex login` with a ChatGPT
plan), then pipe prompt_brain_b.md + packet.json into `codex exec` and save to
codex_view.md. Until then, Brain B is a fresh, blind Claude agent — honest caveat:
same vendor, so agreement means slightly less than a true rival model.

## Honest limitations (same as the original tutorial)
- yfinance reports ~no premarket volume, so RVOL is a full-day stand-in premarket.
- Quiet tape = short list. That's real; don't fake a busy morning.
- The baseline rules are Humbled Trader's published backtest parameters, not Zac's.
  Replace them after backtesting your own (the Strategy Lab can help).
Not financial advice. The rules pick the watchlist, the brains judge quality,
Zac makes the trade.
