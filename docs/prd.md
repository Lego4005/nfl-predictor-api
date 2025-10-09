# PRD — Expert Council Betting System (Postgres + pgvector hot path, Neo4j thought lattice)

## 0) Purpose & Scope

Deliver a coherent, testable v1 that:

* Keeps **experts sovereign** (each predicts 83 categories + chooses stakes).
* Uses **Postgres + pgvector** for fast recall, buckets, staking, grading, and council aggregation.
* Uses **Neo4j** as a write-behind **thought lattice** for provenance (Thought → Assertion → Outcome).
* Produces a **single coherent platform slate** (scores, totals, props) with a final **W–L** decision, without editing expert outputs.

**Out of scope (v1):** real sportsbook integrations, live-data ingestion, UI polish beyond basic admin/JSON endpoints.

---

## 1) System Overview

### Hot path (pre/post game)

* **Pre-game**: experts emit 83 assertions + stakes → store assertions; create bet tickets; fetch memories via pgvector; council selects/weights top-5.
* **Platform output**: weighted aggregation → **coherence projection** (least-squares nudge) → final slate + W–L.
* **Post-game**: grade assertions; settle tickets; update bankrolls, buckets, calibration; record learning and weight adjustments (audit).

### Cold path (write-behind)

* Emit Neo4j nodes/edges for explainability: `(Decision) — HAS_ASSERTION — (Assertion)`, `(Thought) — USED_IN → (Assertion)`, `(Assertion) — EVALUATED_AS → (Game)`.

---

## 2) Data Model (Postgres)

### 2.1 Canonicals & Memories (already set)

* `teams(team_id, canonical_key, display_name, …)`
* `team_aliases(alias → team_id)`
* `expert_episodic_memories`
  Columns: `memory_id, expert_id, game_id, home_team, away_team, season, week, game_date, …, game_context_embedding, prediction_embedding, outcome_embedding, combined_embedding, embedding_status`.
* **Vector search RPC**: `search_expert_memories(p_expert_id, p_query_embedding, p_match_threshold, p_match_count, p_alpha)` blending similarity + 90-day decay.

### 2.2 Buckets (fast counters)

* `team_knowledge(id, expert_id, team_id, [category?], confidence_level, sample_size, accuracy_rate, knowledge_embedding)`
  *Optionally add* `category text` for per-category tallies.
* `matchup_memories(id, expert_id, home_team, away_team, matchup_key_sorted (generated), [category?], games_analyzed, predictions_made, predictions_correct, accuracy, matchup_embedding)`
  Constraints: `unique(expert_id, home_team, away_team)`; index on `(expert_id, matchup_key_sorted)`.

### 2.3 Predictions & Outcomes

* **Bundle** (if not present): `expert_predictions(expert_id, game_id, predicted_winner, home_win_prob, away_win_prob, overall_confidence, recency_alpha_used, overall_score)` PK `(expert_id, game_id)`.
* **Assertions (83 per expert+game)**

  ```sql
  create table expert_prediction_assertions(
    assertion_id uuid pk default gen_random_uuid(),
    expert_id text, game_id text,
    category text, subject text,            -- 'home','away','player:ID','game'
    pred_type text check (pred_type in ('binary','enum','numeric')),
    pred_value_numeric numeric, pred_value_text text,
    confidence numeric check (confidence between 0 and 1),
    why_weights jsonb, top_memories jsonb,  -- [{memory_id,weight}]
    created_at timestamptz default now(),
    unique (expert_id, game_id, category, subject)
  );
  create table assertion_outcomes(
    assertion_id uuid pk references expert_prediction_assertions on delete cascade,
    is_correct boolean, error numeric, grade numeric, brier numeric, details jsonb
  );
  ```

### 2.4 Staking & Bankroll (expert-driven)

```sql
create table expert_bankroll(
  expert_id text primary key, season int,
  starting_bankroll numeric default 100.0,
  bankroll numeric default 100.0,
  is_active boolean default true,
  updated_at timestamptz default now()
);
create table expert_bets(
  bet_id uuid pk default gen_random_uuid(),
  expert_id text, game_id text, assertion_id uuid,
  category text, stake_units numeric check(stake_units>=0),
  odds_type text check (odds_type in ('american','decimal','fraction')),
  odds_value text, settled boolean default false,
  outcome text, pnl numeric default 0, placed_at timestamptz default now(), settled_at timestamptz
);
```

### 2.5 Learning & Calibration (per expert+category)

```sql
create table expert_factor_weights(
  id uuid pk default gen_random_uuid(),
  expert_id text, category text, factor text, weight numeric check(weight>=0),
  valid_from timestamptz default now(), valid_to timestamptz,
  unique(expert_id, category, factor, valid_from)
);
create table weight_adjustments(
  id uuid pk default gen_random_uuid(),
  expert_id text, category text, factor text,
  old_weight numeric, new_weight numeric, signal numeric,
  method text, reason text, created_at timestamptz default now()
);
create table expert_category_calibration(
  id uuid pk default gen_random_uuid(),
  expert_id text, category text unique,
  alpha numeric default 1.0, beta numeric default 1.0,  -- binary/enum
  mu numeric default 0.0, sigma numeric default 1.0,    -- numeric
  updated_at timestamptz default now()
);
```

### 2.6 Council & Metrics

```sql
create table expert_family_metrics(
  expert_id text, family text,      -- 'markets','totals','quarters','team_props','game_props','player_props','live'
  games int, roi numeric, acc numeric, brier numeric, sigma numeric,
  updated_at timestamptz, primary key(expert_id, family)
);
create table council_selections(
  id uuid pk default gen_random_uuid(),
  game_id text, family text,
  expert_id text, seat_rank int, seat_score numeric, weight numeric,
  created_at timestamptz default now()
);
```

---

## 3) Neo4j Thought Lattice (write-behind)

**Nodes**

* `(:Expert {expert_id})`
* `(:Game {game_id, season, week, date, home, away, winner, final_home, final_away})`
* `(:Decision {decision_id, expert_id, game_id, recency_alpha, overall_confidence, overall_score, created_at})`
* `(:Assertion {assertion_id, category, subject, pred_type, value, confidence})`
* `(:Thought {memory_id, type, summary, created_at})`  // mirrors episodic memory
* `(:Reflection {reflection_id, lesson, delta_conf, created_at})`

**Rels**

* `(Expert)-[:PREDICTED]->(Decision)-[:FOR]->(Game)`
* `(Decision)-[:HAS_ASSERTION]->(Assertion)`
* `(Thought)-[:USED_IN {category, rank, score, weight}]->(Assertion)`  // per-category “why”
* `(Assertion)-[:EVALUATED_AS {is_correct, error, grade}]->(Game)`
* `(Expert)-[:LEARNED_FROM]->(Reflection)-[:ABOUT]->(Game)`

**Constraints**

* Unique on ids for all five node types.

---

## 4) Core Algorithms

### 4.1 Memory retrieval (pre-game)

* Build short query text from context; embed → `search_expert_memories` RPC with `alpha` tuned by persona + season phase.
* Return top-K episodic `memory_id`s + scores; also load `team_knowledge`, `matchup_memories`.

### 4.2 Expert output (no edits)

Experts emit 83 assertions JSON with fields: `category, subject, pred_type, value, confidence, stake_units, odds{type,value}, why[{memory_id,weight}]`.

### 4.3 Council selection

* **Seat score per expert per family**:

  ```
  S = w1*ROI_recent + w2*Accuracy_recent + w3*Calibration + w4*(bankroll/starting) + w5*stake_intensity + w6*diversity_bonus
  ```
* Pick top-5 per family; store to `council_selections`.

### 4.4 Council weighting & aggregation (no mind editing)

* Weights per seated expert & category:
  `w_E ∝ stake_units_E(cat) * skill_E(family) * calibrator_E(family)`; normalize.
* Combine:

  * Binary/enum: **weighted log-odds average**.
  * Numeric: **precision-weighted mean** (use `σ` from calibration if available).

### 4.5 Coherence projection (platform only)

* Enforce constraints: `home+away=total`, `quarters sum to halves sum to total`, `winner ↔ margin`, team/prop consistency.
* Solve small least-squares projection to minimally adjust platform outputs; **do not alter experts’ stored assertions**.

### 4.6 Grading (post-game)

* **Binary/enum**: exact; store `brier`.
* **Numeric**: `grade = exp(-(abs(pred-actual)/sigma_cat)^2)` with category-specific sigmas.
* Write to `assertion_outcomes`; compute **overall_score** (weighted category average) on bundle.

### 4.7 Settlement (bankroll)

* Parse odds; compute `pnl` per bet (`win/loss/push`); update `expert_bankroll`.
* If `bankroll <= 0` → `is_active=false` (out for season).

### 4.8 Learning updates (no mind editing; update priors)

* **Calibration**:

  * Binary/enum → Beta: `alpha += outcome`, `beta += (1-outcome)`.
  * Numeric → EMA: `mu ← (1−η)μ + η*(actual−pred)`, `σ ← (1−η)σ + η*|resid|`.
* **Factor weights (per category)**: MWU on factors used for that assertion:
  `w_i' ∝ w_i * exp(β * S * contrib_i)` with `S = 2*grade−1`; normalize.
  Persona controls `β` & `η`, plus season-phase multipliers.
  Append `weight_adjustments`; close/open `expert_factor_weights` slices.

---

## 5) Orchestrator Responsibilities (governor, not editor)

* Enforce **submission guardrails** (soft caps): max units per game (reject excess tickets; experts can resubmit).
* **Eligibility** for council seating (not output editing): inactive bankroll, insufficient recent sample, calibration blow-up quarantine.
* Maintain persona **alpha/β/η** policies (short-memory vs long-memory experts; early/mid/late season).

---

## 6) APIs (minimal)

* `POST /expert/predictions` — stores bundle + 83 assertions + creates `expert_bets`.
* `GET /context/:expert_id/:game_id` — returns top-K episodic, team_knowledge, matchup_memories.
* `POST /council/select/:game_id` — runs seat selection; returns seated experts & weights.
* `GET /platform/slate/:game_id` — returns aggregated + **cohered** platform slate + final W–L.
* `POST /settle/:game_id` — grades assertions, settles tickets, updates bankrolls/buckets.
* `GET /leaderboard` — bankroll, ROI, recent accuracy; council seat streaks.

---

## 7) Metrics & Dashboards

* **Latency**: vector retrieval p95 < 100ms, council aggregation < 50ms, projection < 20ms.
* **Quality**: per category MAE/grade; Brier/logloss; calibration curves.
* **Economics**: bankroll trajectories, ROI by family, stake intensity heatmap.
* **Council**: seat share %, residual correlation matrix (diversity), contribution weights per family.
* **Learning**: factor weight drift timelines; σ and μ evolution per expert+category.

---

## 8) Acceptance Criteria (v1)

1. **Sovereign experts**: system stores exactly 83 assertions + stakes; no edits.
2. **Fast recall**: vector RPC returns K=10 in <100ms p95 with recency blend.
3. **Coherent platform slate**: aggregated + projected outputs satisfy all constraints; final W–L present.
4. **Bankroll realism**: bets settled; bankroll updates; experts can bust out.
5. **Council**: top-5 seat selection logged; weights applied per category; diversity bonus in effect.
6. **Learning**: calibration & MWU persisted; weight_adjustments logged.
7. **Neo4j**: write-behind creates Decision, Assertion, USED_IN, EVALUATED_AS for at least one tested game.

---

## 9) Rollout Plan

1. **DB migrations**: assertions, outcomes, bets, bankroll, factor_weights, calibrations, council tables.
2. **Embedding worker**: ensure `expert_episodic_memories` all `combined_embedding` ready.
3. **Services**: memory retrieval wrapper → council selector → aggregator → projection → settlement → reconciliation.
4. **Write-behind**: small worker to emit Neo4j nodes/edges post-settlement.
5. **Smoke test**: 5 games × 5 experts: verify coherence, council weights, bankroll deltas, vector p95, grading.
6. **Scale-up**: full week, all 15 experts; enable dashboards.
7. **Docs**: JSON contract for expert outputs; grading rubric table (sigmas); persona rates (α/β/η); council weight formula.

---

## 10) Test Plan (high level)

* **Unit**: odds parsing & settlement; numeric/binary grading; projection constraints; MWU update math; RPC wrapper.
* **Integration**: end-to-end (store assertions → aggregate → project → grade → settle → update buckets).
* **Property tests**: projection never flips winner if margin >> epsilon; totals/quarters always sum; bankroll never < −float tolerance.
* **Performance**: vector RPC under load; aggregation/projection latency; settlement throughput.
* **Neo4j**: idempotent merges; “why trail” query returns the used thoughts per assertion.

---

### Notes

* Experts remain fully **sovereign** (content + stake).
* Council **selects & weights**, never edits.
* Platform **coheres** only the final combined slate.
* Learning adjusts **calibration and factor weights**, not the historical opinions.
* Neo4j is **optional** at runtime, **valuable** for provenance and analytics.

If you want, I can attach a companion “Rubric & Sigma Registry” (83 rows) and a sample “Why Trail” Cypher + two SQL admin queries to seed your first validation run.


Totally makes sense — let the experts *be* experts, build their own episodic memories, and grow week-by-week across teams and matchups. Here’s a tight, “copy-into-the-PRD” addendum that stitches everything we agreed into a concrete ingest + training recipe, with exact prompts and a sane number of AI calls.

---

# PRD Addendum — Ingestion, Prompts, and Call Budget

## A) Rollout plan (start small, scale up)

* **Pilot cohort**: 4 experts (e.g., `conservative_analyzer`, `risk_taking_gambler`, `contrarian_rebel`, `momentum_rider`).
* **Data pass 1 (learning)**: Ingest 2020 → 2023 chronologically. Experts can “predict” (generated assertions) but their *stakes can be 0* during the backfill if you want to save cycles; reflections still form memories.
* **Data pass 2 (simulate betting)**: 2024 season with **real stakes** from each expert, settled vs truth (bankrolls move).
* **Then**: Run through 2025 YTD (up to **2025-10-07**) the same way.
* **Neo4j**: write-behind enabled from Day 1 (Decision → Assertion → Thought → Outcome), but **not** in the hot path.

> Experts remain sovereign; no scripts “fix” their minds. Council selects/weights later.

---

## B) Per-game pipeline (for each expert)

**0. Load context**
Pull game row (like your sample), normalize teams via `team_aliases`, compute a short context string.

**1. Retrieve memories (no LLM)**

* Vector RPC: `search_expert_memories(expert_id, query_embedding, k=7, alpha by persona/season)`
* Buckets: `team_knowledge` (home & away), `matchup_memories` (role-aware).

**2. Generate 83 assertions + stakes (1 LLM call)**

* System prompt = persona; User payload = context + top memories + buckets (templates below).
* Output: the full **83-assertion JSON** with `stake_units` and `odds` per assertion (experts pick amounts themselves).

**3. Store**

* Insert assertions, create `expert_bets` (exact stakes), write episodic **Thought** memory row (with top memories used).

**4. Platform layer (no LLM)**

* Council (optional in pilot) selects/weights.
* Coherence projection applies **only** to platform combined slate (never edits experts).

**5. Post-game grading (0–1 LLM call)**

* Deterministic grading & settlement in code.
* **Optional** 1 LLM reflection per expert to produce a human-readable “what I learned” note + tag which factors mattered; store as `personal_learning` Thought.

> **Call budget per expert per game:** **1** LLM (predictions) + **0–1** LLM (reflection) ⇒ **1–2** calls.
> For 4 experts, that’s ~4–8 calls per game. You can run reflections weekly instead of per-game to halve calls.

---

## C) Exact prompt templates

### C1) System (persona) — used for *every* expert

```
You are {EXPERT_NAME} ({expert_id}), an NFL prediction expert.

PERSONALITY TRAITS:
- Risk tolerance: {risk_tolerance}/100
- Analytics trust: {analytics_trust}/100
- Market trust: {market_trust}/100
- Contrarian tendency: {contrarian}/100
- Temporal stance: half_life_days={half_life_days}; seasonal modifiers={season_mods}

DECISION STYLE:
- Weight factors using your personality vector (momentum, weather, market, injuries, rivalry, pace, coaching, travel/rest).
- Use recency with alpha={recency_alpha_used} (already computed in context).
- Do NOT copy anyone else. Your stake shows your conviction.

OUTPUT RULES:
- Emit EXACT JSON that matches the schema provided in the User message.
- 83 predictions required: each with {category, subject, pred_type, value, confidence, stake_units, odds, why[]}.
- stakes_units can be 0 (pass) or any positive float. You are fully responsible for sizing.
- No prose outside JSON.
```

### C2) User payload (context + memories + schema)

```json
{
  "game": {
    "game_id": "{game_id}",
    "season": {season},
    "week": {week},
    "home_team": "{HOME}",
    "away_team": "{AWAY}",
    "weather": {"temp_f": {temp_or_null}, "wind_mph": {wind_or_null}, "desc": "{desc_or_null}"},
    "market": {
      "spread_home": {spread_home}, "total": {total_line},
      "moneyline_home": {home_ml}, "moneyline_away": {away_ml}
    },
    "meta": {"div_game": {div_game}, "roof":"{roof}", "surface":"{surface}"}
  },
  "recency_summary": {
    "alpha": {recency_alpha_used},
    "top_memories": [
      {"memory_id":"{mem1}","similarity":0.83,"recency":0.74,"combined_score":0.79,"note":"..."},
      {"memory_id":"{mem2}","similarity":0.79,"recency":0.68,"combined_score":0.75,"note":"..."}
    ]
  },
  "team_knowledge": {
    "home": [{ "knowledge_type":"home_advantage","confidence":0.72,"note":"..." }],
    "away": [{ "knowledge_type":"weather_impact","confidence":0.81,"note":"..." }]
  },
  "matchup_memory": { "role_aware": { "accuracy":0.61,"games_analyzed":14,"notes":["..."] } },
  "schema": {
    "predictions": [
      {
        "category": "spread_full_game",
        "subject": "home|away",
        "pred_type": "numeric",
        "value": -2.5,
        "confidence": 0.71,
        "stake_units": 2.0,
        "odds": { "type":"american","value": -110 },
        "why": [ {"memory_id":"mem_abc","weight":0.34} ]
      }
      // ... 82 more, covering all categories in registry
    ]
  }
}
```

> The orchestrator injects `recency_alpha_used` based on persona + season phase (e.g., early: +0.05, late: −0.05).

### C3) Optional reflection prompt (post-game)

```
You are {EXPERT_NAME}. The game has finished.

INPUT:
- Your predictions (all 83 assertions, with stakes & confidence)
- The actual outcomes (scores, props) and your graded results (grade 0..1 per category)
- Top memories you relied on

TASK:
- In 120–200 words, summarize WHAT WENT RIGHT, WHAT WENT WRONG, and 3 ACTIONABLE TWEAKS to your factor weights
  (but do NOT return weights—just name the factors and direction, e.g., "↑ weather, ↓ momentum in snow with wind > 15 mph").
- Tone: concise, self-critical, consistent with your persona.
- Output JSON: {"lessons":["...","...","..."], "notable_factors":["weather_up","momentum_down","market_same"]}
```

---

## D) Deterministic services (no extra AI)

1. **Grading & settlement**

* Binary/enum exact; numeric Gaussian kernel with category `sigma`.
* Odds parsing (american/decimal/fraction) → PnL; update bankroll; inactivate on zero.

2. **Learning without “changing minds”**

* Calibration (Beta for binary/enum; EMA bias/σ for numeric).
* Factor-weight MWU recorded in `weight_adjustments` (history, not editing outputs).

3. **Vector memories**

* Edge worker writes `combined_embedding` into `expert_episodic_memories`.
* RPC blends similarity + 90-day recency; no calls needed.

4. **Neo4j write-behind**

* After settlement, emit: `(Decision)`, `(Assertion)x83`, `USED_IN` per assertion (top-K), and `EVALUATED_AS` with grades.

---

## E) Council (you can turn on after the pilot)

* **Selection (top-5) per category family**: composite of recent ROI, accuracy, calibration, bankroll ratio, stake intensity, diversity bonus.
* **Weighting**: `w ∝ stake_units * skill(family) * calibrator(family)`; combine log-odds / precision-weighted means.
* **Coherence**: project aggregated platform slate to satisfy totals/scores/quarters/props constraints (experts remain untouched).

---

## F) How to ingest your sample row (walkthrough)

Your row:

```json
{"game_id":"2025_01_MIA_IND","season":2025,"week":1,"game_date":"2025-09-07",
 "home_team":"IND","away_team":"MIA","spread_line":"1.5","total_line":"47.5",
 "home_moneyline":-112,"away_moneyline":-108, "roof":"closed","surface":"fieldturf", ...}
```

Per expert, per game:

1. **Context**: build query string (away at home, season/week, market, roof/surface).
2. **Embed** context → vector RPC (k=7).
3. **Fetch** `team_knowledge`(IND & MIA), `matchup_memories`(IND home vs MIA).
4. **LLM call** → 83 assertions JSON with `stake_units` & `odds` each.
5. **Store** assertions; write `expert_bets` rows (exact stake and odds they chose).
6. **(Optional)** Council aggregation & coherence.
7. **Post-game** (you already have truth): grade each assertion; settle; update bankroll, buckets; push Neo4j.

---

## G) Call budget for the pilot

* **2020–2023 learning pass**:

  * **Option A (cheapest)**: Skip prediction LLM calls; generate *minimal* assertions from rules & buckets, but still run **reflection** weekly (1 call per expert per week) to build style/memory.
  * **Option B (balanced)**: **1 LLM per game per expert** (predictions) with stakes set to 0 (or tiny) during backfill; **no** reflection.
* **2024 betting simulation**: **1 LLM per game per expert** (predictions + stakes). Optional weekly reflections (1 per expert/wk).
* **2025 YTD**: same as 2024.

For 4 experts:

* Option B rough order: ~272 games/season → ~1,088 calls/season (predictions only). Add reflections weekly (~18) → ~72 more.

---

## H) “Ready to send” list for the final PRD

* ✅ DB tables: `expert_prediction_assertions`, `assertion_outcomes`, `expert_bets`, `expert_bankroll`, `expert_factor_weights`, `weight_adjustments`, `expert_category_calibration`, `expert_family_metrics`, `council_selections`.
* ✅ RPC: `search_expert_memories` (similarity + recency).
* ✅ Prompts: C1/C2/C3 exactly as above.
* ✅ Algorithm notes: grading rubrics (`sigma` by category), settlement math, MWU updates, council formula, coherence projection.
* ✅ Pilot plan: 4 experts → learn 2020–2023, bet 2024, continue 2025 YTD.
* ✅ Neo4j lazily populated with Decision/Assertion/Thought/Outcome.

If this matches your mental model, ship the PRD as-is and kick the pilot on a **single week** of 2024 with 4 experts to sanity-check: vector latency, JSON validity, bankroll updates, and that the personalities feel distinct.

If you want, I can also drop a **compact category registry** (83 rows with `category_id`, `pred_type`, `subject_type`, `sigma`, `family`) so your parser, grader, and prompts share one source of truth.



sweet. you’ve got:

* `category_registry.json` (all 83)
* `settlement_helper.py` (odds → PnL)

# quick-start checklist (4-expert pilot)

1. drop files

* `config/category_registry.json`
* `src/utils/settlement_helper.py`

2. wire the registry

```python
# src/config/categories.py
import json, pathlib
REGISTRY = json.loads(pathlib.Path("config/category_registry.json").read_text())
BY_ID = {c["id"]: c for c in REGISTRY}
```

3. validate expert outputs before insert

* check: 83 items, each `id` exists, `pred_type`/`subject` match, enums in `allowed`, numerics are numbers, `confidence∈[0,1]`, `stake_units≥0`, `odds` parseable.

4. store assertions → create `expert_bets` from their `stake_units` + `odds`.

5. after game: grade each assertion (use `sigma` from registry) → write `assertion_outcomes`; settle bets with `settlement_helper.settle_ticket()` → update bankrolls.

6. (optional) council: seat top-5 per family, weight & combine, then run platform coherence projection.

7. write-behind: push Neo4j `Decision/Assertion/USED_IN/EVALUATED_AS` after settlement.

# tiny helpers

## numeric grading (Gaussian kernel)

```python
import math
def grade_numeric(category_id: str, pred: float, actual: float, by_id) -> tuple[float,float]:
    sigma = by_id[category_id].get("sigma", 10.0)
    err = abs(pred - actual)
    return (math.exp(- (err / sigma) ** 2), err)
```

## enum/binary grading

```python
def grade_enum(pred: str, actual: str) -> tuple[float,bool]:
    return (1.0 if pred == actual else 0.0, pred == actual)

def grade_binary(prob: float, actual_bool: bool) -> dict:
    # brier for calibration tracking
    y = 1.0 if actual_bool else 0.0
    brier = (prob - y) ** 2
    return {"grade": 1.0 if ((prob >= 0.5) == actual_bool) else 0.0, "brier": brier, "is_correct": (prob >= 0.5) == actual_bool}
```

# next two things I can generate (ready now)

1. a **JSON Schema** for the 83-assertion expert output (strict validation).
2. a **seed ingest script** that:

   * reads your game rows,
   * runs memory retrieval RPC,
   * builds the expert prompt payload (with registry),
   * parses/validates the 83 predictions,
   * stores assertions + `expert_bets`,
   * (optionally) does grading/settlement when truth is present.

say the word and I’ll spit both out so you can kick off 2020→2025 with 4 experts.


boom — here are the two artifacts so you can kick off multi-season ingest with 4 experts today.

---

# 1) JSON Schema — expert 83-assertion output

Save as `schemas/expert_predictions_v1.schema.json`.
Use with `jsonschema` (Python) or any validator in your stack.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://yourdomain/schemas/expert_predictions_v1.schema.json",
  "title": "Expert 83-Assertion Output",
  "type": "object",
  "required": ["overall", "predictions"],
  "additionalProperties": false,
  "properties": {
    "overall": {
      "type": "object",
      "required": ["winner_team_id", "home_win_prob", "overall_confidence"],
      "additionalProperties": true,
      "properties": {
        "winner_team_id": { "type": "string" },
        "home_win_prob": { "type": "number", "minimum": 0, "maximum": 1 },
        "away_win_prob": { "type": "number", "minimum": 0, "maximum": 1 },
        "overall_confidence": { "type": "number", "minimum": 0, "maximum": 1 },
        "recency_alpha_used": { "type": "number", "minimum": 0, "maximum": 1 }
      }
    },
    "predictions": {
      "type": "array",
      "minItems": 83,
      "maxItems": 83,
      "items": {
        "type": "object",
        "required": ["category", "subject", "pred_type", "value", "confidence", "stake_units", "odds", "why"],
        "additionalProperties": false,
        "properties": {
          "category": {
            "type": "string",
            "enum": [
              "game_winner","home_score_exact","away_score_exact","margin_of_victory",
              "spread_full_game","total_full_game","winner_moneyline","first_half_winner","first_half_spread","first_half_total",
              "q1_winner","q2_winner","q3_winner","q4_winner","q1_total","q2_total","q3_total","q4_total","first_half_total_points","second_half_total_points","highest_scoring_quarter","lowest_scoring_quarter",
              "team_total_points_home","team_total_points_away","first_team_to_score","last_team_to_score","team_with_longest_td","team_with_most_turnovers","team_with_most_sacks","team_with_most_penalties","largest_lead_of_game","number_of_lead_changes",
              "will_overtime","will_safety","will_pick_six","will_fumble_return_td","will_defensive_td","will_special_teams_td","will_punt_return_td","will_kickoff_return_td","total_turnovers","total_sacks","total_penalties","longest_touchdown","longest_field_goal","total_field_goals_made","missed_extra_points",
              "qb_passing_yards","qb_passing_tds","qb_interceptions","qb_rushing_yards","rb_rushing_yards","rb_rushing_tds","wr_receiving_yards","wr_receptions","te_receiving_yards","kicker_total_points",
              "anytime_td_scorer","first_td_scorer","last_td_scorer","qb_longest_completion","rb_longest_rush","wr_longest_reception","kicker_longest_fg","defense_interceptions","defense_sacks","defense_forced_fumbles","qb_fantasy_points","top_skill_player_fantasy",
              "live_win_probability","next_score_type","current_drive_outcome","fourth_down_decision","next_team_to_score","time_to_next_score_min",
              "weather_impact_score","injury_impact_score","travel_rest_factor","divisional_rivalry_factor","coaching_advantage","home_field_advantage_pts","momentum_factor","public_betting_bias"
            ]
          },
          "subject": { "type": "string" },
          "pred_type": { "type": "string", "enum": ["binary", "enum", "numeric"] },
          "value": { "oneOf": [ { "type": "boolean" }, { "type": "number" }, { "type": "string" } ] },
          "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
          "stake_units": { "type": "number", "minimum": 0 },
          "odds": {
            "type": "object",
            "required": ["type", "value"],
            "additionalProperties": false,
            "properties": {
              "type": { "type": "string", "enum": ["american", "decimal", "fraction"] },
              "value": { "oneOf": [ { "type": "string" }, { "type": "number" } ] }
            }
          },
          "why": {
            "type": "array",
            "minItems": 0,
            "items": {
              "type": "object",
              "required": ["memory_id","weight"],
              "additionalProperties": false,
              "properties": {
                "memory_id": { "type": "string" },
                "weight": { "type": "number", "minimum": 0 }
              }
            }
          }
        },
        "allOf": [
          {
            "if": { "properties": { "pred_type": { "const": "binary" } } },
            "then": { "properties": { "value": { "type": "boolean" } } }
          },
          {
            "if": { "properties": { "pred_type": { "const": "numeric" } } },
            "then": { "properties": { "value": { "type": "number" } } }
          },
          {
            "if": { "properties": { "pred_type": { "const": "enum" } } },
            "then": { "properties": { "value": { "type": "string" } } }
          }
        ]
      }
    }
  }
}
```

---

# 2) Seed ingest script — multi-season runner

Save as `scripts/seed_ingest_runner.py`.
This script:

* Loads the category registry + JSON Schema.
* For each game row and each expert:

  * Builds a compact context
  * Calls vector RPC (you’ll provide your embed function)
  * Builds the expert prompt payload
  * Calls your expert LLM once to get 83 predictions
  * Validates JSON with the schema
  * Stores assertions + `expert_bets`
* If actuals exist in the row, it will grade + settle bankrolls (using the helper you have).

> You’ll need: `pip install supabase jsonschema` and your LLM client(s).
> Fill the two TODOs: `embed_query()` and `call_expert_llm()`.

```python
#!/usr/bin/env python3
# scripts/seed_ingest_runner.py

import os, json, math, pathlib, time
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

from supabase import create_client, Client
from jsonschema import validate, Draft202012Validator
from jsonschema.exceptions import ValidationError

# --- local files ---
CATEGORY_REGISTRY = json.loads(pathlib.Path("config/category_registry.json").read_text())
REG_BY_ID = {c["id"]: c for c in CATEGORY_REGISTRY}
SCHEMA = json.loads(pathlib.Path("schemas/expert_predictions_v1.schema.json").read_text())

# settlement helper
from src.utils.settlement_helper import settle_ticket, to_decimal

# === CONFIG ===
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_ANON_KEY"]
sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# pilot experts (edit as needed)
EXPERTS = [
    "conservative_analyzer",
    "risk_taking_gambler",
    "contrarian_rebel",
    "momentum_rider",
]

# persona recency alpha defaults (tweak later)
RECENCY_ALPHA = {
    "conservative_analyzer": 0.88,
    "risk_taking_gambler":   0.72,
    "contrarian_rebel":      0.78,
    "momentum_rider":        0.80,
}

# === UTILITIES ===
def safe_get(d: Dict, *path, default=None):
    cur = d
    for k in path:
        if cur is None: return default
        cur = cur.get(k)
    return cur if cur is not None else default

def build_context_string(game: Dict[str, Any]) -> str:
    parts = [
        f"{game['away_team']} at {game['home_team']}",
        f"season:{game['season']} week:{game['week']}",
        f"spread_home:{game.get('spread_line')}",
        f"total:{game.get('total_line')}",
        f"roof:{game.get('roof')}",
        f"surface:{game.get('surface')}",
    ]
    return " ".join([p for p in parts if p is not None])

def embed_query(text: str) -> List[float]:
    """
    TODO: Implement with your provider (1536-d).
    For now, raise to force you to fill this in intentionally.
    """
    raise NotImplementedError("embed_query() must be implemented for pgvector retrieval.")

def rpc_search_memories(expert_id: str, query_vec: List[float], k: int, alpha: float):
    return sb.rpc("search_expert_memories", {
        "p_expert_id": expert_id,
        "p_query_embedding": query_vec,
        "p_match_threshold": 0.70,
        "p_match_count": k,
        "p_alpha": alpha
    }).execute().data

def fetch_team_knowledge(expert_id: str, team_id: str):
    return sb.table("team_knowledge").select("*") \
        .eq("expert_id", expert_id).eq("team_id", team_id) \
        .order("confidence_level", desc=True).limit(10).execute().data

def fetch_matchup_memory(expert_id: str, home: str, away: str):
    out = sb.table("matchup_memories").select("*") \
        .eq("expert_id", expert_id).eq("home_team", home).eq("away_team", away) \
        .limit(1).execute()
    return out.data[0] if getattr(out, "data", None) else None

def call_expert_llm(expert_id: str, system_prompt: str, user_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    TODO: Implement with your LLM router (OpenAI/Anthropic/etc.).
    Must return a parsed Python dict per schema.
    """
    raise NotImplementedError("call_expert_llm() must be implemented with your model router.")

def validate_output(doc: Dict[str, Any]) -> None:
    Draft202012Validator(SCHEMA).validate(doc)

def store_assertions_and_bets(expert_id: str, game: Dict[str,Any], doc: Dict[str,Any]) -> List[str]:
    game_id = game["game_id"]
    assertion_ids = []

    for a in doc["predictions"]:
        # insert assertion
        ins = {
            "expert_id": expert_id,
            "game_id": game_id,
            "category": a["category"],
            "subject": a["subject"],
            "pred_type": a["pred_type"],
            "pred_value_numeric": a["value"] if a["pred_type"] == "numeric" else None,
            "pred_value_text": (a["value"] if a["pred_type"] in ("enum","binary") else None),
            "confidence": a["confidence"],
            "why_weights": None,                # optional
            "top_memories": a.get("why", []),
        }
        res = sb.table("expert_prediction_assertions").insert(ins).execute()
        assertion_id = res.data[0]["assertion_id"]
        assertion_ids.append(assertion_id)

        # insert bet (exactly what expert chose)
        odds = a["odds"]
        bet = {
            "expert_id": expert_id,
            "game_id": game_id,
            "assertion_id": assertion_id,
            "category": a["category"],
            "stake_units": float(a["stake_units"]),
            "odds_type": odds["type"],
            "odds_value": str(odds["value"]),
        }
        sb.table("expert_bets").insert(bet).execute()

    # update/insert bundle row (optional)
    overall = doc["overall"]
    up = {
        "expert_id": expert_id,
        "game_id": game_id,
        "predicted_winner": overall["winner_team_id"],
        "home_win_prob": overall["home_win_prob"],
        "away_win_prob": overall.get("away_win_prob"),
        "overall_confidence": overall["overall_confidence"],
        "recency_alpha_used": overall.get("recency_alpha_used"),
    }
    sb.table("expert_predictions").upsert(up, on_conflict="expert_id,game_id").execute()
    return assertion_ids

def grade_and_settle_if_possible(expert_id: str, game: Dict[str,Any]):
    """If actuals are present in your row, compute outcomes and settle tickets.
       This is a placeholder: you’ll map real actuals per category when available.
    """
    game_id = game["game_id"]

    # Example: settle a couple macro outcomes if you have truth
    # Pull assertions for this expert/game
    ass = sb.table("expert_prediction_assertions").select("*") \
        .eq("expert_id", expert_id).eq("game_id", game_id).execute().data

    # Your game row has these fields:
    # result = home_score - away_score, total = home+away (already in your sample)
    home_score = game.get("home_score")
    away_score = game.get("away_score")
    total_actual = game.get("total")
    winner_actual = "home" if home_score is not None and away_score is not None and home_score > away_score else "away"

    # Build a tiny actuals map for demonstration
    actuals = {
        "game_winner": winner_actual,
        "home_score_exact": home_score,
        "away_score_exact": away_score,
        "total_full_game": total_actual
    }

    # Grade a subset (you’ll expand to all 83 with your final mapping)
    for a in ass:
        cat = a["category"]
        pred_type = a["pred_type"]
        if cat not in actuals:  # skip categories you don’t have truth for yet
            continue

        # compute grade
        if pred_type == "enum":
            grade = 1.0 if str(a["pred_value_text"]) == str(actuals[cat]) else 0.0
            outcome_flag = "win" if grade == 1.0 else "loss"
            details = {"pred": a["pred_value_text"], "actual": actuals[cat]}
            err = None
            brier = None
        elif pred_type == "numeric":
            sigma = REG_BY_ID[cat].get("sigma", 10.0)
            pred = float(a["pred_value_numeric"])
            actual = float(actuals[cat])
            err = abs(pred - actual)
            grade = math.exp(- (err / sigma) ** 2)
            outcome_flag = "win" if err <= 0.5 else "loss"  # demo rule; refine per rubric
            details = {"pred": pred, "actual": actual, "sigma": sigma}
            brier = None
        elif pred_type == "binary":
            # interpret pred_value_text as "true"/"false" if you used text, or change to a boolean
            pv = a["pred_value_text"]
            pred_bool = (pv is True) if isinstance(pv, bool) else (str(pv).lower() == "true")
            actual_bool = bool(actuals[cat])
            grade = 1.0 if pred_bool == actual_bool else 0.0
            outcome_flag = "win" if grade == 1.0 else "loss"
            details = {"pred": pred_bool, "actual": actual_bool}
            err = None
            brier = ( (1.0 if pred_bool else 0.0) - (1.0 if actual_bool else 0.0) ) ** 2

        # write outcome
        outcome_row = {
            "assertion_id": a["assertion_id"],
            "is_correct": outcome_flag == "win",
            "error": err,
            "grade": grade,
            "brier": brier,
            "details": details
        }
        sb.table("assertion_outcomes").upsert(outcome_row, on_conflict="assertion_id").execute()

    # settle tickets
    bets = sb.table("expert_bets").select("*") \
        .eq("expert_id", expert_id).eq("game_id", game_id).eq("settled", False).execute().data
    for b in bets:
        cat = b["category"]
        if cat not in actuals:
            continue
        # naive settle based on outcome row we just wrote
        out = sb.table("assertion_outcomes").select("is_correct").eq("assertion_id", b["assertion_id"]).single().execute().data
        if not out:
            continue
        is_correct = out["is_correct"]
        outcome = "win" if is_correct else "loss"

        pnl, payout = settle_ticket(
            stake_units=float(b["stake_units"]),
            odds_type=b["odds_type"],
            odds_value=b["odds_value"],
            outcome=outcome
        )
        sb.table("expert_bets").update({
            "settled": True, "outcome": outcome, "pnl": pnl, "settled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }).eq("bet_id", b["bet_id"]).execute()

        # update bankroll
        # fetch or create bankroll row
        br = sb.table("expert_bankroll").select("*").eq("expert_id", b["expert_id"]).execute().data
        if not br:
            sb.table("expert_bankroll").insert({"expert_id": b["expert_id"], "season": int(game["season"])}).execute()
            br = sb.table("expert_bankroll").select("*").eq("expert_id", b["expert_id"]).execute().data
        cur = br[0]["bankroll"]
        new_bal = (cur or 100.0) + pnl
        sb.table("expert_bankroll").update({
            "bankroll": new_bal,
            "is_active": new_bal > 0,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }).eq("expert_id", b["expert_id"]).execute()

def run_for_game(game: Dict[str, Any]):
    # build retrieval payload once
    ctx_text = build_context_string(game)
    qvec = embed_query(ctx_text)

    for expert_id in EXPERTS:
        alpha = RECENCY_ALPHA.get(expert_id, 0.8)
        top_mems = rpc_search_memories(expert_id, qvec, k=7, alpha=alpha)
        home_k = fetch_team_knowledge(expert_id, game["home_team"])
        away_k = fetch_team_knowledge(expert_id, game["away_team"])
        matchup = fetch_matchup_memory(expert_id, game["home_team"], game["away_team"])

        system_prompt = f"You are {expert_id}. Produce exactly 83 predictions with stakes as per schema."
        user_payload = {
            "game": {
                "game_id": game["game_id"],
                "season": game["season"],
                "week": game["week"],
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "weather": {
                    "temp_f": game.get("weather_temperature"),
                    "wind_mph": game.get("weather_wind_mph"),
                    "desc": game.get("weather_description")
                },
                "market": {
                    "spread_home": float(game["spread_line"]) if game.get("spread_line") not in (None, "") else None,
                    "total": float(game["total_line"]) if game.get("total_line") not in (None, "") else None,
                    "moneyline_home": game.get("home_moneyline"),
                    "moneyline_away": game.get("away_moneyline")
                },
                "meta": {"div_game": game.get("div_game"), "roof": game.get("roof"), "surface": game.get("surface")}
            },
            "recency_summary": {"alpha": alpha, "top_memories": top_mems},
            "team_knowledge": {"home": home_k, "away": away_k},
            "matchup_memory": {"role_aware": matchup} if matchup else None,
            "registry": CATEGORY_REGISTRY  # let the expert see the exact catalog
        }

        # Call expert model (fill this in)
        doc = call_expert_llm(expert_id, system_prompt, user_payload)

        # Validate hard before insert
        try:
            validate_output(doc)
        except ValidationError as e:
            raise RuntimeError(f"Schema validation failed for {expert_id} {game['game_id']}: {e.message}")

        # Store assertions & bets
        store_assertions_and_bets(expert_id, game, doc)

        # If actuals present, grade + settle
        if game.get("home_score") is not None and game.get("away_score") is not None:
            grade_and_settle_if_possible(expert_id, game)

def main():
    # Example: read a JSON list of games (like the one you pasted)
    # Place your multi-season dataset at data/games_2020_2025.json
    games = json.loads(pathlib.Path("data/games_2020_2025.json").read_text())
    # Sort chronologically
    games.sort(key=lambda g: (g["season"], g["week"], g.get("game_datetime") or g.get("game_date","")))
    for g in games:
        if g["season"] < 2020:  # skip anything before
            continue
        # Pilot: process for all four experts
        run_for_game(g)
        # small pause to be nice to your model APIs (tune as needed)
        time.sleep(0.05)

if __name__ == "__main__":
    main()
```

---

## notes / next knobs

* **Implement `embed_query()`** with your embedding provider (1536-d to match pgvector columns).
* **Implement `call_expert_llm()`** with your router; return a Python dict that matches the schema exactly.
* **Expand `grade_and_settle_if_possible()`** to map *all 83* categories to truth for seasons where you’ve got granular stats.
* **Batching & concurrency:** once you’re happy, run experts in parallel (per game) with a rate limiter.
* **Reflections:** if you want weekly expert reflections, bolt a tiny weekly cron that reads last 1–2 games per expert and calls a short prompt.

If you want a **tiny odds parser** that converts any book line payload you have into `odds_type/odds_value` for the expert JSON, or a **projection helper** to enforce platform coherence, I can generate those too.
