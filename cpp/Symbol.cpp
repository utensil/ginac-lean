#include <lean/lean.h>
#include <ginac/ginac.h>
#include "CppClass.h"
using namespace std;
using namespace GiNaC;

extern "C" LEAN_EXPORT lean_obj_res Ginac_Symbol_mk(b_lean_obj_arg name) {
    auto sym = new symbol(lean_string_cstr(name));
    return of_cppClass(sym);
}

extern "C" LEAN_EXPORT lean_obj_res Ginac_Symbol_name(b_lean_obj_arg _sym) {
    auto sym = to_cppClass<symbol>(_sym);
    return lean_mk_string(sym->get_name().c_str());
}

