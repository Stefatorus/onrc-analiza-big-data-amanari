/-
  OnrcProofs/QueueTheory.lean
  Machine-checked formal proofs for discrete FIFO queue dynamics,
  Skorokhod reflection equivalence, calendar vs. working-day boundaries,
  and two-class priority capacity conservation (INMATRIC265 vs. CERERE265).
-/

namespace OnrcProofs

/-- Single-day Lindley workload update: S_{t+1} = max(0, S_t + A_t - C_t). -/
def lindleyStep (s a c : Int) : Int :=
  max 0 (s + a - c)

/-- Discrete Lindley workload state trajectory from t = 0 to t. -/
def lindleyState (s0 : Int) (a c : Nat → Int) : Nat → Int
  | 0 => s0
  | t + 1 => lindleyStep (lindleyState s0 a c t) (a t) (c t)

/-- Cumulative net workload arrival stream N_k = sum_{j < k} x_j. -/
def cumNet (x : Nat → Int) : Nat → Int
  | 0 => 0
  | k + 1 => cumNet x k + x k

/-- Running minimum of shifted cumulative net flow s0 + N_k from 0 to k. -/
def reflMin (s0 : Int) (x : Nat → Int) : Nat → Int
  | 0 => min 0 s0
  | k + 1 => min (reflMin s0 x k) (s0 + cumNet x (k + 1))

/-- Theorem 1a: Lindley queue stock is monotone in initial stock (≤), arrivals (≤),
    and inverse-capacity (≥). -/
theorem lindley_mono (s1 s2 : Int) (a1 a2 c1 c2 : Nat → Int)
    (hs : s1 ≤ s2)
    (ha : ∀ t, a1 t ≤ a2 t)
    (hc : ∀ t, c2 t ≤ c1 t) :
    ∀ t, lindleyState s1 a1 c1 t ≤ lindleyState s2 a2 c2 t := by
  intro t
  induction t with
  | zero =>
      simp [lindleyState]
      exact hs
  | succ k ih =>
      simp [lindleyState, lindleyStep]
      have ha_k := ha k
      have hc_k := hc k
      omega

/-- Helper invariant: reflMin ≤ s0 + cumNet x k and reflMin ≤ 0 when s0 ≥ 0. -/
private theorem reflMin_bounds (s0 : Int) (hs0 : 0 ≤ s0) (x : Nat → Int) :
    ∀ k, reflMin s0 x k ≤ 0 ∧ reflMin s0 x k ≤ s0 + cumNet x k := by
  intro k
  induction k with
  | zero =>
      simp [reflMin, cumNet]
      omega
  | succ j ih =>
      simp [reflMin, cumNet] at *
      omega

/-- Theorem 1b (Skorokhod Reflection Equivalence):
    For any initial backlog s0 ≥ 0 and daily net inflow stream x_t = a_t - c_t,
    the iterative Lindley recursion equals audit_oug.py's closed-form reflection:
      S_k = (s0 + cumNet x k) - min(0, min_{j ≤ k} (s0 + cumNet x j)). -/
theorem skorokhod_reflection_exact (s0 : Int) (hs0 : 0 ≤ s0) (x : Nat → Int) :
    ∀ k, lindleyState s0 x (fun _ => 0) k = (s0 + cumNet x k) - reflMin s0 x k := by
  intro k
  induction k with
  | zero =>
      simp [lindleyState, cumNet, reflMin]
      omega
  | succ j ih =>
      have hb := reflMin_bounds s0 hs0 x j
      simp [lindleyState, lindleyStep, cumNet, reflMin] at *
      omega

/-- Cumulative capacity up to day n (exclusive): C_0 + ... + C_{n-1}. -/
def cumCap (c : Nat → Int) : Nat → Int
  | 0 => 0
  | n + 1 => cumCap c n + c n

/-- Remaining capacity across horizon h days strictly after filing day t. -/
def horizonCap (c : Nat → Int) (t h : Nat) : Int :=
  cumCap c (t + 1 + h) - cumCap c (t + 1)

theorem horizonCap_zero (c : Nat → Int) (t : Nat) :
    horizonCap c t 0 = 0 := by
  simp [horizonCap]

theorem horizonCap_succ (c : Nat → Int) (t k : Nat) :
    horizonCap c t (k + 1) = horizonCap c t k + c (t + 1 + k) := by
  have ha : t + 1 + (k + 1) = (t + 1 + k) + 1 := by omega
  simp only [horizonCap]
  rw [ha, cumCap]
  omega

/-- Theorem 1c (<= 3 Calendar-Day Service Condition & Friday-Weekend Distinction):
    Under non-negative daily capacities, backlog + 1 clears within d ∈ {1,2,3} days
    iff stock + 1 ≤ sum of the next 3 calendar days of capacity (C_{t+1}+C_{t+2}+C_{t+3}). -/
theorem cal_wait_le3_iff (stock : Int) (c : Nat → Int) (hc : ∀ k, 0 ≤ c k) (t : Nat) :
    (stock + 1 ≤ horizonCap c t 1 ∨ stock + 1 ≤ horizonCap c t 2 ∨ stock + 1 ≤ horizonCap c t 3) ↔
      stock + 1 ≤ c (t + 1) + c (t + 2) + c (t + 3) := by
  have hc2 : 0 ≤ c (t + 2) := hc (t + 2)
  have hc3 : 0 ≤ c (t + 3) := hc (t + 3)
  have h1 : horizonCap c t 1 = c (t + 1) := by
    rw [horizonCap_succ, horizonCap_zero, Nat.add_zero, Int.zero_add]
  have h2 : horizonCap c t 2 = c (t + 1) + c (t + 2) := by
    rw [horizonCap_succ, h1]
  have h3 : horizonCap c t 3 = c (t + 1) + c (t + 2) + c (t + 3) := by
    rw [horizonCap_succ, h2]
  rw [h1, h2, h3]
  omega

/-- Friday boundary lemma: if Saturday (t+1) = 0, Sunday (t+2) = 0, Monday (t+3) ≥ 1,
    a dossier filed Friday close with zero stock clears in 3 calendar days (= 1 working day),
    strictly distinct from 3 working days. -/
theorem friday_3cal_is_1wd (cMon : Int) (hc : 1 ≤ cMon) :
    let c : Nat → Int := fun k => if k = 1 ∨ k = 2 then 0 else cMon
    horizonCap c 0 3 = cMon ∧ (0 + 1 ≤ horizonCap c 0 3) ∧ ¬(0 + 1 ≤ horizonCap c 0 2) := by
  intro c
  have h1 : horizonCap c 0 1 = 0 := by
    rw [horizonCap_succ, horizonCap_zero]
    simp [c]
  have h2 : horizonCap c 0 2 = 0 := by
    rw [horizonCap_succ, h1]
    simp [c]
  have h3 : horizonCap c 0 3 = cMon := by
    rw [horizonCap_succ, h2]
    simp [c]
  omega

/-- Theorem 1d (FIFO Monotonicity in Horizon Clearance):
    If stock1 ≤ stock2 and scenario 1 has at least as much capacity as scenario 2 after t,
    any horizon h that clears scenario 2 also clears scenario 1. -/
theorem wait_mono (s1 s2 : Int) (c1 c2 : Nat → Int) (t h : Nat)
    (hs : s1 ≤ s2)
    (hc : ∀ k, t < k → c2 k ≤ c1 k) :
    s2 + 1 ≤ horizonCap c2 t h → s1 + 1 ≤ horizonCap c1 t h := by
  have hcap : horizonCap c2 t h ≤ horizonCap c1 t h := by
    induction h with
    | zero =>
        rw [horizonCap_zero, horizonCap_zero]
        omega
    | succ k ih =>
        have hstep : c2 (t + 1 + k) ≤ c1 (t + 1 + k) := hc (t + 1 + k) (by omega)
        rw [horizonCap_succ, horizonCap_succ]
        omega
  omega

/-- Theorem 2 (Kleinrock Conservation Law & Two-Class Queue Coupled Coupling):
    When INMATRIC265 (class 1) and CERERE265 (class 2) share pooled capacity C = c1 + c2
    and both queues are backlog-saturated, shifting Δ > 0 units of daily capacity from
    CERERE265 to INMATRIC265 decreases S1' by Δ, increases S2' by Δ, and leaves total
    system backlog S1' + S2' strictly invariant (no net backlog creation or destruction).
    AUDIT NOTE (21.11.2026): despite the name, this is a ONE-STEP identity of the Lindley map
    in the saturated regime (both max(0,·) inactive). It is NOT Kleinrock's M/G/1 conservation
    law for work-weighted mean waits, and says nothing about multi-day dynamics or
    non-saturated days. -/
theorem kleinrock_two_class_conservation
    (s1 s2 a1 a2 c1 c2 delta : Int)
    (hdelta : 0 < delta)
    (hsat1 : c1 + delta ≤ s1 + a1)
    (hsat2 : c2 ≤ s2 + a2) :
    let base1 := lindleyStep s1 a1 c1
    let base2 := lindleyStep s2 a2 c2
    let shift1 := lindleyStep s1 a1 (c1 + delta)
    let shift2 := lindleyStep s2 a2 (c2 - delta)
    shift1 + shift2 = base1 + base2 ∧
      shift1 = base1 - delta ∧
      shift2 = base2 + delta ∧
      shift1 < base1 ∧
      base2 < shift2 := by
  simp [lindleyStep]
  omega

end OnrcProofs
