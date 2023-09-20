import GinacFFI

def main : IO Unit :=
  IO.println <| myAdd 5 1

#eval main