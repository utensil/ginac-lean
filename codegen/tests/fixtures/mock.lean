
import Ginac.Dep

namespace Ginac

opaque SymbolPointed : NonemptyType
def Symbol : Type := (SymbolPointed).type
instance : Nonempty (Symbol) := (SymbolPointed).property

@[extern "Ginac_Symbol_mk"]
opaque Symbol.mk (name : @&String) (another : @&String) : Symbol

@[extern "Ginac_Symbol_name"]
opaque Symbol.name (how : @&String) (are : @&String) (you : @&String) : String


end Ginac
