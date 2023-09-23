namespace Ginac

opaque SymbolPointed : NonemptyType
def Symbol : Type := (SymbolPointed).type
instance : Nonempty (Symbol) := (SymbolPointed).property

@[extern "GiNaC_symbol_mk"]
opaque Symbol.mk (name : @&String) : Symbol

@[extern "GiNaC_symbol_name"]
opaque Symbol.name : Symbol → String