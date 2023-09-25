# Lean FFI to C++: a case study with GiNaC

We are working on creating a Lean 4 binding to [GiNaC](https://www.ginac.de/), which is an open-source symbolic computation library in C++, it has extensive algebraic capabilities, and has been specifically developed to be an engine for high energy physics applications.

This post intends to discuss the technical details of the FFI to a C++ library from Lean 4, and the challenges we faced during the process.

## Building blocks of GiNaC

GiNaC depends on [CLN](https://www.ginac.de/CLN/). They both use a `autoconf`(i.e. `./configure && make` style) building system.

GiNaC also relies on the C++ standard library and utilizes C++11 features. Internally, GiNaC heavily employs macros and template metaprogramming, but thankfully, much less on the API surface. Creating a Lean 4 binding for GiNaC is feasible but challenging due to Lean 4's limited support for C++ FFI at the moment.

## Related work

In this section, we give a non-exhaustive survey on the status quo of creating bindings in Lean 4 or for GiNaC.

### FFI to C++ in Lean 4

Lean 4 manual provides [documents](https://lean-lang.org/lean4/doc/dev/ffi.html) and [an example](https://github.com/leanprover/lean4/blob/master/src/lake/examples/ffi) on FFI to C.

There's [a minimal FFI to C++ example](https://github.com/lecopivo/lean-cpp-ffi) which explores only the basics of calling C++ standard library functions inside a `extern "C"` Lean FFI function.

[EigenLean](https://github.com/lecopivo/EigenLean) gives a complete solution to safely create C++ objects, use them from an opaque Lean type, call C++ methods on them, and safely destroy them via reference counting mechanism available in Lean 4 and destructor mechanism in C++. The solution slightly utilizes C++14 features, thus require a C++14-compatible compiler. One caveat is that the solution is not immediately thread-safe but can be made so easily. And the bonus is it builds all the foundation to call template methods on C++ template classes, which in retrospect, is very natural from Lean's dependent types but technical non-trivial. There are quite a few great header-only libraries could be brought to Lean 4 in the same way. It also settles on a good way to organize the C++ code and the Lean code, as well as some naming conventions (an exotic naming like GiNaC still has its own subtleties, though).

What EigenLean didn't explore, is to work with a non-header-only C++ library, which is the case for GiNaC, as well as many other C++ libraries. One particularly common case is that you have some C++ header and a pre-compiled shared library, whether it's due to the unavailability of the source code, or the difficulties to compile and link, including long compilation time. Its lakefiles is thus very simple and applicable only to libraries with less complications from its source code or binary distribution.

This is mostly covered by [LeanInfer](https://github.com/lean-dojo/LeanInfer), which does a great job to make binary-only runtime to work with Lean, integreated with the Lake's [cloud build releases](https://github.com/leanprover/lean4/tree/master/src/lake#cloud-releases) to bundle binaries like pre-compiled linker-happy shared libraries for supported platforms. 

Some limitations of LeanInfer's solution: At the time of writing, it relies on local builds by the authors, including building LLVM, Clang and its standard library `libc++` from source, no CI has been set up to run this continuously to make it applicable for other projects. It also requires to build the C++ part with `clang++` and its standard library `libc++` on all platforms, which could be chanllenaging for FFI binding developers who are not familiar with C++ toolchains, also some libraries requires heavy patching to compile and link with `libc++` instead of the more widely available `libstdc++` from GNU.

There is also another library worth noticing, [hashbrown4lean](https://github.com/SchrodingerZhu/hashbrown4lean) which successfully creates a Lean 4 binding to the Rust library [hashbrown](https://github.com/rust-lang/hashbrown). Its solution is very similar to EigenLean's, but it also demonstrates how to ensure memory safety, and type correspondance across the FFI boundary bewteen Lean and Rust, which could be inspriring for C++ FFI binding developers as well.

### FFI to C++ in some other languages

In general, creating a binding to a C++ library requires a C shim layer, which is the only universal ABI to talk between languages. So the task boils down to creating a C style interface to the C++ library which faithfully represents the C++ API, make it available as a low-level interface in the target language, and then create a high-level interface in the target language to make it more idiomatic to use.

These tasks are non-trival and tedious. The only fun may be designing the idiomatic high-level interface in the target language, which is the only part that is not mechanical, and could be very different from the original C++ API. That's why people tend to create code generators to automate the process.

[SWIG](http://www.swig.org/) is a popular code generator for creating bindings to C and C++ libraries. It supports many target languages, including Python, Ruby, Java, C#, Go, etc. Its own C++ parser supports many but not all C++ features, but as C++ has been greatly evolved in the last decade, good libraries might have been utilizing these new features, not only internally but also on the API surface. It would be hard to assess upfront whether SWIG is a good fit for a particular C++ library.

For popular languages like Python and Node.js, there are many solutions to create bindings to C++ libraries, also for Rust libraries nowadays. Enumerating them is out of the scope of this post. The gist of these solutions are to parse C/C++ header files, align the primitive and composite types, align the way to call functions and efficiently pass things around, then using a template to generate the target language code.

To avoid playing catch-up with C++ features, it's not recommended to write a C++ parser manually, but to use a C++ compiler to do the job. [libclang](https://clang.llvm.org/doxygen/group__CINDEX.html) is a popular choice, which is a C API to the C++ compiler [Clang](https://clang.llvm.org/). It also has a idiomatic (or "pythonic") Python binding [clang.cindex](https://libclang.readthedocs.io/en/latest/) with [bundled libclang binaries](https://github.com/sighingnow/libclang), which is very convenient to use. Its [Rust low-level binding](https://github.com/KyleMayes/clang-sys) has been used in [rust-bindgen](https://github.com/rust-lang/rust-bindgen), the same author has a [Rust high-level binding](https://github.com/KyleMayes/clang-rs) but [not used in `rust-bindgen`](https://github.com/rust-lang/rust-bindgen/issues/55#issuecomment-255295325).

We also expect the code generators can help with translating the unit tests in C++ and documentations to C++ comments to the target language, the former is not seen in the existing solutions while the latter is relatively easy and common. This is feasible if we use `libclang` because it can parse C++ source code as well. The difficulty comes from the fact that C++ unit test frameworks make heavy use of macros which is expanded to implementation details by `libclang`, we need a way to recover its original intent for mapping the unit test cases.

### GiNaC Bindings

Existing GiNaC bindings to other languages are the source of inspirations for designing the high-level interface, handling interoperability subtilities, and tooling.

[PyGiNaC](https://pyginac.sourceforge.net/) is the Python binding, which resembles the C++ API closely, only with some Pythonic tweaks. Users can reuse examples in the GiNaC tutorial easily, with [a few easy-to-remember modifications](https://moebinv.sourceforge.net/pyGiNaC.html#similarity). It also provides its own tutorial as [a Colab notebook](https://colab.research.google.com/github/vvkisil/MoebInv-notebooks/blob/master/Geometry_of_cycles/Start_from_Basics/pyGiNaC.ipynb). It uses the [Boost.Python](http://www.boost.org/libs/python/doc/index.html) library to implement the binding thus less applicable to other target languages.

[ginac-wasm](https://github.com/Daninet/ginac-wasm) is a WebAssembly binding which also has [a fun demo web page](https://daninet.github.io/ginac-wasm/) that loads in a blink of an eye. Calls to GiNaC functions made in the JavaScript end (written in TypeScript) are encoded into a representation that fits in a `Uint8Array` buffer and passed to a few `extern C`-style entry functions exposed to the WebAssembly module that accepts such buffer. All functions are implemented both in TypeScript and C++ FFI glue code to handle encoding, decoding and calling the GiNaC C++ functions. Finally it uses [Emscripten](https://emscripten.org/) with docker to compile GiNaC and the FFI glue code to WebAssembly. This method is interesting but less efficient and desirable. It also didn't make use of techniques like [AssemblyScript](https://www.assemblyscript.org/) to ease the process.

There's no Rust binding found, and its [Haskell FFI binding](https://github.com/laserpants/bindings-ginac) is experimental and dated.

## Challenges

We have to get back to writing this section as we have resolved all issues that are roadblocks to this project with the help from [Zulip](https://leanprover.zulipchat.com/#narrow/stream/270676-lean4/topic/.E2.9C.94.20FFI.20to.20C.2B.2B.3A.20GiNaC), and some aspects the issues are already discussed above or in the Zulip thread.

There are quite a few issues to investigate and reproduce in minimal settings, to isolate the direct cause and find a best practice or an appropriate fix. We'll get back to them.

## What has been done in this project

This project is a work-in-progress, in case it would help others, so far it has successfully explored the following aspects, which are essential basics for similar projects:

- compile `GiNaC` and its dependency `CLN` with `clang++` and `libstdc++` from GNU as it fails to compile with `libc++` from LLVM without heavy patching
  - check `scripts/build_ginac.sh` for details, a few minor patches are applied
- make `GiNaC` with `libstdc++` compile and link with Lean FFI glue code which seems to require linking with `libc++` from LLVM as well, this completes the call chain `Lean -> FFI C++ glue code -> C++ GiNaC code -> GNU C++ stdlib`
  - check `lakefile.lean` for details, it's adapted from `LeanInfer`'s `lakefile.lean`
- map a few GiNaC C++ APIs to Lean opaque types and opaque functions on it following the practice of EigenLean, which applies to almost all other classes and methods in GiNaC, this improves the previous call chain to `Idiomatic Lean -> Lean FFI glue code -> C++ GiNaC code -> GNU C++ stdlib`
  - check `lean/` and `cpp/` for details
- use the Python binding of `libclang` to parse GiNaC headers, and have identified the required elements for generating the Lean interface of these opaque types and functions
  - check `codegen/parse.py` for details
- set up a CI to pass under both Ubuntu and Mac OS (Windows support is in similar spirit but it's not a priority for now), which caches the compilation product of C++ CLN&GiNa but rebuild everything for C++ FFI glue code and Lean code, this shortens the build time from 25min to less than 10min (which includes running C++ test cases, close to the run time of Lean test cases yet to be generated) but also ensures modifications to lakefile, FFI&Lean code are continuously verified as we will tweak them a lot
  - check `.github/workflows/ci.yml` for details

A few major TODOs, these might be interesting goals for similar projects:

- ensure it continues to work with newer Lean and Lake
- finish automatically generating the Lean interface of the opaque types and functions, along with documents
- figure out automatically generating the Lean test cases from the C++ unit tests
- design and implement a DSL directly embeded in Lean to call GiNaC functions
- make GiNaC available to Lean tactics, where CAS style manipulations are possibly useful
- make the DSL somehow work with Lean theorems and tactics, like they can reference the same variables (symbols) and propositions (formulas)

Some possible future explorations:

- the binding generating capability can become a spin-off project, which can be reused in other Lean 4 binding projects
- explore creating bindings to Rust libraries(e.g. [egglog](https://github.com/egraphs-good/egglog/)) and making them idiomatic in Lean, like [egglog's Python binding](https://egg-smol-python.readthedocs.io/en/latest/)
- explore reverse-FFI, i.e. calling Lean functions from C++/Rust code, even from JavaScript in the browser provided [Lean 4 WASM build makes progress](https://leanprover.zulipchat.com/#narrow/stream/270676-lean4/topic/wasm.20build)


