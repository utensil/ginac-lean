#include <lean/lean.h>
#include <iostream>
#include <ginac/ginac.h>
#include "CppClass.h"
using namespace std;
using namespace GiNaC;

extern "C" uint32_t my_add(uint32_t a, uint32_t b) {
    return a + b;
}

extern "C" lean_obj_res my_lean_fun() {
    symbol x("x"), y("y"), z("z");
    ex MyEx1 = sin(x + 2*y) + 3*z + 41;
    ex MyEx2 = MyEx1 + 1;              

    cout << MyEx2 << endl;

    return lean_io_result_mk_ok(lean_box(0));
}
