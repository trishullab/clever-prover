def implementation (operations: List Int) : Bool :=
  let rec process (ops: List Int) (balance: Int) : Bool :=
    match ops with
    | [] => false  -- No more operations, balance never went below zero
    | op :: rest =>
      let newBalance := balance + op
      if newBalance < 0 then
        true  -- Balance fell below zero
      else
        process rest newBalance  -- Continue with the rest of the operations
  
  process operations 0  -- Start with balance = 0