# Watchlist criteria — the source of truth the scanner encodes

These rules decide watchlist membership. The code computes them as pass/fail flags.
The AI brains never decide membership — they only judge quality.

The two setups below are Humbled Trader's published baseline parameters (from her
free tutorial). **They are placeholders until Zac backtests his own** — edit this file
and re-encode scan.py whenever the rules change. The Your Book overlay is Zac's own.

## DAY TRADING WATCHLIST — "Trend Join Long"
(Her published backtest: 54.6% win rate, profit factor 1.59, 280 trades.)

Premarket selection — ALL required:
- Gap % vs previous close > 3%
- Price > $3
- Market cap > $1B
- Relative volume (RVOL) > 1.5 (full-day stand-in when run premarket)
- Price breaking above yesterday's high

Intraday plan (context for the report, not encoded in the scanner):
- Window 10:00am–3:30pm ET
- Trigger: price > premarket high AND > prior high-of-day
- Stop: 1% below premarket high or LOD, whichever is lower (= 1R)
- Scale 1/3 at +1R, 1/3 at +2R, trail last 1/3 on the 21-EMA
- Flat by 3:51pm

## SWING WATCHLIST — gap-up + real catalyst
(Her published backtest: 57.6% win / PF 5.34 on news catalysts; 44.7% / PF 2.57 on earnings.)

Premarket selection — ALL required:
- Gap % ≥ 8%
- Price > $3
- Open > yesterday's high
- Open > 200-day SMA
- Market cap ≥ $800M
- A real catalyst (earnings on the gap day, or news with no earnings)

Swing entries are starter ideas only — no invented stops or targets.

## YOUR BOOK overlay (Zac-specific, always on)
The scanner also pulls Zac's holdings and watchlist and flags:
- own_gapper: one of his names appears in the day's movers
- buy_zone: price at/under his stored buy-below level
- big_move: any of his names moving ±4% on the day

Holdings: WTC.AX, NOW, V500(VOO). Watchlist: CSL.AX, TLX.AX, WDS.AX, BAP.AX, PV1.AX,
MU, IONQ, MSFT, OUST, VPG, AMBA. Buy levels come from the live dashboard snapshot.
