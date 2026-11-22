/-
  OnrcProofs/AuditChecks.lean   (added by the 21 Nov 2026 adversarial audit)

  A proof of `H → C` is worthless if `H` can never hold (vacuous truth), and a `decide`
  certificate on hand-typed constants says nothing about how close it is to failing.
  This file therefore machine-checks two things:

  Part 1 — NON-VACUITY: every theorem with hypotheses is applied to concrete values that
           satisfy all of its hypotheses (so the hypothesis set is consistent).
  Part 2 — TIGHTNESS / FRAGILITY: for each numeric `decide` witness we prove that a small,
           plausible perturbation of an input makes the claimed inequality FALSE. These are
           the honest error bars of the witnesses; the report text must not present them
           as robust facts.
-/
import OnrcProofs.QueueTheory
import OnrcProofs.CapacityAndMix
import OnrcProofs.EconometricsAndBias
import OnrcProofs.LegalEconomicsSampling

namespace OnrcProofs.AuditChecks
open OnrcProofs

/-! ## Part 1 — non-vacuity witnesses -/

example : lindleyState 0 (fun _ => 1) (fun _ => 0) 3 ≤ lindleyState 0 (fun _ => 2) (fun _ => 0) 3 :=
  lindley_mono 0 0 (fun _ => 1) (fun _ => 2) (fun _ => 0) (fun _ => 0)
    (Int.le_refl _) (fun _ => by simp) (fun _ => Int.le_refl _) 3

example := skorokhod_reflection_exact 5 (by decide) (fun t => if t % 2 = 0 then 3 else -4)

example := cal_wait_le3_iff 2 (fun _ => 1) (fun _ => by simp) 0

example := wait_mono 1 2 (fun _ => 2) (fun _ => 1) 0 3 (by decide) (fun _ _ => by simp)

-- both queues saturated, Δ = 1 actually moved
example := kleinrock_two_class_conservation 10 10 0 0 5 5 1 (by decide) (by decide) (by decide)

-- equal work (1·0+2·2 = 1·2+2·1 = 4), simple share 0 → 2/3: raw count 2 → 3
example : (0 : Int) + 2 < 2 + 1 :=
  simpson_mix_inflation 0 2 2 1 1 2 (by decide) (by decide) (by decide) (by decide)
    (by decide) (by decide) (by decide)

example := weight_misestimation_bias_sign 277 420 450 540 (by decide) (by decide)

example := demand_censoring_mu_max_strict (fun _ => 0) 1 1 0 (by decide) (by decide)

example := rework_multiplier_monotone 4000 780 57 82 (by decide) (by decide) (by decide)

example := additive_dominates_multiplicative 1 4 10 1 (by decide) (by decide)

example := right_censoring_truncated_mean_le (fun i => (i : Int))
  (fun _ _ h => Int.ofNat_le.mpr h) 1 2 (by decide)

example := eu_directive_lower_bound (fun _ => 1) (fun _ => 20) 3 10 2 (fun _ _ => by simp)

example := cost_channels_no_double_count 300 600 10 (by decide) (by decide)

example := manski_short_record_bound 1 2 0 1 (by decide) (by decide) (by decide) (by decide) (by decide) (by decide)

example := cluster_deff_ge_one 2 1 (by decide) (by decide)

/-! ## Part 2 — tightness / fragility of the hand-typed numeric witnesses -/

/-- T3b is a BOUNDARY value, not a robust example: with the same 27.7% → 42.0% mix and
    weight 0.54 a −7.6% true decline is NOT masked (break-even ≈ −7.54%). -/
theorem T3b_fails_at_7_6pct :
    let w : Int := 540
    let avgTau0 : Int := 1000 * 1000 - (1000 - w) * 277
    let avgTau1 : Int := 1000 * 1000 - (1000 - w) * 420
    ¬ (924 * avgTau0 > 1000 * avgTau1) := by
  decide

/-- T3b depends on the simple/complex weight: at w = 0.80 (the alternative weight quoted in
    the T4 docstring) a −7.5% decline is NOT masked (masking limit there is ≈ −3.0%). -/
theorem T3b_fails_at_weight_080 :
    let w : Int := 800
    let avgTau0 : Int := 1000 * 1000 - (1000 - w) * 277
    let avgTau1 : Int := 1000 * 1000 - (1000 - w) * 420
    ¬ (925 * avgTau0 > 1000 * avgTau1) := by
  decide

/-- T3b at the "true" weight 0.45 holds with room to spare (masking limit ≈ −9.3%). -/
theorem T3b_holds_at_weight_045 :
    let w : Int := 450
    let avgTau0 : Int := 1000 * 1000 - (1000 - w) * 277
    let avgTau1 : Int := 1000 * 1000 - (1000 - w) * 420
    925 * avgTau0 > 1000 * avgTau1 := by
  decide

/-- T5c needs 3,744.2 < λ < 3,822.2 at μ = 4,000: a ±1.1% change in λ breaks it.
    λ = 3,830 already makes the 5.7%-rejection regime unstable. -/
theorem T5c_fails_lambda_3830 :
    let u1 : Int := 4000 * (1000000 - 57 * 780)
    ¬ ((3830 * 1000000 : Int) < u1) := by
  decide

/-- λ = 3,740 keeps even the 8.2%-rejection regime stable (no "supercritical transition"). -/
theorem T5c_fails_lambda_3740 :
    let u2 : Int := 4000 * (1000000 - 82 * 780)
    ¬ (u2 < (3740 * 1000000 : Int)) := by
  decide

/-- μ = 3,950 (−1.25%) makes the v1 regime already unstable: the transition claim needs μ
    known to about ±1%. -/
theorem T5c_fails_mu_3950 :
    let u1 : Int := 3950 * (1000000 - 57 * 780)
    ¬ ((3780 * 1000000 : Int) < u1) := by
  decide

/-- T10b robustness (this one IS robust): even taking Channel A at 5% of the NET permanent
    value added (3,808 k RON, regime M5) or at zero (M6), the B + D floor exceeds 5,760 k RON.
    Note: T10b's 10,880 k RON is 5% of GROSS VA on all at-risk turnover (483.6M × 0.45 × 5%),
    not "net VA" as its docstring says. Inputs B/D themselves are model assumptions. -/
theorem T10b_holds_M5_and_M6 :
    (5760 : Int) < 3808 + 4494 + 8467 ∧ (5760 : Int) < 0 + 4494 + 8467 := by
  decide

end OnrcProofs.AuditChecks
