import GinacFFI

def main : IO Unit := do
  IO.println <| myAdd 5 1
  myLeanFun

#eval main
