lemma floor_properties (x : Rat) : x.floor ≤ x ∧ x < x.floor + 1 := by
  constructor
  · -- Prove that x.floor ≤ x
    -- This follows from the definition of floor as the greatest integer not exceeding x
    have h : ∃ z, x = x.floor + z ∧ 0 ≤ z ∧ z < 1 := Rat.exists_floor x
    obtain ⟨z, hx, hz_nonneg, hz_lt_one⟩ := h
    rw [hx]
    exact le_add_of_nonneg_right hz_nonneg
  · -- Prove that x < x.floor + 1
    -- This also follows from the floor definition
    have h : ∃ z, x = x.floor + z ∧ 0 ≤ z ∧ z < 1 := Rat.exists_floor x
    obtain ⟨z, hx, hz_nonneg, hz_lt_one⟩ := h
    rw [hx]
    exact add_lt_add_left hz_lt_one x.floor