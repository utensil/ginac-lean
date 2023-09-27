
#include <lean/lean.h>
#include <ginac/ginac.h>
#include "CppClass.h"
using namespace std;
using namespace GiNaC;

extern "C" LEAN_EXPORT lean_obj_res Ginac_Symbol_mk(b_lean_obj_arg _arg_name, b_lean_obj_arg _arg_another) {
    auto _ret_symbol = new symbol(lean_string_cstr(_arg_name), lean_string_cstr(_arg_another));
    return of_cppClass(_ret_symbol);
}
extern "C" LEAN_EXPORT lean_obj_res Ginac_Symbol_name(b_lean_obj_arg _self, b_lean_obj_arg _arg_how, b_lean_obj_arg _arg_are, b_lean_obj_arg _arg_you) {
    auto self = to_cppClass<symbol>(_self);
    auto _ret_std_string = self->get_name(lean_string_cstr(_arg_how), lean_string_cstr(_arg_are), lean_string_cstr(_arg_you));
    return lean_mk_string(_ret_std_string.c_str());
}
