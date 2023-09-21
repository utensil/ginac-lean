# C++ FFI to GiNaC: a case study

I'm working on creating a Lean 4 binding to [GiNaC](https://www.ginac.de/), which is an open-source symbolic computation library in C++, it has extensive algebraic capabilities, and has been specifically developed to be an engine for high energy physics applications.

This post intends to discuss the technical details of the FFI to a C++ library, and the challenges I faced during the process.

## Building blocks of GiNaC

GiNaC depends on [CLN](https://www.ginac.de/CLN/). They both use a `autoconf`(i.e. `./configure && make` style) building system. They both make extensive use of the C++ standard library and C++11 features. They both make extensive use of macros and template metaprogramming internally, but thankfully, much less on the API surface. Creating a binding for it is feasible but challenging, as Lean 4 has limited support for C++ FFI as of now.

## Related work

### C++ FFI in Lean 4 and some other languages

### GiNaC Bindings

