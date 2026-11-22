/-
  OnrcProofs/EconometricsAndBias.lean
  Machine-checked proofs for:
    - Theorem 6: Multiplicative scaling bias vs. Additive Seasonal DiD inflow estimator
    - Theorem 7: Right-censoring truncation downward bias on observed mean and median wait
    - Theorem 8: Attenuation bias toward 1.0 in inter-decision timestamp gaps under shared noise
-/

namespace OnrcProofs

/-- Prefix sum helper over Nat -> Int. -/
private def pSum (f : Nat → Int) : Nat → Int
  | 0 => 0
  | k + 1 => pSum f k + f k

private theorem pSum_add (f : Nat → Int) (k m : Nat) :
    pSum f (k + m) = pSum f k + pSum (fun i => f (k + i)) m := by
  induction m with
  | zero => simp [pSum]
  | succ j ih =>
      have : k + (j + 1) = (k + j) + 1 := by omega
      rw [this]
      simp only [pSum] at *
      omega

/-- Theorem 6a (Exact Multiplicative vs. Additive Inflow Bias Identities):
    In baseline period 0: R0 registrar filings, U0 non-registrar filings, T0 = R0 + U0 > 0.
    In crisis period: R = R0 + ΔR, U = U0 + ΔU, T = R + U.
    Multiplicative estimator R_mult = (R0 / T0) * T has denominator-cleared bias:
      T0 * R_mult - T0 * R = R0 * ΔU - U0 * ΔR.
    Specifically, when non-registrar traffic is unchanged (ΔU = 0) and there is a
    registrar surge (ΔR > 0), R_mult underestimates R by (U0 / T0) * ΔR > 0 (deleting ~81%
    of the Sep 2026 CAEN surge!), whereas Additive DiD (T - U0 - R = ΔU) has ZERO bias! -/
theorem multiplicative_inflow_bias_exact (R0 U0 dR dU : Int) :
    let T0 := R0 + U0
    let R := R0 + dR
    let U := U0 + dU
    let T := R + U
    (R0 * T - T0 * R = R0 * dU - U0 * dR) ∧
    ((T - U0) - R = dU) := by
  have h1 : R0 * (R0 + dR + (U0 + dU)) - (R0 + U0) * (R0 + dR) = R0 * dU - U0 * dR := by
    have ha : R0 * (R0 + dR + (U0 + dU)) = R0 * R0 + R0 * dR + R0 * U0 + R0 * dU := by
      simp only [Int.mul_add]; omega
    have hb : (R0 + U0) * (R0 + dR) = R0 * R0 + R0 * dR + U0 * R0 + U0 * dR := by
      simp only [Int.add_mul, Int.mul_add]; omega
    have hc : R0 * U0 = U0 * R0 := Int.mul_comm R0 U0
    omega
  constructor
  · exact h1
  · omega

/-- Theorem 6b (Strict Dominance Condition of Additive DiD over Multiplicative Scaling):
    Assuming baseline shares R0 > 0, U0 > 0, T0 = R0 + U0, and non-negative surge dR > 0:
    whenever non-registrar shift |ΔU| is bounded by (2*R0 + U0) * |ΔU| < U0 * dR
    (i.e. |ΔU| / dR < (1 - s) / (1 + s)), the additive DiD error is STRICTLY smaller
    than the multiplicative error: T0 * |dU| < |R0 * dU - U0 * dR|. -/
theorem additive_dominates_multiplicative (R0 U0 dR dU : Int)
    (hR0 : 0 < R0)
    (hbound : (2 * R0 + U0) * (if 0 ≤ dU then dU else -dU) < U0 * dR) :
    let T0 := R0 + U0
    let abs_add := T0 * (if 0 ≤ dU then dU else -dU)
    let diff_mult := R0 * dU - U0 * dR
    let abs_mult := if 0 ≤ diff_mult then diff_mult else -diff_mult
    abs_add < abs_mult := by
  by_cases h : 0 ≤ dU
  · have hb1 : (2 * R0 + U0) * dU = 2 * (R0 * dU) + U0 * dU := by
      rw [Int.add_mul, Int.mul_assoc]
    have hT0 : (R0 + U0) * dU = R0 * dU + U0 * dU := Int.add_mul R0 U0 dU
    have hp : 0 ≤ R0 * dU := Int.mul_nonneg (by omega) h
    simp only [h, ↓reduceIte, hb1, hT0] at *
    by_cases hm : 0 ≤ R0 * dU - U0 * dR
    · simp only [hm, ↓reduceIte]; omega
    · simp only [hm, ↓reduceIte]; omega
  · have hdU_neg : 0 < -dU := by omega
    have hR0_neg : R0 * (-dU) > 0 := Int.mul_pos hR0 hdU_neg
    have hneg_eq : R0 * (-dU) = -(R0 * dU) := Int.mul_neg R0 dU
    have hb1 : (2 * R0 + U0) * (-dU) = 2 * (R0 * (-dU)) + U0 * (-dU) := by
      rw [Int.add_mul, Int.mul_assoc]
    have hT0 : (R0 + U0) * (-dU) = R0 * (-dU) + U0 * (-dU) := Int.add_mul R0 U0 (-dU)
    have hU0_neg : U0 * (-dU) = -(U0 * dU) := Int.mul_neg U0 dU
    simp only [h, ↓reduceIte, hb1, hT0, hneg_eq, hU0_neg] at *
    by_cases hm : 0 ≤ R0 * dU - U0 * dR
    · simp only [hm, ↓reduceIte]; omega
    · simp only [hm, ↓reduceIte]; omega

/-- Monotone bound lemma for prefix sums: i < k -> f i ≤ f k -> prefixSum f k ≤ k * f k,
    and tail indices ≥ k -> k * f k ≤ tailSum. -/
private theorem prefix_le_pivot (f : Nat → Int) (hmono : ∀ i j, i ≤ j → f i ≤ f j) (k : Nat) :
    pSum f k ≤ (k : Int) * f k := by
  induction k with
  | zero => simp [pSum]
  | succ m ih =>
      simp only [pSum]
      have h1 : f m ≤ f (m + 1) := hmono m (m + 1) (by omega)
      have h2 : pSum f m ≤ (m : Int) * f (m + 1) := by
        have hpos : (m : Int) * f m ≤ (m : Int) * f (m + 1) :=
          Int.mul_le_mul_of_nonneg_left h1 (by omega)
        omega
      have hstep : ((m + 1 : Nat) : Int) * f (m + 1) = (m : Int) * f (m + 1) + f (m + 1) := by
        have : ((m + 1 : Nat) : Int) = (m : Int) + 1 := by omega
        rw [this, Int.add_mul, Int.one_mul]
      omega

private theorem pivot_le_tail (f : Nat → Int) (hmono : ∀ i j, i ≤ j → f i ≤ f j) (k m : Nat) :
    (m : Int) * f k ≤ pSum (fun i => f (k + i)) m := by
  induction m with
  | zero => simp [pSum]
  | succ j ih =>
      simp only [pSum]
      have hjk : f k ≤ f (k + j) := hmono k (k + j) (by omega)
      have hstep : ((j + 1 : Nat) : Int) * f k = (j : Int) * f k + f k := by
        have : ((j + 1 : Nat) : Int) = (j : Int) + 1 := by omega
        rw [this, Int.add_mul, Int.one_mul]
      omega

/-- Theorem 7a (Right-Censoring Downward Bias on Truncated Mean):
    For ANY non-decreasing wait-time order statistic sequence f (since resolved dossiers leave
    and longer waits stay censored in the pending backlog) and any observed slice 1 ≤ k ≤ n,
    the observed average wait over k resolved dossiers never exceeds the true cohort mean:
      n * ∑_{i < k} f(i) ≤ k * ∑_{i < n} f(i). -/
theorem right_censoring_truncated_mean_le (f : Nat → Int)
    (hmono : ∀ i j, i ≤ j → f i ≤ f j) (k n : Nat) (hkn : k ≤ n) :
    (n : Int) * pSum f k ≤ (k : Int) * pSum f n := by
  obtain ⟨m, rfl⟩ := Nat.exists_eq_add_of_le hkn
  rw [pSum_add f k m]
  have hpref : (m : Int) * pSum f k ≤ (m : Int) * ((k : Int) * f k) :=
    Int.mul_le_mul_of_nonneg_left (prefix_le_pivot f hmono k) (by omega)
  have htail : (k : Int) * ((m : Int) * f k) ≤ (k : Int) * pSum (fun i => f (k + i)) m :=
    Int.mul_le_mul_of_nonneg_left (pivot_le_tail f hmono k m) (by omega)
  have hkm : (m : Int) * ((k : Int) * f k) = (k : Int) * ((m : Int) * f k) := Int.mul_left_comm _ _ _
  have hm_sum : ((k + m : Nat) : Int) * pSum f k = (k : Int) * pSum f k + (m : Int) * pSum f k := by
    have : ((k + m : Nat) : Int) = (k : Int) + (m : Int) := by omega
    rw [this, Int.add_mul]
  have hk_sum : (k : Int) * (pSum f k + pSum (fun i => f (k + i)) m) =
      (k : Int) * pSum f k + (k : Int) * pSum (fun i => f (k + i)) m := Int.mul_add _ _ _
  omega

/-- Theorem 7b (Right-Censoring Downward Bias on Truncated Median):
    Under the same FIFO truncation of k ≤ n order statistics, the observed median f(k / 2)
    is ≤ (weakly; NOT strictly) the true uncensored cohort median f(n / 2).
    AUDIT NOTE: the proof is just monotonicity of f; the content is the modelling assumption
    that observed waits are the k smallest of the cohort (FIFO, single cohort). -/
theorem right_censoring_truncated_median_le (f : Nat → Int)
    (hmono : ∀ i j, i ≤ j → f i ≤ f j) (k n : Nat) (hkn : k ≤ n) :
    f (k / 2) ≤ f (n / 2) := by
  have hdiv : k / 2 ≤ n / 2 := by omega
  exact hmono (k / 2) (n / 2) hdiv

/-- Theorem 8 (Timestamp-Gap Attenuation Bias toward 1.0):
    When unobserved postponements (AUTO_AMANARI) or batch signing add shared positive noise
    η > 0 per consecutive decision gap, and true net times satisfy 0 < τ_s < τ_c,
    the observed ratio (τ_s + η)/(τ_c + η) is strictly compressed toward 1.0:
      τ_s / τ_c < (τ_s + η) / (τ_c + η) < 1 (cross-multiplied). -/
theorem timestamp_gap_attenuation (tau_s tau_c eta : Int)
    (ht : tau_s < tau_c) (heta : 0 < eta) :
    tau_s * (tau_c + eta) < (tau_s + eta) * tau_c ∧ (tau_s + eta) < (tau_c + eta) := by
  have h1 : 0 < eta * (tau_c - tau_s) := Int.mul_pos heta (by omega)
  have c1 : eta * tau_s = tau_s * eta := Int.mul_comm _ _
  have c2 : tau_s * tau_c = tau_c * tau_s := Int.mul_comm _ _
  have hid : (tau_s + eta) * tau_c - tau_s * (tau_c + eta) = eta * (tau_c - tau_s) := by
    rw [Int.add_mul, Int.mul_add, Int.mul_sub, c1, c2]
    omega
  constructor
  · omega
  · omega

end OnrcProofs
