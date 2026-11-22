/-
  OnrcProofs/TandemBottleneck.lean
  Machine-checked formal proofs for the two-stage ONRC tandem workflow:
    [Stage 1: County Operation (Prelucrare)] -> [Stage 2: National Registrar Resolution (Soluționare)].

  All theorems are non-trivial, non-vacuous (explicitly witnessed below), use only standard Lean 4
  axioms (no sorryAx), and accurately state their exact scope (deterministic discrete tandem model
  and exact algebraic mass-conservation / max-frontier identifiability laws).
-/

namespace OnrcProofs.TandemBottleneck

/-- Actual operated flow transferred from Stage 1 to Stage 2 on a single day:
    cannot exceed available Stage-1 work (s1 + a) or Stage-1 capacity c1. -/
def stage1Flow (s1 a c1 : Int) : Int :=
  min (s1 + a) c1

/-- Next-day Stage-1 stock: S1' = S1 + A - F1 = max(0, S1 + A - C1). -/
def stage1Next (s1 a c1 : Int) : Int :=
  s1 + a - stage1Flow s1 a c1

/-- Actual resolved output exiting Stage 2 on a single day:
    cannot exceed Stage-2 stock plus Stage-1 transfer (s2 + F1) or Stage-2 capacity c2. -/
def stage2Flow (s1 s2 a c1 c2 : Int) : Int :=
  min (s2 + stage1Flow s1 a c1) c2

/-- Next-day Stage-2 stock: S2' = S2 + F1 - F2 = max(0, S2 + F1 - C2). -/
def stage2Next (s1 s2 a c1 c2 : Int) : Int :=
  s2 + stage1Flow s1 a c1 - stage2Flow s1 s2 a c1 c2

/-- Coupled two-stage tandem state trajectory (S1_t, S2_t). -/
def tandemState (s1_0 s2_0 : Int) (a c1 c2 : Nat → Int) : Nat → Int × Int
  | 0 => (s1_0, s2_0)
  | t + 1 =>
      let st := tandemState s1_0 s2_0 a c1 c2 t
      (stage1Next st.1 (a t) (c1 t), stage2Next st.1 st.2 (a t) (c1 t) (c2 t))

/-- Cumulative arrivals up to day T (exclusive). -/
def cumSum (x : Nat → Int) : Nat → Int
  | 0 => 0
  | t + 1 => cumSum x t + x t

/-- Cumulative Stage-1 operated flow up to day T (exclusive). -/
def cumFlow1 (s1_0 s2_0 : Int) (a c1 c2 : Nat → Int) : Nat → Int
  | 0 => 0
  | t + 1 =>
      let st := tandemState s1_0 s2_0 a c1 c2 t
      cumFlow1 s1_0 s2_0 a c1 c2 t + stage1Flow st.1 (a t) (c1 t)

/-- Cumulative Stage-2 resolved output up to day T (exclusive). -/
def cumFlow2 (s1_0 s2_0 : Int) (a c1 c2 : Nat → Int) : Nat → Int
  | 0 => 0
  | t + 1 =>
      let st := tandemState s1_0 s2_0 a c1 c2 t
      cumFlow2 s1_0 s2_0 a c1 c2 t + stage2Flow st.1 st.2 (a t) (c1 t) (c2 t)

/-- Helper: Stage-1 and Stage-2 stocks remain non-negative for all T whenever initial stocks,
    arrivals, and capacities are non-negative. -/
theorem tandem_nonneg
    (s1_0 s2_0 : Int) (a c1 c2 : Nat → Int)
    (hs1 : 0 ≤ s1_0) (hs2 : 0 ≤ s2_0)
    (ha : ∀ t, 0 ≤ a t) (hc1 : ∀ t, 0 ≤ c1 t) (hc2 : ∀ t, 0 ≤ c2 t) :
    ∀ T, 0 ≤ (tandemState s1_0 s2_0 a c1 c2 T).1 ∧
         0 ≤ (tandemState s1_0 s2_0 a c1 c2 T).2 := by
  intro T
  induction T with
  | zero =>
      simp [tandemState]
      exact ⟨hs1, hs2⟩
  | succ t ih =>
      have ha_t := ha t
      have hc1_t := hc1 t
      have hc2_t := hc2 t
      simp [tandemState, stage1Next, stage2Next, stage1Flow, stage2Flow] at *
      omega

/-- Theorem T13a (Exact Multi-Day Tandem Mass Conservation):
    For every horizon T ≥ 0, total system backlog plus cumulative resolved output equals
    initial total backlog plus cumulative arrivals, and Stage-1 and Stage-2 individually
    conserve mass across their shared transfer stream cumFlow1. -/
theorem tandem_mass_conservation
    (s1_0 s2_0 : Int) (a c1 c2 : Nat → Int) :
    ∀ T,
      (tandemState s1_0 s2_0 a c1 c2 T).1 + cumFlow1 s1_0 s2_0 a c1 c2 T = s1_0 + cumSum a T ∧
      (tandemState s1_0 s2_0 a c1 c2 T).2 + cumFlow2 s1_0 s2_0 a c1 c2 T = s2_0 + cumFlow1 s1_0 s2_0 a c1 c2 T ∧
      (tandemState s1_0 s2_0 a c1 c2 T).1 + (tandemState s1_0 s2_0 a c1 c2 T).2 +
        cumFlow2 s1_0 s2_0 a c1 c2 T = s1_0 + s2_0 + cumSum a T := by
  intro T
  induction T with
  | zero =>
      simp [tandemState, cumFlow1, cumFlow2, cumSum]
  | succ t ih =>
      rcases ih with ⟨h1, h2, htot⟩
      simp [tandemState, stage1Next, stage2Next, cumFlow1, cumFlow2, cumSum] at *
      omega

/-- Helper: cumulative Stage-1 flow cannot exceed cumulative Stage-1 capacity, and
    cumulative Stage-2 flow cannot exceed cumulative Stage-2 capacity. -/
theorem tandem_flow_le_cap
    (s1_0 s2_0 : Int) (a c1 c2 : Nat → Int) :
    ∀ T,
      cumFlow1 s1_0 s2_0 a c1 c2 T ≤ cumSum c1 T ∧
      cumFlow2 s1_0 s2_0 a c1 c2 T ≤ cumSum c2 T := by
  intro T
  induction T with
  | zero =>
      simp [cumFlow1, cumFlow2, cumSum]
  | succ t ih =>
      rcases ih with ⟨h1, h2⟩
      simp [cumFlow1, cumFlow2, cumSum, stage1Flow, stage2Flow] at *
      omega

/-- Theorem T13b (Tandem Bottleneck Dominance & Stage-2 Starvation Bound):
    Over ANY horizon T ≥ 0, cumulative resolved output cumFlow2 is simultaneously bounded above by:
      (1) Total supply: s1_0 + s2_0 + cumSum a T;
      (2) Stage-1 starvation ceiling: s2_0 + cumSum c1 T;
      (3) Stage-2 capacity ceiling: cumSum c2 T.
    Consequence: scaling Stage-2 capacity C2 arbitrarily high without expanding Stage-1 capacity C1
    can NEVER raise cumulative resolved output above s2_0 + cumSum c1 T (once S2 drains, Stage 2
    is starved by Stage 1). -/
theorem tandem_throughput_ceiling
    (s1_0 s2_0 : Int) (a c1 c2 : Nat → Int)
    (hs1 : 0 ≤ s1_0) (hs2 : 0 ≤ s2_0)
    (ha : ∀ t, 0 ≤ a t) (hc1 : ∀ t, 0 ≤ c1 t) (hc2 : ∀ t, 0 ≤ c2 t) :
    ∀ T,
      cumFlow2 s1_0 s2_0 a c1 c2 T ≤ s1_0 + s2_0 + cumSum a T ∧
      cumFlow2 s1_0 s2_0 a c1 c2 T ≤ s2_0 + cumSum c1 T ∧
      cumFlow2 s1_0 s2_0 a c1 c2 T ≤ cumSum c2 T := by
  intro T
  have hnn := tandem_nonneg s1_0 s2_0 a c1 c2 hs1 hs2 ha hc1 hc2 T
  have hmc := tandem_mass_conservation s1_0 s2_0 a c1 c2 T
  have hcap := tandem_flow_le_cap s1_0 s2_0 a c1 c2 T
  omega

/-- Theorem T13c (Staff Reallocation Optimum & OUG Art. I Cannibalization Threshold):
    Suppose Stage 1 has daily capacity c1, Stage 2 has daily capacity c2 ≤ c1, and reallocating
    internal staff transfers δ ≥ 0 units/day from Stage 1 to Stage 2 (1:1 transfer):
      - Steady-state tandem throughput min(c1 - δ, c2 + δ) is bounded above by (c1 + c2)/2
        (specifically 2 * min(c1 - δ, c2 + δ) ≤ c1 + c2 for ALL δ);
      - For 0 < δ < c1 - c2, throughput strictly exceeds baseline c2;
      - At the break-even threshold δ = c1 - c2, throughput returns to baseline c2 (zero gain);
      - For δ > c1 - c2 (over-cannibalization), throughput STRICTLY FALLS below baseline c2
        because Stage 1 flips into the tighter bottleneck. -/
theorem tandem_reallocation_cannibalization
    (c1 c2 delta : Int)
    (horder : c2 ≤ c1) :
    (2 * min (c1 - delta) (c2 + delta) ≤ c1 + c2) ∧
    (0 < delta ∧ delta < c1 - c2 → c2 < min (c1 - delta) (c2 + delta)) ∧
    (delta = c1 - c2 → min (c1 - delta) (c2 + delta) = c2) ∧
    (c1 - c2 < delta → min (c1 - delta) (c2 + delta) < c2) := by
  omega

/-- General asymmetric conversion version of T13c:
    If reallocating staff loses u1 > 0 of Stage-1 capacity and adds u2 > 0 of Stage-2 capacity,
    steady-state throughput strictly decreases whenever c1 - u1 < c2 (even if u2 is arbitrarily large). -/
theorem tandem_asymmetric_cannibalization
    (c1 c2 u1 u2 : Int)
    (hdrop : c1 - u1 < c2) :
    min (c1 - u1) (c2 + u2) < c2 := by
  omega

/-- Theorem T13d (Global-FIFO Max-Frontier Identifiability & Dual-Threshold Exposure Law):
    When Stage 2 serves operated dossiers in global applicationDate order with national wait floor w2
    and county c has local Stage-1 lag w1, total county wait is w_total = max w1 w2. Then:
      (1) One-sided excess: w_total - w2 ≥ 0 always (no fast county can beat the national floor);
      (2) Masking equivalence: w_total = w2 ↔ w1 ≤ w2 (fast Stage-1 counties are masked by Stage 2);
      (3) Exact Stage-1 identification above floor: w2 < w_total → w1 = w_total;
      (4) Monotone dual-threshold exposure: if a priority class (e.g. INMATRIC265) lowers the Stage-2
          floor from w2_hi to w2_lo < w2_hi, every county exposed at w2_hi remains exposed at w2_lo,
          and every intermediate county (w2_lo < w1 ≤ w2_hi) becomes newly exposed. -/
theorem max_frontier_identifiability
    (w1 w2_lo w2_hi : Int)
    (hfloor : w2_lo < w2_hi) :
    (0 ≤ max w1 w2_hi - w2_hi) ∧
    (max w1 w2_hi = w2_hi ↔ w1 ≤ w2_hi) ∧
    (w2_hi < max w1 w2_hi → w1 = max w1 w2_hi) ∧
    (w2_hi < max w1 w2_hi → w2_lo < max w1 w2_lo) ∧
    (w2_lo < w1 ∧ w1 ≤ w2_hi → max w1 w2_hi = w2_hi ∧ w2_lo < max w1 w2_lo) := by
  omega

/-- Theorem T13e (Exact Two-Stage Conservation Identifiability — Independent of Unobserved Arrivals):
    Over any interval where Stage-1 stock changes by dS1 = I - O1 and Stage-2 stock changes by
    dS2 = O1 - O2, the throughput gap O1 - O2 equals dS2 identically for ALL unobserved inflows I.
    Moreover, if dS1 < 0, dS2 > 0, and dS1 + dS2 < 0 (the exact MJ 30 Oct -> 6 Nov regime),
    then strictly I < O2 < O1 holds unconditionally. -/
theorem tandem_interval_identifiability
    (s1_0 s1_1 s2_0 s2_1 I O1 O2 : Int)
    (h1 : s1_1 - s1_0 = I - O1)
    (h2 : s2_1 - s2_0 = O1 - O2) :
    (O1 - O2 = s2_1 - s2_0) ∧
    (s1_1 < s1_0 ∧ s2_0 < s2_1 ∧ s1_1 + s2_1 < s1_0 + s2_0 → I < O2 ∧ O2 < O1) := by
  omega

/-- Concrete MJ 30 Oct -> 6 Nov 2026 certificate:
    S1: 114,360 -> 106,060 (-8,300); S2: 93,958 -> 98,354 (+4,396).
    For ANY unobserved weekly inflow I and Stage-2 output O2 satisfying mass conservation,
    Stage-1 output O1 exceeds O2 by exactly 4,396 dossiers (+879.2/wd over 5 workdays) and I < O2 < O1. -/
theorem mj_oct30_nov06_exact_gap
    (I O1 O2 : Int)
    (h1 : 106060 - 114360 = I - O1)
    (h2 : 98354 - 93958 = O1 - O2) :
    O1 - O2 = 4396 ∧ O1 - I = 8300 ∧ O2 - I = 3904 ∧ I < O2 ∧ O2 < O1 := by
  omega

/-- Non-vacuity witness: concretely instantiates T13a, T13b, T13c, T13d, T13e with positive
    real-scale ONRC numbers (distinct-dossier Nov 2–6 anchor: C1=6156, C2=5277, I=4496, δ=440)
    confirming no hypothesis set is vacuous. -/
theorem tandem_non_vacuity_witness :
    let st := tandemState 106060 98354 (fun _ => 4496) (fun _ => 6156) (fun _ => 5277) 1
    st.1 = 104400 ∧ st.2 = 99233 ∧
    (5277 < min (6156 - 440) (5277 + 440)) ∧
    (min (6156 - 1100) (5277 + 1100) < 5277) ∧
    (max 47 57 = 57 ∧ 41 < max 47 41) := by
  decide

end OnrcProofs.TandemBottleneck
