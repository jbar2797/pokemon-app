# Signals Methodology – Master Architecture.md

## Executive Summary

**Objective.** Design a hedge‑fund‑grade, explainable signals stack that treats each individual Pokémon card instance (set/language/variant/grade/cert) as a tradable security. The system outputs a **Composite Card Investment Score (CIS)**, a **Value Factor Score (VFS)** (intrinsic value vs. observed price), multi‑horizon forecasts, and calibrated **Buy / Hold / Sell** actions with confidence.

**Approach.** We build a layered architecture:

1) **Canonical security ID & clean room data model** resolving listing‑level events across venues.
2) **Hedonic & structural valuation layer** for intrinsic value with robust M‑estimation under monotonic/shape constraints.
3) **Proprietary factor library** spanning Value, Momentum, Liquidity/Market Impact, Quality/Condition, Rarity/Scarcity, Sentiment/Attention, Seasonality/Event, Cross‑Asset/Relative Value, and Risk Style exposures.
4) **Ensemble modeling**: monotonic gradient boosting + regularized GLMs + sequence models (TFT/TST), blended by a meta‑learner with conformal calibration and drift/change‑point guards.
5) **Signal construction**: state‑space weight adaptation, volatility/liquidity standardization, and confidence derived from predictive intervals and data quality.
6) **Actioning & portfolio sizing**: utility‑aware thresholds, Kelly‑fraction with drawdown cap, capacity/turnover controls, and venue‑aware cost models.

**Why proprietary.** The blueprint fuses domain‑specific microstructure (listing hazard, best‑offer acceptance, relist dynamics), grading/pop‑report mechanics, image‑based eye‑appeal, and cross‑venue spreads with multi‑horizon, regime‑aware ML. Factor specifications, hazard models, and the hedonic fair‑value engine are bespoke to trading‑card markets and tuned for execution reality.

---

## 1) Universe Definition & Identifiers

### 1.1 Canonical Security Key

Each **security** is a unique, tradable entity:

```
SECURITY_KEY :=
  publisher='Pokemon' |
  set_id | subset/parallel_id | card_number | artwork_id |
  language | print_run/edition (1st ed., unlimited, shadowless, etc.) |
  variant (holo, reverse, alt art, promo, stamped) |
  grading_co (PSA/BGS/CGC/ACE/None) |
  grade_numeric (1–10 with half steps) |
  grade_qualifiers (OC, MK, etc., normalized) |
  certification_id (if graded; else null) |
  slab_version (label generation/series) |
  condition_ungraded_bucket (NM/M, LP, etc., when raw)
```

**Listings** reference a SECURITY_KEY plus **lot_id** (unique listing instance), venue, seller, and lifecycle (created, price changes, offers, watchers, sold, withdrawn, relisted).

### 1.2 Corporate‑Action Analogs

- **Regrades / Cross‑grades.** If a cert is cracked or cross‑graded, we record a **CA_REGRADE** action linking `old_cert_id → new_cert_id`, timestamp, and grade movement $\Delta g$.
- **Retops / Label changes.** Record **CA_SLAB_SERIES** when slab/label generation changes (affects eye‑appeal/liquidity).
- **Bundle splits.** **CA_SPLIT_LOT** maps multi‑card lots to child securities with allocation weights.

### 1.3 Bias Controls

- **Survivorship‑free universes.** Securities are included from first observable listing event; delisted or zero‑pop lines persist with null trading until present.
- **Look‑ahead control.** All features use **lagged** inputs; pop changes and sentiment observations are included only after their **ingestion_timestamp**. Price targets use **trade_timestamp** or **listing_mark‑to‑model** strictly after feature timestamps.

---

## 2) Data Engineering

### 2.1 Ingestion & Canonicalization

- **Sources.** eBay, TCGplayer, PWCC, Goldin, Whatnot, Facebook marketplace proxies (if licensed), grading‑co pop reports, Google Trends, X/TikTok/YouTube APIs, calendar of releases/tournaments.
- **Timestamps.** Store `event_time_utc` (nanosecond), `observed_time_utc` (ingestion), and `venue_local_time`.
- **Currencies.** Normalize to USD using WM/Ref mid at 16:00 London or venue‑day VWAP; for intra‑day label creation use nearest hour mid.
- **Fees & shipping.** Venue‑specific fee engine $F_v(p)$, payment fees, estimated shipping/insurance $S_v(w, d)$ by weight/destination; returns/refunds cost model $R_v$.

### 2.2 Deduplication & Identity Resolution

- **Listing de‑dupe.** Fuzzy match on title + image pHash/dHash + seller + time window; hierarchical clustering to collapse cross‑posted duplicates.
- **Image hashing.** pHash (64‑bit), dHash, and perceptual embeddings; Hamming distance thresholds tuned per venue.
- **Canonical text.** Regex + ML NER to extract set, number, language, variant, grade/qualifiers.

### 2.3 Data Quality & Outlier Control

- **Quality tiers:** `A` (verified sold with cert & image), `B` (sold, partial metadata), `C` (ask/offer only), `D` (ambiguous).
- **Outliers/fraud.** Robust scale with MAD and **Huber** loss; price filter if $\frac{|p-\tilde{p}|}{\text{MAD}} > \tau$ with venue/price‑tier adaptive $\tau$. Offer‑to‑ask > 1.5, self‑wash heuristics, zero‑feedback seller risk.

### 2.4 Missing‑Data Imputation

- **Subgrades.** Bayesian hierarchical imputer using era/grade cluster priors.
- **Shipping/fees.** Venue defaults by region and price tier.
- **Eye‑appeal.** Use image embedding model to impute centering/edges when absent; uncertainty propagated as feature variance.

### 2.5 Pop‑Report Tracking

- **Pop diffs.** Daily scrape/diff per card/grade ⇒ $\Delta \text{Pop}_{t}$; derive **submission velocity** and **net pop absorption** (pop increase minus sold count). Lagged by publication time.

### 2.6 Sentiment Signals

- **Search/Social.** Normalize to z‑scores per region; de‑seasonalize weekly pattern; apply exponential decay kernels.
- **Influencer events.** Named entity resolution for creators; shock size = residual vs. AR baseline.

### 2.7 Lag Structures

All features are created with explicit **lags** $(\ell)$ so that no feature at time $t$ depends on data after $t$:
- Most market microstructure features: $\ell=1$ hour.
- Pop, sentiment, calendar: $\ell=1$ day (or publication latency if longer).

---

## 3) Hedonic & Structural Valuation Core

We estimate **Hedonic Fair Value (HFV)** per security $i$ at time $t$ for horizon $h$:

$$
\widehat{V}_{i,t} = f_\theta(X^{\text{hed}}_{i,t}) \quad \text{s.t. }
\begin{cases}
\text{Monotonic: } \partial f/\partial \text{grade} \ge 0 \\
\text{Convexity caps on extreme grades} \\
\text{Robust M-estimation (Huber)} \\
\end{cases}
$$

Inputs $X^{\text{hed}}$ include set/era dummies, language, variant, grade, eye‑appeal embeddings, rarity proxies, recent venue medians, and liquidity terms. We produce a **Value Gap**:

$$
\text{VG}_{i,t} = \frac{\widehat{V}_{i,t} - P^{\text{obs}}_{i,t}}{\widehat{V}_{i,t}},
$$

where $P^{\text{obs}}_{i,t}$ is mid of best ask/offer or last sale depending on context.

---

## 4) Proprietary Feature/Factor Library

**Conventions.**
- Returns: $R_{i,t\to t+h} = \ln\frac{P_{i,t+h}}{P_{i,t}}$.
- Z‑score: $z(x) = \frac{x-\text{median}(x)}{\text{MAD}(x)}$ within cross‑section.
- Expected sign: **+** increases expected return/hazard; **–** decreases.

### 4.1 Value / Intrinsic

| Name (Proprietary) | Intuition | Formal Definition | Inputs | Lag | Freq | Exp. Sign | Horizon | Risk Bucket | Notes |
|---|---|---|---|---:|---:|:--:|:--:|---|---|
| **Hedonic Value Gap (HVG)** | Discount vs intrinsic value | $\text{HVG}_{i,t}=\frac{\widehat{V}_{i,t}-P^{\text{ask}}_{i,t}}{\widehat{V}_{i,t}}$ | HFV, current asks | 1h | 1h | + | 7–90d | Value | Clip to [-1,1] |
| **Shadow Price Alpha (SPA)** | Robust price under M‑estimation | $\text{SPA}_{i,t}=\frac{\tilde{P}^{\text{Huber}}_{i,t}-P^{\text{ask}}_{i,t}}{\tilde{P}^{\text{Huber}}_{i,t}}$ | Venue‑window robust estimator | 1h | 1h | + | 7–30d | Value | Guards against spoof |
| **Grade Elasticity Curve (GEC)** | Marginal $ value$ per grade notch | $\text{GEC}_{i,t} = \frac{\partial \widehat{V}}{\partial g}\big|_{i,t}$ | HFV model | 1d | 1d | + | 30–180d | Quality/Value | Higher GEC ⇒ larger premium for upgrades |
| **Scarcity Pressure Index (SPI)** | Value premium from rarity scarcity | $\text{SPI}_{i,t} = z\!\left(\frac{1}{\text{Pop}_{i,t}}\right)\ +\ z(\text{PrintRunProxy}^{-1})$ | Pop, print proxies | 1d | 1d | + | 30–180d | Rarity | Combine via PCA if needed |
| **Population Pressure (PPI)** | Supply headwinds from pop growth | $\text{PPI}_{i,t} = -z(\Delta \text{Pop}_{i,t}^{30d})$ | Pop diffs | 1d | 1d | + | 30–180d | Rarity | Negative pop change is positive |
| **Liquidity‑Adjusted Value (LAV)** | Discount adjusted for expected slippage | $\text{LAV}_{i,t} = \text{HVG}_{i,t} - \widehat{\text{Slip}}_{i,t}$ | HVG, slippage curve | 1h | 1h | + | 7–30d | Value/Liq | Venue & price‑tier specific |
| **Cross‑Venue Mispricing (CVM)** | Spread to clean venue fair | $\text{CVM}_{i,t}=z\!\left(\frac{P^{\text{ask}}_{i,t}}{\widehat{V}_{i,t}^{(\text{clean})}}-1\right)$ | Clean venue HFV | 1h | 1h | – | 7–30d | Value | Negative CVM (cheap) is positive expected return |

### 4.2 Momentum

| Name | Intuition | Formal Definition | Inputs | Lag | Freq | Sign | Horizon | Risk Bucket | Notes |
|---|---|---|---|---:|---:|:--:|:--:|---|---|
| **Vol‑Scaled TSM (vTSM)** | Time‑series momentum | $\text{vTSM}_{i,t}=\frac{\sum_{k=1}^K w_k R_{i,t-k\delta\to t-(k-1)\delta}}{\hat{\sigma}_{i,t}}$ | Last sales, vol | 1h | 1h | + | 7–30d | Momentum | $w_k \propto e^{-\lambda k}$ |
| **Cross‑Sectional Momentum (XSM)** | Winners vs losers | Rank of $R_{i,t-30\to t}$ cross‑section | Returns | 1d | 1d | + | 30–90d | Momentum | |
| **Listing‑to‑Sale Momentum (LSM)** | Price path in listing lifecycle | $\text{LSM}_{i,t}= -z(\#\text{price cuts}) + z(\text{%↑ reprice})$ | Listing edits | 1h | 1h | + | 7–30d | Microstructure | |
| **Failed‑Sale Reprice Momentum (FRM)** | Stickiness after failures | $\text{FRM}_{i,t}= z\!\big(\Delta P^{\text{ask}}\ \big|\ \text{fail}\to\text{relist}\big)$ | Relist chain | 1h | 1h | – | 7–30d | Momentum | Large cuts after fails ⇒ capitulation |
| **Breakout Regime Score (BRS)** | Detect structural move | $\text{BRS}_{i,t} = \mathbb{1}\{\text{CUSUM/BOCPD change}\}$ | Change‑point stats | 1h | 1h | + | 7–30d | Regime | Combine with vol filter |

### 4.3 Liquidity / Market Impact

| Name | Intuition | Formal Definition | Inputs | Lag | Freq | Sign | Horizon | Risk Bucket | Notes |
|---|---|---|---|---:|---:|:--:|:--:|---|---|
| **Listing Hazard Alpha (LHA)** | Faster sell‑through | $\text{LHA}_{i,t}=\hat{h}_{i,t}(1\,\text{wk}) - \bar{h}_{\text{peer},t}$ | Survival model | 1h | 1h | + | 7–30d | Liquidity | Peer by era/price |
| **Depth Proxy (DEPTH)** | Market depth from active listings | $\text{DEPTH}_{i,t} = \sum_{l} \mathbb{1}\{|P_l-P^{\text{ask}}|<\epsilon\}$ | Order‑like book | 1h | 1h | – | 7–30d | Liquidity | More depth at ask ⇒ harder upside |
| **Watcher Intensity (WIX)** | Demand interest | $\text{WIX}_{i,t}=z(\text{watchers}/\text{days live})$ | Watchers | 1h | 1h | + | 7–30d | Liquidity | Venue‑specific scaling |
| **Bid‑Ask Imbalance (BAI)** | Demand vs supply | $\text{BAI}_{i,t} = \frac{B-A}{B+A}$ | Count of bids $B$ vs asks $A$ | 1h | 1h | + | 7–14d | Liquidity | Proxy on venues without explicit book |
| **Slippage Curve Parameter (SCP)** | Price impact slope | $\text{SCP}_{i,t} = \hat{\alpha}_v$ in $\text{Slip}=\alpha_v \ln p + \beta_v$ | Venue calibration | 1d | 1d | – | 7–30d | Liquidity | Used to discount value |

### 4.4 Quality / Condition

| Name | Intuition | Formal Definition | Inputs | Lag | Freq | Sign | Horizon | Risk Bucket | Notes |
|---|---|---|---|---:|---:|:--:|:--:|---|---|
| **Eye‑Appeal Score (EAS)** | Visual premium | $\text{EAS}_{i,t}=z(\text{emb}_\text{aesthetic}\cdot w)$ | Image embeddings | 1d | 1d | + | 30–180d | Quality | Trained on premium outcomes |
| **Centering Score (CTR)** | Better centering ⇒ premium | $\text{CTR}_{i,t}=1-\frac{|L-R|}{W}$ (similarly vertical) | Vision model | 1d | 1d | + | 30–180d | Quality | |
| **Surface Defect Score (SDS)** | Fewer defects | $\text{SDS}_{i,t}=-z(\text{defect count})$ | Vision model | 1d | 1d | + | 30–180d | Quality | |
| **Subgrade Vector Coherence (SGC)** | Balanced subgrades price better | $\text{SGC}_{i,t}=-\text{Var}(\text{subgrades})$ | BGS/CGC subs | 1d | 1d | + | 30–180d | Quality | |
| **Upgrade Probability (UPG)** | Chance to bump grade | $\text{UPG}_{i,t}=\Pr(\Delta g>0\mid \text{features})$ | Quality model | 1d | 1d | + | 90–180d | Quality | Guides cross‑grade plays |

### 4.5 Rarity / Scarcity

| Name | Intuition | Formal | Inputs | Lag | Freq | Sign | Horizon | Bucket | Notes |
|---|---|---|---|---:|---:|:--:|:--:|---|---|
| **Vaulted Supply Indicator (VSI)** | Supply withdrawn from market | $\text{VSI}_{i,t}=\mathbb{1}\{\text{vault phase}\}$ | Release db | 1d | 1d | + | 90–180d | Rarity | |
| **Cert‑Series Rarity (CSR)** | Short‑run label rarity | $\text{CSR}_{i,t}=z(\text{label\_series rarity})$ | Grader series | 1d | 1d | + | 30–90d | Rarity | |
| **Era Scarcity Premium (ESP)** | Older eras premium | $\text{ESP}_{i,t}=\beta_{\text{era}}$ from HFV | HFV | 1d | 1d | + | 90–180d | Style | Treated as style exposure |

### 4.6 Sentiment / Attention

| Name | Intuition | Formal | Inputs | Lag | Freq | Sign | Horizon | Bucket | Notes |
|---|---|---|---|---:|---:|:--:|:--:|---|---|
| **Search Trend Z (STZ)** | Demand lift | $\text{STZ}_{i,t}=z(\text{GoogleTrends}_{i,t})$ | Trends | 1d | 1d | + | 7–30d | Sentiment | |
| **Buzz Acceleration (SBA)** | Second derivative of attention | $\text{SBA}_{i,t}=\Delta^2 \text{Buzz}_{i,t}$ | Social volume | 1h | 1h | + | 7–14d | Sentiment | |
| **Influencer Shock Residual (ISR)** | Impact beyond baseline | $\text{ISR}_{i,t} = \text{Buzz}_{i,t}-\widehat{\text{Buzz}}^{\text{AR}}_{i,t}$ | AR residual | 1h | 1h | + | 7–14d | Sentiment | |
| **Event Catalyst Proximity (ECP)** | Upcoming drivers | $\text{ECP}_{i,t}=e^{-\kappa \cdot \text{days\_to\_event}}$ | Calendar | 1d | 1d | + | 7–30d | Event | |

### 4.7 Seasonality / Event

| Name | Intuition | Formal | Inputs | Lag | Freq | Sign | Horizon | Bucket | Notes |
|---|---|---|---|---:|---:|:--:|:--:|---|---|
| **Holiday Lift (HOLI)** | Holiday demand | $\text{HOLI}_{t}=\text{seasonal index}_{\text{holiday},t}$ | Seasonal model | 1d | 1d | + | 7–30d | Seasonality | |
| **Release Window Overhang (RWO)** | New supply pressure | $\text{RWO}_{i,t}=z(\text{days since release}^{-1})$ | Releases | 1d | 1d | – | 7–30d | Seasonality | |
| **Anniversary Effect (ANNV)** | Set anniversaries | $\text{ANNV}_{t}=\cos(2\pi \cdot \text{age}/\text{year})$ | Calendar | 1d | 1d | + | 7–30d | Seasonality | |

### 4.8 Cross‑Asset / Relative Value

| Name | Intuition | Formal | Inputs | Lag | Freq | Sign | Horizon | Bucket | Notes |
|---|---|---|---|---:|---:|:--:|:--:|---|---|
| **Character Ladder Spread (CLS)** | Value vs character tier | $\text{CLS}_{i,t}=z\big(\frac{P_{i,t}}{\text{char\,index}_t}\big)$ | Character index | 1d | 1d | – | 30–90d | Relative | |
| **Cross‑Language Parity Dev. (CLPD)** | Language spread | $\text{CLPD}_{i,t}=\frac{P^{\text{lang}=\ell}_{i,t}}{P^{\text{lang}=\text{EN}}_{j,t}}-1$ | Matched art | 1d | 1d | mean‑revert | 30–90d | Relative | |
| **Grade Ladder Arbitrage (GLA)** | Adjacent grade parity | $\text{GLA}_{i,t}=\frac{\widehat{V}_{g+1}-P_{g}}{\widehat{V}_{g}}$ | HFV by grade | 1d | 1d | + | 30–90d | Relative | Guides crack/resub |

### 4.9 Risk Style Factors (Exposures)

Style exposures (not alphas): Era (WotC/EX/DPt/SM/SS/SV), Character clusters, Art‑style clusters, Price‑tier styles. Estimated via constrained regressions:

$$R_{i,t\to t+h} = \alpha_{i,h} + \beta^\top_{i} S_{t} + \epsilon_{i,t},$$

where $S_t$ is the vector of style returns. We **neutralize** CIS to non‑target style exposures for portfolio construction.

---

## 5) Labeling & Targets

We define multi‑horizon targets $h \in \{7,30,90,180\}$ days.

1. **Realized alpha vs HFV** (net of fees/slippage):

$$
\alpha^{(h)}_{i,t} = \ln\frac{P^{\text{exit}}_{i,t+h}}{\widehat{V}_{i,t}} - c_v(P, q) - \text{Slip}_v(P),
$$

with $P^{\text{exit}}$ = realized sale (or mark‑to‑model at $t+h$ if unsold) and $c_v,\ \text{Slip}_v$ venue/size costs.

2. **Sell‑through within time‑at‑risk** via discrete‑time hazard:

$$
y^{\text{sell}}_{i,t}(h) = \mathbb{1}\{\text{sold by }t+h\}.
$$

3. **Expected time‑to‑sale (ETTS).** From survival model $\hat{h}_{i,\tau}$:

$$
\widehat{\text{ETTS}}_{i,t} = \sum_{\tau \ge 0} \Pr(T>\tau).
$$

### Utility‑Aware Action Labels

Define expected utility for action $a \in \{\text{Buy},\text{Hold},\text{Sell}\}$:

$$
U_a = \mathbb{E}[ \alpha^{(h)}_{i,t} ]
- \gamma \cdot \text{DownsideRisk}_{i,t}
- \lambda \cdot \text{CapitalDays}_{i,t}
- \mu \cdot \text{InventoryRisk}_{i,t},
$$

with horizon‑specific $(\gamma,\lambda,\mu)$. Labels:

- **Buy** if $U_\text{Buy} - U_\text{Hold} > \tau^{\text{buy}}_h$ and $\hat{h}_{i,t}(h)>\underline{h}_h$.
- **Sell** if $U_\text{Sell} - U_\text{Hold} > \tau^{\text{sell}}_h$.
- **Hold** otherwise.

Default thresholds: $\tau^{\text{buy}}_{7,30,90,180} = \{0.8\%, 1.5\%, 2.5\%, 3.5\%\}$ net; $\underline{h}_{7,30}=\{0.35,0.55\}$.

---

## 6) Modeling & ML Stack

### 6.1 Base Learners

- **Monotonic Gradient Boosting (GBM)** (e.g., LightGBM/XGBoost with monotone constraints on `HVG`, `LAV`, `GEC`, etc.).
- **Regularized GLMs** (Elastic Net) for linear explainability and stability on sparse securities.
- **Sequence Model**: **Temporal Fusion Transformer (TFT)** or Temporal Convolution/TST for listing microstructure and sentiment sequences.

Targets learned: $\alpha^{(h)}$, $\Pr(\text{sell by }h)$, $\text{ETTS}$.

### 6.2 Meta‑Learner & Blending

Stacked generalization with Ridge/Elastic Net meta‑learner, trained on out‑of‑fold predictions. Per‑horizon weights; **Bayesian hierarchical partial pooling** across rare securities to borrow strength at character/set/era level.

### 6.3 Guardrails

- **Lagging & leakage tests**: backshift features by minimum latency; assert no target inclusion.
- **Monotonic constraints** on Value/Quality interpretable features.
- **Conformal prediction** (inductive, normalized residuals) to yield $[L_{i,t}^{(h)}, U_{i,t}^{(h)}]$ for net return and for sell‑through probability.
- **Drift detection** (ADWIN, KS on residuals) and **online change‑point** (BOCPD) to re‑weight models.
- **Feature stability filter** using rolling **IC** and **PSI**.

### 6.4 Hyperparameter Search

Bayesian optimization (TPE/SMBO) with early stopping on **rolling walk‑forward** validation, objective: maximize **capacity‑adjusted IR** (Information Ratio net of capacity penalty).

---

## 7) Signal Construction

### 7.1 Composite Card Investment Score (CIS)

For horizon $h$ we compute **alpha** $\widehat{\alpha}^{(h)}_{i,t}$, **sell hazard** $\hat{h}^{(h)}_{i,t}$, and **downside vol** $\hat{\sigma}^{\downarrow}_{i,t}$. The **state‑space** weight vector $w_t$ evolves via a Kalman filter to adapt to regimes:

$$
\text{CIS}_{i,t}^{(h)}
= w_{t,1}\,\widehat{\alpha}^{(h)}_{i,t}
+ w_{t,2}\,\hat{h}^{(h)}_{i,t}
- w_{t,3}\,\hat{\sigma}^{\downarrow}_{i,t}
- w_{t,4}\,\widehat{\text{Slip}}_{i,t}.
$$

**Normalization.** Cross‑sectional z‑score then logistic squash to $[-100,100]$ for UI.

### 7.2 Value Factor Score (VFS)

Primary, interpretable value score:

$$
\text{VFS}_{i,t} = \text{z}\!\left(\text{HVG}_{i,t}\right) + \eta_1 \text{z}(\text{LAV}_{i,t}) + \eta_2 \text{z}(\text{SPI}_{i,t}) - \eta_3 \text{z}(\text{PPI}_{i,t}),
$$

with default $(\eta_1,\eta_2,\eta_3)=(0.5,0.3,0.2)$. Displayed separately and included in CIS via monotone link.

### 7.3 Confidence Score (0–100)

From conformal interval width $W_{i,t}^{(h)}=U-L$, normalized by cross‑section median $W^{\text{med}}_h$, data quality $Q_{i,t}\in[0,1]$, and coverage $C_{i,t}$:

$$
\text{Conf}_{i,t}^{(h)} = 100 \cdot \left[
0.6 \left(1 - \min\left(1, \frac{W_{i,t}^{(h)}}{W^{\text{med}}_h}\right)\right)
+ 0.25 Q_{i,t} + 0.15 C_{i,t}
\right].
$$

### 7.4 Winsorization & Stabilization

Winsorize factor z‑scores at $\pm 3$, apply **volatility targeting**: scale CIS by inverse recent cross‑sectional volatility to stabilize ranks.

---

## 8) Portfolio Sizing & Actioning

### 8.1 Position Sizing

Fractional **Kelly with drawdown cap** on independent trade bets:

$$
f^*_{i} = \min\left\{ \bar{f},\ c \cdot \frac{\widehat{\alpha}^{(h)}_{i,t}}{\hat{\sigma}^2_{i,t}} \cdot \rho_{i}\right\},
$$

where $c\in[0.25,0.5]$ (fractional Kelly), $\rho_i = \sqrt{1-R^2_{i}}$ reduces sizing by style correlation, and $\bar{f}$ caps per security (e.g., 5% of bankroll or venue capacity). **Ageing**: if not filled within ETTS × 1.5, reduce $f$ by 50%.

### 8.2 Capacity & Turnover

- **Capacity** per card from **DEPTH** and historical absorption; cap projected daily buy notional ≤ 20% of 30‑day median sold notional.
- **Turnover** targets by horizon: 7d: 150–250%/mo; 30d: 60–120%/mo; 90d+: ≤ 40%/mo.

### 8.3 Execution & Costs

- Venue‑aware **slippage curves** by price tier, time‑of‑day; include fees $F_v$ and shipping/insurance $S_v$; expected best‑offer acceptance probability to model fills.

---

## 9) Governance & Monitoring

- **Dashboards.** Hit‑rate per horizon, realized slippage vs. model, sell‑through lead/lag, factor IC decay, feature drift PSI, action confusion matrices under costs.
- **Alarms.** Residual KS/ADWIN drift, capacity breach, drawdown breach, estimator instability.
- **Auto‑rollback.** If IR over last 250 trades < –0.25 or drift persists 3 days, fall back to conservative rule‑based VFS/HVG actions.

---

## 10) UX Output Contract

**Per card (all users):**
- `CIS` (–100 to 100), `VFS` (–3 to +3), **Action** (Buy/Hold/Sell), **Confidence** (0–100%), **Expected net return (h)**, **Expected time‑to‑sale (ETTS)**, **Top 3 drivers** with sign (e.g., HVG↑, LHA↑, PPI↓), **Data‑quality badge** (A/B/C/D).

**Premium panel:**
- Full factor vector & histories, style exposures, backtest slice by horizon/venue/grade, risk stats, and scenario analysis (shock SPI, fees, sentiment).

---

## 11) Pseudocode

### 11.1 Data Preprocessing

```pseudo
FOR each venue v IN sources:
  ingest raw_events
  normalize timestamps -> UTC
  fx_normalize prices to USD
  extract metadata via NER + regex
  compute image hashes + embeddings
  resolve SECURITY_KEY
  deduplicate listings via hash+seller+time clustering
  compute fees S_v, F_v, slippage params
  assign data_quality tier

join with pop_reports (lagged), sentiment (lagged), calendar
compute rolling stats (vol, medians) per SECURITY_KEY
materialize feature store with explicit lags
```

### 11.2 Label Creation

```pseudo
FOR horizon h in {7,30,90,180}:
  FOR each listing i at decision_time t:
    compute HFV_t
    compute realized exit price P_exit by t+h (else mark-to-model)
    alpha_h = log(P_exit / HFV_t) - fees - slippage
    sold_h = 1 if sold by t+h else 0
    ETTS from survival model fit on historical lifetimes
    store targets with observation_time = t, enforce embargo window
```

### 11.3 Model Training (Walk‑Forward)

```pseudo
define rolling windows: train=[t0, t1), validate=[t1, t2), test=[t2, t3)
FOR each window:
  fit HFV with robust, monotone constraints
  fit base learners: GBM, GLM, Sequence on train
  generate OOF predictions on validate
  fit meta-learner on validate OOF
  conformal calibrate intervals using validate residuals
  evaluate on test; log metrics; update drift detectors
  advance window by step Δ
```

### 11.4 Signal Construction

```pseudo
FOR each card i at time t:
  predict alpha_h, hazard_h, downside_vol
  update state-space weights w_t via Kalman using recent performance
  CIS_h = w1*alpha_h + w2*hazard_h - w3*downside_vol - w4*slippage
  VFS = z(HVG) + 0.5*z(LAV) + 0.3*z(SPI) - 0.2*z(PPI)
  compute conformal interval [L,U] -> Confidence
  choose Action via utility thresholds
```

---

## 12) Assumptions Log

- Pop reports provide daily/weekly snapshots with reliable timestamps; publication latency ≤ 24h.
- Access to listing watchers/bids and best‑offer details is available via API or scrape.
- Image quality sufficient for centering/defect inference on ≥70% of graded cards.
- Venue fees, payment fees, and shipping costs are estimable within ±10% error by price tier.
- Print run proxies exist via set rarity tiers and public proxies; precise print numbers may be unavailable—handled via proxies and clustering.
- Calendar of releases/tournaments/influencer events is maintained and time‑stamped.

**Impact:** If any of the above is materially false, factor reliability and calibration will shift; guardrails (drift, conformal) limit live degradation but backtest realism depends on these assumptions.

---
