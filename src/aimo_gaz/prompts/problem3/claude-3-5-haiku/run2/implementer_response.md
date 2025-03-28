def implementation (operations: List Int) : Bool :=
  let rec helper (remainingOps: List Int) (currentSum: Int) : Bool :=
    match remainingOps with
    | [] => false
    | x :: xs => 
        let newSum := currentSum + x
        if newSum < 0 then true
        else helper xs newSum
  
  helper operations 0