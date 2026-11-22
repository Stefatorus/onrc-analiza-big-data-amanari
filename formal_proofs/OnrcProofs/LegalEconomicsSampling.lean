/-
  OnrcProofs/LegalEconomicsSampling.lean
  Machine-checked proofs for:
    - Theorem 9: Strict EU Directive 2019/1151 breach lower bound under unobserved payment lag
    - Theorem 10: Cost channel non-double-counting, monotonicity in backlog, and 95% macro
                  substitution deadweight floor vs. 5.76 mil. RON OUG budget
    - Theorem 11a: Manski non-parametric bound for BERC API short-response records
    - Theorem 11b: Cluster sampling Design Effect DEFF >= 1 for 545 PDF bulletins
-/

namespace OnrcProofs

/-- Count indices i < n satisfying predicate P i. -/
def countPred (P : Nat → Bool) : Nat → Nat
  | 0 => 0
  | n + 1 => countPred P n + if P n then 1 else 0

/-- Theorem 9 (Strict Lower Bound on EU Directive 2019/1151 Violations):
    If observed total wait W_total(i) = pay_lag(i) + proc(i) and every eligible J formation
    satisfies 0 ≤ pay_lag(i) ≤ B (payment/completion buffer, e.g. B = 2 or 5 workdays),
    then the count with W_total(i) > L + B is a STRICT LOWER BOUND on true violations
    proc(i) > L from the Directive clock start.
    AUDIT NOTE: the bound is weak (≤), not strict, and is only as good as the UNVERIFIABLE
    hypothesis pay(i) ≤ B and the decomposition W_total = pay + proc (no other non-ONRC time
    inside W_total; postponed dossiers are excluded upstream). Legal scope (online SRL
    formation, 5 vs 10 wd) is not modelled here. -/
theorem eu_directive_lower_bound (pay proc : Nat → Nat) (n L B : Nat)
    (hB : ∀ i, i < n → pay i ≤ B) :
    countPred (fun i => decide (L + B < pay i + proc i)) n ≤
      countPred (fun i => decide (L < proc i)) n := by
  induction n with
  | zero => simp [countPred]
  | succ m ih =>
      have hm := ih (fun i hi => hB i (by omega))
      have hpay_m := hB m (by omega)
      simp only [countPred]
      by_cases h1 : L + B < pay m + proc m
      · have h2 : L < proc m := by omega
        simp [h1, h2]
        omega
      · by_cases h2 : L < proc m
        · simp [h1, h2]
          omega
        · simp [h1, h2]
          omega

/-- Theorem 10a (Channel Non-Double-Counting & Backlog Cost Monotonicity):
    If Channel B share s_B ≥ 0 and disjoint Channel C share s_C ≥ 0 satisfy s_B + s_C ≤ 1000
    (permille), no modification delay day D ≥ 0 is counted in both channels:
      s_B * D + s_C * D ≤ 1000 * D.
    Furthermore, marginal daily economic exposure grows strictly with pending stock L
    whenever per-unit marginal cost rate m > 0.
    AUDIT NOTE: disjointness of the channels is ASSUMED via hsum, not verified; the theorem
    is the tautology "shares summing to ≤ 1 give a weighted sum ≤ total". Whether the
    pipeline's channel definitions really are disjoint must be checked in audit_costs.py. -/
theorem cost_channels_no_double_count (sB sC D : Int)
    (hsum : sB + sC ≤ 1000) (hD : 0 ≤ D) :
    sB * D + sC * D ≤ 1000 * D := by
  have h1 : 0 ≤ (1000 - (sB + sC)) * D := Int.mul_nonneg (by omega) hD
  have h2 : (1000 - (sB + sC)) * D = 1000 * D - (sB * D + sC * D) := by
    rw [Int.sub_mul, Int.add_mul]
  omega

theorem cost_monotone_in_backlog (L1 L2 rate fixed_obs : Int)
    (hL : L1 < L2) (hrate : 0 < rate) :
    fixed_obs + L1 * rate < fixed_obs + L2 * rate := by
  have h : 0 < (L2 - L1) * rate := Int.mul_pos (by omega) hrate
  rw [Int.sub_mul] at h
  omega

/-- Theorem 10b (95% Macroeconomic Substitution Deadweight Floor > 5.76 mil. RON OUG Budget):
    Even if 95% of all delayed new-firm turnover (Channel A) is fully offset by competitors
    in the macroeconomy (leaving only 5% net VA deadweight loss = 10.88M RON in central),
    plus direct Channel B ANAF reactivation costs (4.494M RON) and Channel D avoidable rework
    (8.467M RON) strictly exceeds the 5.76 mil. RON 2027 OUG budget (23.84M vs 5.76M RON).
    AUDIT NOTE: `decide` only adds four hand-typed numbers. 10,880 k = 5% of GROSS VA on all
    at-risk turnover (483.6M × 0.45 × 0.05), not "net VA"; with net permanent VA (M5, 3,808 k)
    or zero Channel A (M6) the inequality still holds (AuditChecks.T10b_holds_M5_and_M6).
    B and D are themselves model outputs from assumed unit costs (audit_costs.py). -/
theorem macro_substitution_floor_gt_oug_budget :
    let ougBudgetK : Int := 5760
    let channelA_5pctVA_K : Int := 10880
    let channelB_direct_K : Int := 4494
    let channelD_rework_K : Int := 8467
    ougBudgetK < channelA_5pctVA_K + channelB_direct_K + channelD_rework_K := by
  decide

/-- Theorem 11a (Manski Non-Parametric Bound for API Short-Response Records):
    Let n > 0 be returned records with k ∈ [0, n] events, and m ≥ 0 be reported-but-unreturned
    ("short") records with unknown j ∈ [0, m] true events.
    Then without ANY MCAR or distributional assumption, the difference between observed rate k/n
    and full-universe rate (k+j)/(n+m) is bounded by m/(n+m):
      |k * (n + m) - (k + j) * n| ≤ m * n. -/
theorem manski_short_record_bound (k n j m : Int)
    (hk0 : 0 ≤ k) (hkn : k ≤ n) (hj0 : 0 ≤ j) (hjm : j ≤ m) (hn : 0 < n) (hm : 0 ≤ m) :
    let num := k * (n + m) - (k + j) * n
    let abs_num := if 0 ≤ num then num else -num
    abs_num ≤ m * n := by
  have hid : k * (n + m) - (k + j) * n = k * m - j * n := by
    rw [Int.mul_add, Int.add_mul]
    omega
  have h1 : 0 ≤ k * m := Int.mul_nonneg hk0 hm
  have h2 : k * m ≤ n * m := Int.mul_le_mul_of_nonneg_right hkn hm
  have h3 : 0 ≤ j * n := Int.mul_nonneg hj0 (by omega)
  have h4 : j * n ≤ m * n := Int.mul_le_mul_of_nonneg_right hjm (by omega)
  have hcomm : n * m = m * n := Int.mul_comm n m
  by_cases hsign : 0 ≤ k * (n + m) - (k + j) * n
  · simp [hsign]; omega
  · simp [hsign]; omega

/-- Exact numeric certificate for BERC 2023–2026 archive:
    4,093,329 returned vs 15,627 reported-but-not-returned -> Manski worst-case bound < 0.39 pp!
    AUDIT NOTE: constants match coverage_by_day.csv (re-derived in DataWitnesses.lean). The bound
    covers only `records_short`; 317 category-days of 2023 (217 on working days) are status
    "missing" with UNKNOWN counts, so it is assumption-free for 2024–2026 only. It is a
    whole-archive bound: single category-days reach 11.7% short (CERERE265, 31.03.2026). -/
theorem manski_berc_archive_under_39bps :
    15627 * 10000 < 39 * (4093329 + 15627) := by
  decide

/-- Theorem 11b (PDF Bulletin Cluster Design Effect >= 1):
    For mean bulletin cluster size m ≥ 1 and intra-cluster correlation ρ ≥ 0 (scaled),
    the Design Effect DEFF = 1000 + (m - 1) * ρ ≥ 1000, so cluster-robust SE strictly
    dominates naive i.i.d. binomial SE whenever m > 1 and ρ > 0.
    AUDIT NOTE: the analysis uses 530 matched bulletins (545 PDFs on disk), not 545. The formula
    1 + (m̄−1)ρ assumes equal cluster sizes; with the actual very unequal sizes the empirical
    DEFF = (SE_cluster/SE_iid)² ≈ 1.75, not the reported 1.26. ρ ≥ 0 is assumed (ICC can be < 0). -/
theorem cluster_deff_ge_one (m rho : Int) (hm : 1 ≤ m) (hrho : 0 ≤ rho) :
    1000 ≤ 1000 + (m - 1) * rho ∧ (1 < m → 0 < rho → 1000 < 1000 + (m - 1) * rho) := by
  have hnonneg : 0 ≤ (m - 1) * rho := Int.mul_nonneg (by omega) hrho
  constructor
  · omega
  · intro hm1 hr1
    have hpos : 0 < (m - 1) * rho := Int.mul_pos (by omega) hr1
    omega

end OnrcProofs
