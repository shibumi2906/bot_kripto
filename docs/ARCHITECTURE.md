# Architecture and analytical policy (technical-v2)

## Functional core / imperative shell

The domain accepts immutable Candle/MarketSeries/Quote values and explicit integer UTC
as_of. It performs no I/O, reads no environment and calls neither a clock nor an LLM.
Source order does not affect results. API version is 0.3.0; policy version technical-v2.

The shell collects hourly history and current bid/ask in parallel, normalizes provider
schemas, then invokes the core. AI receives a deep copy and returns only commentary.

The SHA-256 input_hash covers all supplied histories, quotes, as_of, mode, balance,
risk_percent and engine version. It is a fingerprint, not input storage. Replay of live
data still requires saving those inputs. Non-finite rejected values use stable internal
JSON markers for hashing; numerical report fields never contain them.

## Candle and activity checks

Same spot USDT pair and hourly UTC opening timestamps. At least 60 consecutive closed
candles, no duplicates or gaps, positive finite OHLC and nonnegative finite base volume.
as_of and candle timestamps must be nonnegative integers, excluding bool/NaN/infinity.
At least two source histories must pass freshness checks. Up to 120 common intervals
are used; the last closed hour cannot be a full hour behind the expected latest closure.

Volume zero is allowed as an observed data value, but a directional scenario requires,
on every accepted history, a positive latest volume and at least 20 positive-volume
hours out of the latest 24. Passing activity checks does not establish market depth.

## Current quotes and scenario admission

The shell separately requests Binance bookTicker, OKX market/ticker and Kraken Ticker.
A quote has bid, ask, timestamp and timestamp_kind. OKX supplies exchange time.
Binance/Kraken ticker responses have no quote timestamp, so they are explicitly marked
received with local receipt time. This establishes response recency, not proof that an
upstream cache or market is fresh. No exchange timestamp is invented.

Valid bid/ask must be finite and positive, bid <= ask, timestamp not in the future,
age <=30 seconds. Two accepted histories must also supply valid quotes. Missing or
rejected quotes do not suppress the historical report, but prevent a scenario without
a quote quorum.

Every accepted quote must pass these limits:

- Bid/ask spread: <=0.2% of its midpoint.
- Cross-source midpoint range: <=0.5% of median midpoint.
- Maximum absolute bid or ask deviation from median analyzed close: <=0.5%.

These are conservative configurable-in-code policy thresholds, not learned optimums.
A blocked scenario is HOLD with trade_plan=null and explicit execution.blocks.

BUY entry is the highest accepted ask with its source and timestamp. SELL entry is
the lowest bid. These are conservative snapshot references, not orders or fill guarantees.
Full depth, lot-size rounding, fees, slippage and gaps are not modeled.

## Indicator definitions

All are calculated per exchange on the synchronized closed-candle window:

- SMA20/SMA50: arithmetic close means.
- RSI14: simple mean gains/losses over 14 differences, not Wilder smoothing.
  Flat history gives 50; no losses gives 100.
- ATR14: simple mean true range over 14 intervals using previous close.
- Volatility: population standard deviation of 24 hourly log returns times sqrt(24),
  expressed in percent. A smooth crash can have near-zero variance.
- Return24h: (last close / close 24 intervals earlier - 1) * 100.
- Drawdown24h: maximum decline from a preceding running closing-price peak over
  25 closes; intrabar high/low drawdown is not measured.
- WorstHour24h: minimum simple return over the last 24 intervals, capped at zero.
- VolumeRatio: last base volume / preceding 20-volume mean, or zero if unavailable.
- Trend: up if close > SMA20 > SMA50; down if the inverse; otherwise mixed.

Reference close, ATR, RSI, volatility and 24h return use medians across sources.
Drawdown and worst hour use the most adverse accepted source.
Historical divergence = close range / median close * 100.

## Three separate risk outputs

risk.data_quality reports history coverage, quote count, recent activity and whether
data-level execution checks passed. It is not a market-return forecast.

risk.market reports heuristic market stress, using the following normalized components:

| Component | Score, capped at 100 |
| --- | --- |
| ATR percent | ATR% / 5 * 100 |
| Daily-scaled volatility percent | volatility% / 10 * 100 |
| Absolute 24h return percent | abs(return24h%) / 10 * 100 |
| Closing-price drawdown percent | drawdown24h% / 10 * 100 |
| Worst hourly loss percent | abs(worst_hour%) / 3 * 100 |

The aggregate is the maximum, rounded to two decimals. A single severe movement cannot
be averaged away by low variance. Labels: normal <30, elevated <60, high >=60.
Normal does not mean safe. Scores and thresholds have not been calibrated historically.

risk.position contains the BUY scenario's planned balance loss and quantity when balance
is supplied, otherwise null. This is a loss-at-stop calculation, not expected loss,
Value at Risk, or probability of loss.

## Decision and sizing

Admission gates: activity, quote readiness, historical divergence <=0.5%, stress <60.
Then unanimous uptrend with median RSI in [45,70] gives BUY; unanimous downtrend with
RSI in [30,55] gives SELL (reduce spot exposure); otherwise HOLD.

For directional scenarios: stop distance 2*ATR; target distance 4*ATR; gross ratio 2:1.
BUY stop below entry, SELL stop above entry. Invalid levels force HOLD.
BUY quantity = min(balance * risk_percent / 100 / stop_distance, balance / current_ask).
risk_percent must be in (0,1]. Planned balance loss percent is returned explicitly.
SELL does not size a leveraged short. HOLD has no levels or invented confidence.

## AI and budget boundary

GPT-6.1 Sol receives a copy of the core report, not decision-making authority.
Generated prose is untrusted commentary; consumers use core for numerical facts.
Disabled, failed, incomplete or budget-exhausted AI preserves deterministic output.

A SQLite BEGIN IMMEDIATE transaction reserves conservative text/output capacity before
sending. Retries are disabled and reservations are retained on success or failure.
The ledger cannot account for other apps or establish OpenAI complimentary-token eligibility.

## Tests and limits

Tests cover hand-computable SMA/RSI/ATR/returns/drawdown/variance examples, NaN time,
zero activity, smooth crashes, quote age/spread/drift, position bounds, source adapters
and AI isolation. CI is configured for Windows and Linux.

This fixes observed correctness failures, not strategy validation. Historical out-of-sample
evaluation, economic costs, threshold calibration and live-input replay remain future work.
