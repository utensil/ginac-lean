import GinacFFI

def main : IO Unit := do
  myLeanFun
  let x := GiNaC.Symbol.mk "x"
  println! x.name

#eval main
