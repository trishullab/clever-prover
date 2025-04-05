theorem correctness
(number: Rat)
: problem_spec implementation number := by
  -- Unfold the problem specification
  unfold problem_spec
  
  -- Define the result and show it exists
  let result := implementation number
  exists result
  
  -- Introduce the implementation equality
  intro h_impl_eq
  
  -- Unfold the implementation in our hypothesis
  unfold implementation at h_impl_eq
  
  -- Extract properties from the floor_properties lemma
  have floor_le : number.floor ≤ number := (floor_properties number).1
  have number_lt : number < number.floor + 1 := (floor_properties number).2
  
  -- Prove the three required properties
  constructor
  
  -- 1. Prove 0 ≤ result
  · rw [← h_impl_eq]
    simp only [sub_nonneg]
    exact floor_le
  
  constructor
  
  -- 2. Prove result < 1
  · rw [← h_impl_eq]
    have h : number - number.floor < 1 := by
      rw [sub_lt_iff_lt_add]
      exact number_lt
    exact h
  
  -- 3. Prove number = number.floor + result
  rw [← h_impl_eq]
  calc
    number = number.floor + (number - number.floor) := by rw [add_sub_cancel_left]
    _      = number.floor + result := by rw [h_impl_eq]