/-
  OnrcProofs/CapacityAndMix.lean
  Machine-checked proofs for:
    - Theorem 3: Simpson mix inflation & productivity-loss masking
    - Theorem 4: Direction of complexity-weight misestimation bias (telescoping identity)
    - Theorem 5a: Demand-censored v1.0 baseline vs. true max capacity mu_max
    - Theorem 5b: Rework multiplier from higher rejection rates and supercritical regime shift
-/

namespace OnrcProofs

/-- Bilinear algebraic expansion lemma for 2x2 cross-multiplication in Simpson's mix paradox. -/
private theorem mix_cross_identity (s0 c0 s1 c1 ts tc : Int) :
    (ts * s0 + tc * c0) * (s1 + c1) - (ts * s1 + tc * c1) * (s0 + c0) =
      (tc - ts) * (s1 * (s0 + c0) - s0 * (s1 + c1)) := by
  have lhs_exp : (ts * s0 + tc * c0) * (s1 + c1) - (ts * s1 + tc * c1) * (s0 + c0) =
      (tc * (c0 * s1) - tc * (s0 * c1)) - (ts * (c0 * s1) - ts * (s0 * c1)) := by
    rw [Int.mul_add, Int.add_mul, Int.add_mul, Int.mul_add, Int.add_mul, Int.add_mul]
    have a1 : ts * s0 * s1 = ts * (s0 * s1) := Int.mul_assoc _ _ _
    have a2 : ts * s1 * s0 = ts * (s0 * s1) := by rw [Int.mul_assoc, Int.mul_comm s1 s0]
    have a3 : ts * s0 * c1 = ts * (s0 * c1) := Int.mul_assoc _ _ _
    have a4 : tc * c0 * s1 = tc * (c0 * s1) := Int.mul_assoc _ _ _
    have a5 : tc * c0 * c1 = tc * (c0 * c1) := Int.mul_assoc _ _ _
    have a6 : tc * c1 * c0 = tc * (c0 * c1) := by rw [Int.mul_assoc, Int.mul_comm c1 c0]
    have a7 : ts * s1 * c0 = ts * (c0 * s1) := by rw [Int.mul_assoc, Int.mul_comm s1 c0]
    have a8 : tc * c1 * s0 = tc * (s0 * c1) := by rw [Int.mul_assoc, Int.mul_comm c1 s0]
    rw [a1, a2, a3, a4, a5, a6, a7, a8]
    omega
  have rhs_exp : (tc - ts) * (s1 * (s0 + c0) - s0 * (s1 + c1)) =
      (tc * (c0 * s1) - tc * (s0 * c1)) - (ts * (c0 * s1) - ts * (s0 * c1)) := by
    have hm : s1 * (s0 + c0) - s0 * (s1 + c1) = c0 * s1 - s0 * c1 := by
      rw [Int.mul_add, Int.mul_add, Int.mul_comm s1 s0, Int.mul_comm s1 c0]
      omega
    rw [hm, Int.sub_mul, Int.mul_sub, Int.mul_sub]
  rw [lhs_exp, rhs_exp]

/-- Theorem 3a (Simpson Mix Inflation Identity):
    Suppose a workforce delivers identical true service work T₀ = T₁ in two periods,
    with simple dossiers taking τ_s > 0 minutes and complex dossiers τ_c > τ_s minutes.
    If simple share strictly increases (s₁ / N₁ > s₀ / N₀, cleared as s₁ * N₀ > s₀ * N₁),
    then raw output N₁ MUST strictly exceed N₀ with ZERO true capacity gain. -/
theorem simpson_mix_inflation
    (s0 c0 s1 c1 tau_s tau_c : Int)
    (htau_s : 0 < tau_s)
    (htau : tau_s < tau_c)
    (hs0 : 0 ≤ s0) (hc0 : 0 ≤ c0)
    (hN0 : 0 < s0 + c0)
    (hsameWork : tau_s * s0 + tau_c * c0 = tau_s * s1 + tau_c * c1)
    (hmix : s0 * (s1 + c1) < s1 * (s0 + c0)) :
    s0 + c0 < s1 + c1 := by
  have hTpos : 0 < tau_s * s0 + tau_c * c0 := by
    have h1 : 0 ≤ tau_s * s0 := Int.mul_nonneg (by omega) hs0
    have h2 : 0 ≤ tau_c * c0 := Int.mul_nonneg (by omega) hc0
    by_cases hs_zero : s0 = 0
    · have hc_pos : 0 < c0 := by omega
      have h2p : 0 < tau_c * c0 := Int.mul_pos (by omega) hc_pos
      omega
    · have hs_pos : 0 < s0 := by omega
      have h1p : 0 < tau_s * s0 := Int.mul_pos htau_s hs_pos
      omega
  have hrhs_pos : 0 < (tau_c - tau_s) * (s1 * (s0 + c0) - s0 * (s1 + c1)) :=
    Int.mul_pos (by omega) (by omega)
  have hid := mix_cross_identity s0 c0 s1 c1 tau_s tau_c
  have hlhs : (tau_s * s0 + tau_c * c0) * (s1 + c1) - (tau_s * s1 + tau_c * c1) * (s0 + c0) =
      (tau_s * s0 + tau_c * c0) * ((s1 + c1) - (s0 + c0)) := by
    rw [← hsameWork, Int.mul_sub]
  have hprod_pos : 0 < (tau_s * s0 + tau_c * c0) * ((s1 + c1) - (s0 + c0)) := by
    rw [← hlhs, hid]
    exact hrhs_pos
  by_cases hlt : s0 + c0 < s1 + c1
  · exact hlt
  · have hneg : (s1 + c1) - (s0 + c0) ≤ 0 := by omega
    have hmul_le : (tau_s * s0 + tau_c * c0) * ((s1 + c1) - (s0 + c0)) ≤ 0 :=
      Int.mul_nonpos_of_nonneg_of_nonpos (by omega) hneg
    omega

/-- Theorem 3b (ONRC Capacity-Loss Masking Concrete Witness):
    Exact arithmetic proof on empirical ONRC shares (27.7% -> 42.0% simple dossiers,
    at calibrated CAEN/simple weight 0.54x): a -7.5% decline in true equivalent work
    still appears as a strictly positive raw dossier count gain.
    AUDIT NOTE: −7.5% is the BOUNDARY (break-even −7.54%): −7.6% fails, and at weight 0.80 the
    masking limit is only −3.0% (AuditChecks.T3b_fails_at_7_6pct / _at_weight_080). -/
theorem capacity_loss_masking_onrc :
    let w : Int := 540
    let avgTau0 : Int := 1000 * 1000 - (1000 - w) * 277
    let avgTau1 : Int := 1000 * 1000 - (1000 - w) * 420
    925 * avgTau0 > 1000 * avgTau1 := by
  decide

/-- Telescoping algebraic identity for complexity weight bias in scaled form M = K - u * p. -/
private theorem weight_bias_quad_id (K ut ue p0 p1 : Int) :
    (K - ue * p1) * (K - ut * p0) - (K - ut * p1) * (K - ue * p0) =
      K * (ut - ue) * (p1 - p0) := by
  have hswap1 : (ue * p1) * (ut * p0) = (ut * p1) * (ue * p0) := by
    calc (ue * p1) * (ut * p0)
        = ue * (p1 * (ut * p0)) := Int.mul_assoc _ _ _
      _ = ue * (ut * (p1 * p0)) := by rw [Int.mul_left_comm p1 ut p0]
      _ = ut * (ue * (p1 * p0)) := Int.mul_left_comm ue ut (p1 * p0)
      _ = ut * (p1 * (ue * p0)) := by rw [Int.mul_left_comm p1 ue p0]
      _ = (ut * p1) * (ue * p0) := (Int.mul_assoc _ _ _).symm
  have c1 : (ue * p1) * K = K * (ue * p1) := Int.mul_comm _ _
  have c2 : (ut * p1) * K = K * (ut * p1) := Int.mul_comm _ _
  have e1 : (K - ue * p1) * (K - ut * p0) =
      K * K - K * (ut * p0) - K * (ue * p1) + (ue * p1) * (ut * p0) := by
    rw [Int.sub_mul, Int.mul_sub, Int.mul_sub, c1]
    omega
  have e2 : (K - ut * p1) * (K - ue * p0) =
      K * K - K * (ue * p0) - K * (ut * p1) + (ut * p1) * (ue * p0) := by
    rw [Int.sub_mul, Int.mul_sub, Int.mul_sub, c2]
    omega
  have rhs_exp : K * (ut - ue) * (p1 - p0) =
      (K * (ut * p1) - K * (ut * p0)) - (K * (ue * p1) - K * (ue * p0)) := by
    rw [Int.mul_assoc K (ut - ue) (p1 - p0), Int.sub_mul ut ue (p1 - p0)]
    rw [Int.mul_sub ut p1 p0, Int.mul_sub ue p1 p0, Int.mul_sub K, Int.mul_sub K, Int.mul_sub K]
  rw [e1, e2, hswap1, rhs_exp]
  omega

/-- Theorem 4 (Exact Conservative Complexity-Weight Bias Sign):
    When simple share rises (p₁ > p₀) and we use a HIGHER (more conservative) weight w_e > w_t
    (e.g., w_e = 540 or 800 vs true 450), then:
      M(p₁, w_t) * M(p₀, w_e) < M(p₁, w_e) * M(p₀, w_t),
    i.e., E₁(w_e)/E₀(w_e) > E₁(w_t)/E₀(w_t) — conservative weights strictly UNDERSTATE
    any v2.0 productivity decline. -/
theorem weight_misestimation_bias_sign (p0 p1 wt we : Int)
    (hp : p0 < p1) (hw : wt < we) :
    ((1000000 - (1000 - we) * p1) * (1000000 - (1000 - wt) * p0) -
     (1000000 - (1000 - wt) * p1) * (1000000 - (1000 - we) * p0)) =
      1000000 * (we - wt) * (p1 - p0) ∧
    (1000000 - (1000 - wt) * p1) * (1000000 - (1000 - we) * p0) <
      (1000000 - (1000 - we) * p1) * (1000000 - (1000 - wt) * p0) := by
  have hid0 := weight_bias_quad_id 1000000 (1000 - wt) (1000 - we) p0 p1
  have hlin : (1000 - wt) - (1000 - we) = we - wt := by omega
  rw [hlin] at hid0
  refine ⟨hid0, ?_⟩
  have hpos1 : 0 < 1000000 * (we - wt) := Int.mul_pos (by omega) (by omega)
  have hpos2 : 0 < 1000000 * (we - wt) * (p1 - p0) := Int.mul_pos hpos1 (by omega)
  omega

/-- Finite sum of sequence y from 0 to k-1. -/
def prefixSum (y : Nat → Int) : Nat → Int
  | 0 => 0
  | k + 1 => prefixSum y k + y k

/-- Theorem 5a (Demand-Censored v1.0 Output Understates True Max Capacity mu_max):
    If observed daily output on ONRC v1.0 satisfies Y_t = min(D_t, μ₁) ≤ μ₁ for all t < k,
    and at least one day t₀ < k was demand-constrained (D_{t₀} < μ₁), then the sum over
    k days is strictly less than k * μ₁ (observed mean < μ₁). -/
theorem demand_censoring_mu_max_strict (d : Nat → Int) (mu1 : Int) (k t0 : Nat)
    (ht0 : t0 < k) (hslack : d t0 < mu1) :
    prefixSum (fun t => min (d t) mu1) k < (k : Int) * mu1 := by
  have hle_all : ∀ m, prefixSum (fun t => min (d t) mu1) m ≤ (m : Int) * mu1 := by
    intro m
    induction m with
    | zero => simp [prefixSum]
    | succ m ihm =>
        simp only [prefixSum]
        have hm1 : min (d m) mu1 ≤ mu1 := by omega
        have hs : ((m + 1 : Nat) : Int) * mu1 = (m : Int) * mu1 + mu1 := by
          have : ((m + 1 : Nat) : Int) = (m : Int) + 1 := by omega
          rw [this, Int.add_mul, Int.one_mul]
        rw [hs]; omega
  induction k with
  | zero => omega
  | succ n ih =>
      simp only [prefixSum]
      have hterm : min (d n) mu1 ≤ mu1 := by omega
      have hstep : ((n + 1 : Nat) : Int) * mu1 = (n : Int) * mu1 + mu1 := by
        have : ((n + 1 : Nat) : Int) = (n : Int) + 1 := by omega
        rw [this, Int.add_mul, Int.one_mul]
      rw [hstep]
      by_cases heq : t0 = n
      · subst heq
        have hprev := hle_all t0
        omega
      · have ih_n := ih (by omega)
        omega

/-- Theorem 5b (Rework Capacity Loss & Supercritical Regime Transition):
    Net useful capacity U(μ, r, ρ) = μ * (1_000_000 - r * ρ) (in millionths) is strictly
    decreasing in rejection rate r when μ > 0 and re-filing rate ρ > 0. -/
theorem rework_multiplier_monotone (mu rho r1 r2 : Int)
    (hmu : 0 < mu) (hrho : 0 < rho) (hr : r1 < r2) :
    mu * (1000000 - r2 * rho) < mu * (1000000 - r1 * rho) := by
  have h1 : 0 < (r2 - r1) * rho := Int.mul_pos (by omega) hrho
  have h2 : r1 * rho < r2 * rho := by
    have : r2 * rho - r1 * rho = (r2 - r1) * rho := by rw [Int.sub_mul]
    omega
  have h3 : 0 < (1000000 - r1 * rho) - (1000000 - r2 * rho) := by omega
  have h4 : 0 < mu * ((1000000 - r1 * rho) - (1000000 - r2 * rho)) := Int.mul_pos hmu h3
  rw [Int.mul_sub] at h4
  omega

/-- Theorem 5c witness. AUDIT NOTE: rejection 5.7% / 8.2% match the raw archive (57.3 / 81.8 ‰);
    μ = 4,000 and λ = 3,780 are hand-typed; ρ = 0.78 reproduces from the raw BERC JSON
    (77.6–80.4% re-filed within 365 days, independent_audit/check_refiling_rate.py). The claim needs 3,744 < λ < 3,822 at μ = 4,000
    and fails for μ = 3,950 (AuditChecks.T5c_fails_*): it is a ±1% knife-edge. -/
theorem rework_supercritical_onrc_witness :
    let u1 : Int := 4000 * (1000000 - 57 * 780)
    let u2 : Int := 4000 * (1000000 - 82 * 780)
    let lam : Int := 3780 * 1000000
    lam < u1 ∧ u2 < lam := by
  decide

end OnrcProofs
