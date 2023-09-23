@[extern "my_add"]
opaque myAdd : UInt32 → UInt32 → UInt32

@[extern "my_lean_fun"]
opaque myLeanFun : IO PUnit

namespace GiNaC

opaque SymbolPointed : NonemptyType
def Symbol : Type := (SymbolPointed).type
instance : Nonempty (Symbol) := (SymbolPointed).property

@[extern "GiNaC_symbol"]
opaque Symbol.mk (name : @&String) : Symbol

@[extern "GiNaC_symbol_name"]
opaque Symbol.name : Symbol → String