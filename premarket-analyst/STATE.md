# STATE — the loop's memory (survives between runs)

The agent forgets between runs. This file does not.
Every run: read this first, append a run log entry at the end, and if a pick's
outcome is known, write the lesson into LESSONS.md.

## Current status
- Pipeline built: 2026-07-02
- Runs completed: 1
- Open paper picks: none yet
- Verifier: Brain B (blind subagent) + deterministic flags in scan.py
- Execution: PAPER ONLY. This system never places real orders. Zac pulls any trigger himself.

## Pending
- First live run in the US premarket window
- Backtest Zac's own rules to replace the placeholder criteria in WATCHLIST_CRITERIA.md
- Optional: wire OpenAI Codex CLI as a true cross-vendor Brain B (see README)

## Run log
<!-- Append: date · gappers found · day/swing eligible counts · brains agreed on · picks logged -->
- 2026-07-02 21:55 MEL: First full run. 12 gappers (live screener). Day-eligible flags: RGC, FRHC, RDDT, GH, DLO. Swing: none (premarket, no open yet). Brains agreed HIGH on DLO only; conflicted on RDDT (A high / B skip); RGC unanimous trap. Brain B hallucinated 3 claims not in packet (caught at merge). No paper picks logged pending Zac's go-ahead. NFP day.
