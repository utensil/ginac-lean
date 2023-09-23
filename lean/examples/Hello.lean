import Ginac

def main : IO Unit := do
  myLeanFun
  let x := Ginac.Symbol.mk "x"
  println! x.name

#eval main
