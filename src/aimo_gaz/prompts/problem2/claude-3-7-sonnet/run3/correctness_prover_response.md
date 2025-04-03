theorem correctness
(number: Rat)
: problem_spec implementation number := by
  unfold problem_spec
  
  -- Define the result of our implementation
  let result := implementation number
  
  -- Use the result to instantiate the existential
  use result
  
  -- Simplify
  simp [result]
  
  -- Unfold the implementation
  unfold implementation
  
  -- Now prove the three conditions as a conjunction
  constructor
  
  -- Condition 1: 0 ≤ number - number.floor
  have h1 : number.floor ≤ number := Nat.floor_le number
  have h1' : 0 ≤ number - number.floor := by
    rw [sub_nonneg]
    exact h1
  exact h1'
  
  constructor
  
  -- Condition 2: number - number.floor < 1
  have h2 : number < number.floor + 1 := Nat.lt_floor_add_one number
  have h2' : number - number.floor < 1 := by
    rw [sub_lt_iff_lt_add']
    exact h2
  exact h2'
  
  -- Condition 3: number = number.floor + (number - number.floor)
  have h3 : number.floor + (number - number.floor) = number := by
    rw [add_sub_cancel]
  exact h3