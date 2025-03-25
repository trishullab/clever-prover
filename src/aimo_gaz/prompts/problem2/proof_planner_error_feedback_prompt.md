A prover agent was unable to prove the correctness definition using this plan and the conjectured lemmas below.

Please write a new plan for proving the correctness definition.

[LEMMAS]
-- Conjectured lemmas useful for proving the correctness of the implementation

lemma floor_nonneg {x : Rat} (hx : 0 < x) : 0 ≤ x.floor :=
sorry

lemma floor_le {x : Rat} : x.floor ≤ x :=
sorry

lemma floor_le_of_pos {x : Rat} (hx : 0 < x) : x.floor < x :=
sorry

lemma sub_nonneg_of_le {a b : Rat} (h : a ≤ b) : 0 ≤ b - a :=
sorry

lemma sub_pos_of_pos {a b : Rat} (h1 : 0 < a) (h2 : a < b) : 0 < b - a :=
sorry

lemma truncate_result_eq {x : Rat} : implementation x = x - x.floor :=
sorry

lemma exists_truncated_result {x : Rat} : ∃ r, implementation x = r :=
sorry

lemma truncate_spec {x : Rat} : implementation x = x - x.floor → (x - x.floor) = x - x.floor :=
sorry
[END]