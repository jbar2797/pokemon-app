# Backtesting & Evaluation Specification.md

## Executive Summary

This specification defines **venue‑realistic**, **survivorship‑free**, **walk‑forward** backtests for the Pokémon Pricer signals. We simulate listing‑level execution with probabilistic fills, best‑offer acceptance, relist dynamics, venue‑specific costs, and capacity limits. Evaluation emphasizes **capacity‑adjusted alpha**, **liquidity (sell‑through/time‑to‑sale)**, and **risk**.

---

## 1) Backtest Objectives & Principles

- **Out‑of‑sample fidelity:** Rolling/expanding walk‑forward; no peeking beyond decision time.
- **Realistic execution:** Listing‑level simulator with observed microstructure; fills determined by hazard & acceptance models.
- **Survivorship‑bias‑free:** Universe includes inactive/delisted securities through time.
- **Venue‑aware:** Fees, shipping, returns, slippage curves by venue and price tier.
- **Reproducible:** Seeded randomness; deterministic snapshots for audit.

---

## 2) Data Splitting & Validation

- **Walk‑forward CV:** Windows of length $W_{\text{train}}$, $W_{\text{val}}$, $W_{\text{test}}$ (e.g., 18m/3m/3m), stepped monthly.
- **Temporal purging & embargo:** Purge overlapping label periods; embargo of $h_{\text{max}}$ after feature time.
- **Cross‑venue guard:** Prevent leakage via duplicates across venues (linked by image hash); train/test splits respect lot clusters.
- **Nested tuning:** Hyperparameter Bayesian search on **train+val** only; final model locked before test.
- **Horizon alignment:** Labels use price/ETTS definitions aligned to horizon $h$ with lag $\ell$.

---

## 3) Trade Simulation & Execution

### 3.1 Listing‑Level Simulator

- **State.** For each listing $l$ of security $i$: ask path, watchers, offers, relist chain, seller rating, shipping, fees, timestamps.
- **Decision cadence.** Evaluate daily (and intraday for 7‑day horizon) at venue’s liquid hours.

### 3.2 Fill Logic

1) **Eligibility.** If Action=Buy and capacity allows, submit bid/offer with price $P^{\text{bid}}_{i,t}$ from policy (e.g., midpoint of HFV and ask, constrained by slippage target).
2) **Hazard fill.** Draw fill according to hazard $\hat{h}_{i,t}(\Delta)$ conditioned on bid competitiveness; if multiple competing buyers, reduce hazard via depth.
3) **Best‑offer acceptance.** Logistic model:

$$
\Pr(\text{accept}) = \sigma\!\left(\beta_0 + \beta_1 \frac{P^{\text{offer}}}{P^{\text{ask}}} + \beta_2 \text{days\_live} + \beta_3 \text{watchers} + \beta_4 \text{seller\_rating} \right).
$$

4) **Relist dynamics.** If fail, seller may reprice; simulate according to empirical reprice kernels conditional on fail history.

### 3.3 Costs & Lifecycle

- **Costs:** Listing fees, success fees, payment fees, shipping/insurance, returns/refunds probability by seller rating and price tier.
- **Slippage:** Venue curve $\text{Slip}_v(p)=\alpha_v \ln p + \beta_v$ plus time‑of‑day addend.
- **Partial fills & multi‑lots:** Allocate proportionally; average entry price includes fees.
- **Inventory aging:** Capital charge $\lambda$ per day; forced liquidation after max holding $H_{\text{max}}$ using mark‑to‑market or discounted sale.

---

## 4) Costs, Capacity & Constraints

- **Capacity:** Do not exceed 20% of 30‑day median sold notional per card per day; 10% per seller to avoid signaling.
- **Tick/price:** Respect venue minimum increments; round offers accordingly.
- **Turnover limits:** Strategy‑level monthly turnover cap configurable by profile (Aggressive/Balanced/Conservative).
- **Inventory & cash:** Budget constraints and per‑price‑tier exposure limits.

---

## 5) Risk Model

Multi‑factor risk with style exposures $S_t$ (Era, Character cluster, Art‑style, Price‑tier). Covariance with **Ledoit‑Wolf shrinkage** on weekly returns; **heavy‑tail EVT** for VaR/ES.

Key metrics:

- **Max Drawdown (MDD)**, **Calmar**, **Sharpe/Sortino**, **Tracking Error** vs. style benchmark, **Information Ratio**, **ex‑ante VaR/ES** at 95/99%.

---

## 6) Metrics & Reports

### 6.1 Performance (per horizon)

| Metric | Definition |
|---|---|
| **CAGR** | $(\frac{\text{Ending Equity}}{\text{Starting}})^{1/T}-1$ |
| **Sharpe / Sortino** | Mean / std (downside) of daily net returns |
| **Calmar** | CAGR / MDD |
| **Hit‑Rate** | $\Pr(\alpha^{(h)} > 0)$ |
| **PnL / Trade** | Mean net PnL |
| **Time‑to‑Liquidity** | Median ETTS realized |
| **Turnover** | Notional traded / average equity |
| **Avg Slippage** | Execution − mid / mid |
| **Capacity‑Adj. Alpha** | Alpha penalized by absorption fraction |

### 6.2 Stability & Attribution

| Diagnostic | Definition |
|---|---|
| **Factor IC/IR** | Spearman corr. (IC) of factor vs. forward $\alpha$; IR = IC / IC stdev |
| **Monotonicity** | Check bins of VFS vs. realized alpha |
| **PSI** | Population Stability Index of features |
| **SHAP (constrained)** | Attribution with monotone constraints respected |

### 6.3 Action Calibration

- **Buy/Hold/Sell calibration curves**: predicted utility vs. realized net return.
- **Confusion matrices** under costs (TP = profitable buy, etc.).

---

## 7) Robustness & Anti‑Overfitting

- **White’s Reality Check / SPA** on competing strategies.
- **Block bootstrap** of trade sequences (listing chains as blocks).
- **Placebo factors** (e.g., randomly shifted sentiment) & **dummy cards** (synthetic).
- **Temporal scrambling** within non‑overlapping windows to detect time leakage.
- **Stress windows**: mania (release frenzies), crashes (macro shocks), fee changes.

---

## 8) Statistical Tests & Diagnostics

- **Stationarity:** ADF / Zivot–Andrews on returns & residuals.
- **Change‑point:** Bayesian online (BOCPD) on residual mean/variance.
- **Heteroskedasticity & autocorr:** HAC (Newey‑West), Ljung‑Box on residuals.
- **Forecast comparison:** Diebold‑Mariano across model variants.

---

## 9) Reporting Format

### 9.1 Standard Tables/Charts

- Equity curve, drawdowns, rolling Sharpe/IR, exposure heatmaps, IC decay, calibration plots, confusion matrices, slippage vs. price tier, ETTS distribution, style attribution waterfall.

### 9.2 JSON Schema (Machine‑Readable)

```json
{
  "meta": {
    "strategy_id": "cis_v1",
    "run_id": "2025-08-25T00:00:00Z",
    "seed": 1729,
    "data_range": ["2016-01-01","2025-06-30"],
    "horizons": [7,30,90,180]
  },
  "performance": {
    "overall": {"CAGR": 0.23, "Sharpe": 1.8, "Sortino": 2.6, "Calmar": 1.2, "MDD": -0.19},
    "by_horizon": { "7": {...}, "30": {...}, "90": {...}, "180": {...} }
  },
  "risk": {
    "tracking_error": 0.14,
    "style_exposures": {"WotC": 0.3, "EX": 0.1, "SM": -0.05, "SV": 0.2},
    "VaR_95": -0.06, "ES_95": -0.09
  },
  "capacity": {
    "avg_absorption": 0.12,
    "turnover_monthly": 0.85
  },
  "calibration": {
    "buy_curve": [...],
    "confusion_matrix": {"TP":1234,"FP":321,"TN":2310,"FN":290}
  },
  "diagnostics": {
    "IC": {"HVG": 0.18, "LHA": 0.12, "SPI": 0.09},
    "PSI_flags": ["STZ","SBA"]
  },
  "per_trade": [
    {
      "security_key": "…",
      "decision_time": "2024-11-02T15:00:00Z",
      "action": "Buy",
      "cis": 42.1,
      "vfs": 1.3,
      "confidence": 78,
      "size_fraction": 0.012,
      "entry_price": 740.00,
      "exit_time": "2024-11-22T20:10:00Z",
      "exit_price": 815.00,
      "fees": 54.10,
      "slippage": 0.007,
      "pnl_net": 20.4
    }
  ]
}
```

---

## 10) Pseudocode

### 10.1 Walk‑Forward Backtest Driver

```pseudo
init equity, inventory={}, random_seed
FOR each test window [t2, t3):
  load trained models & conformal calibrators from previous step
  FOR each decision time t in [t2, t3):
    universe = eligible listings at t
    features = feature_store.fetch(universe, t)
    preds = model.predict(features)
    cis, vfs, conf = construct_signals(preds, features)
    actions = policy.decide(cis, vfs, conf, thresholds, capacity)
    orders = execution.create_orders(actions, features)
    fills = simulator.fill(orders, t, hazard_model, acceptance_model, depth)
    update inventory, equity with costs/fees/slippage
    apply inventory aging & forced liquidation rules
  log window metrics, exposures, calibration
aggregate windows -> overall report
```

### 10.2 Simulator Core (Listing‑Level)

```pseudo
function fill(orders, t, hazard_model, acceptance_model, depth):
  fills = []
  FOR order in orders:
    lot = order.listing
    competitiveness = price_to_ask_ratio(order.price, lot.ask)
    h = hazard_model.predict(lot, competitiveness, depth)
    if bernoulli(h * Δt) == 1:
      if venue_supports_best_offer:
        acc_p = acceptance_model.predict(lot, order)
        if bernoulli(acc_p) == 0: continue
      exec_price = realized_exec_price(order, lot, slippage_curve)
      costs = fees(venue, exec_price) + shipping(order)
      fills.append({order_id, exec_price, costs})
  return fills
```

### 10.3 Calibration of Buy/Hold/Sell

```pseudo
function calibrate_thresholds(train_history):
  grid τ_buy, τ_sell, hazard_min by horizon
  for each combination:
    simulate utility-weighted outcomes on validation
    objective = mean(net_return - γ*drawdown_penalty - λ*capital_days)
  choose combination maximizing objective with monotonic regularization over horizons
  return thresholds
```

---

## 11) Sign‑Off Criteria

A release is **approved** when all are met:

- **Information Ratio** ≥ 0.75 (7d/30d) and ≥ 0.5 (90d/180d) after costs.
- **Capacity‑adjusted alpha** ≥ 2.0%/mo at target turnover.
- **Max drawdown** ≤ 25% with Calmar ≥ 0.8.
- **Stable IC:** 12‑month rolling IC ≥ 0.06 for HVG/LHA/SPI.
- **Slippage model error**: mean absolute error ≤ 35% of realized slippage by price tier.
- **Action calibration:** Buy curve AUC ≥ 0.65; confusion matrix cost‑weighted F1 ≥ 0.6.

---

## 12) Assumptions & Open Items

- Listing watcher and best‑offer data accessible and historically backfillable.
- Pop reports timestamped and diffable; latency modeled accurately.
- Vision models for eye‑appeal trained on sufficient labeled data; performance ≥ 0.75 AUC for premium/no‑premium classification.
- Capacity constraints (absorption) approximated by historical sell‑through; market impact outside modeled venues is negligible.
- Returns/refunds distributions stationary within price tiers; if not, add regime splits.

**Open items:**
- Formalize **character index** construction methodology (cap‑weighted by flagship cards vs. equal‑weight by set).
- Validate **shipping/insurance** regional models with carrier quotes.
- Expand BOCPD hyperparameters for release week regimes.
- Human‑in‑the‑loop review workflow for extreme CIS flags before push to prod.

---

## Next Steps (Engineering Checklist)

1. **Create repo modules**: `data_ingest/`, `feature_store/`, `hedonic/`, `models/`, `conformal/`, `simulator/`, `backtest/`, `ui_api/`.
2. **Implement HFV** with monotonic GBM + Huber loss; freeze schema.
3. **Materialize factor library** with explicit lag columns and unit tests (no leakage).
4. **Train first walk‑forward run** (2018–2024) and store OOF predictions for conformal.
5. **Wire simulator** with venue cost/slippage curves; validate on historical execution.
6. **Stand up dashboards** for calibration, drift, and IC decay.
7. **Ship v0.1** CIS/VFS to UI with confidence & drivers; run shadow live for 4–6 weeks.
