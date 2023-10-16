# Code generation with Lean 4

Writing the glue code for [FFI](./ffi.md) can be a fun exploration experience at the beginning of the journey, but it can quickly become tedious and error-prone. It's natural that we want to automate the process.

Using some template engine to print the code is a choice but it's bad for maintainability, and still error-prone, only this time, it's even harder to debug because the template engine is not aware of the syntax and semantics of the target language. We did a little experiment with Python for GiNaC with jinja2 and it turns out to be not worth the effort, especially when we have a better alternative: code generation with Lean 4.

Lean 4 itself relies on code generation to work. Lean code gets parsed into `Syntax`, elaborated into `Expr`, and then evaluated and compiled into `IR`(intermediate representation). Lean 4 uses C as its `IR` to make it portable and easier to benefit from other backend optimizations. The C code is then compiled into machine code with LLVM. That's why it comes with a toolchain that can work with C and even C++.

To imagine how Lean 4 code generation could work for FFI glue code generations, we first draw some inspiration from Rust's [FFI](https://doc.rust-lang.org/nightly/nomicon/ffi.html) and its [rust-bindgen](https://github.com/rust-lang/rust-bindgen).

Consider the following Rust code:

```rust
use libc::size_t;

#[link(name = "snappy")]
extern {
    fn snappy_max_compressed_length(source_length: size_t) -> size_t;
}

fn main() {
    let x = unsafe { snappy_max_compressed_length(100) };
    println!("max compressed length of a 100 byte buffer: {}", x);
}
```

The first thing we notice is that the C interface is directly declared in Rust, it's automatically mapped to the corresponding C signature with data types and the calling convention. It's unlike the raw FFI we see in Lean, that we still have to write glue code.

Secondly, the linkage to the C library is declared as `#[link(name = "snappy")]`, then the compiler is instructed to find it following the platform-specific rules then link and load it. Yet in Lean, we still need to write some boilerplate code to load it. Of course, it's great to be able to control compiler and link flags, but the default case should work out-of-box. To make it more difficult, such boilerplate code has to be written in `lakefile.lean` which would orchestrate the whole build process, involving Lean code, C/C++ code are other build targets, thus it's separated from where we declare the FFI interface.

Rust is not satisfied with this, it also reads C header files even C++ header files (only part of the syntax is supported, as C++ syntax surface is massive and rapidly evolving), then generates the corresponding Rust declaration code like above.

After reading the code in `rust-bindgen`, we can see that it's not a trivial task, and we don't want to maintain a C/C++ parser in Lean, it's already done by what it ships with: LLVM+Clang. So we could just reuse it. There are caveats though, the LLVM+Clang is tailored and incomplete for building C++ code, for example it doesn't come with C++ header files, but let's skip the details of setting them up for now.

While we can reuse `libclang` to parse C/C++ header files as we tried with [its Python binding](https://libclang.readthedocs.io/en/latest/), it doesn't have a Lean binding yet and we wish to work natively with Lean. It turns out that we have an immediately available solution which is `clangd`, it's a language server for C/C++ based on `libclang`, and Lean already has rich infrastructure to work with language servers (LS for short) because it relies on LS to provide the interactive experience as an interactvie theorem prover. So we can just reuse the infrastructure to work with `clangd` and it's a much easier task than writing a Lean binding for `libclang`. But we still have to prepare data types in Lean to represent the parsed information, that's still quite some work, but we can selectively prepare for only the part we need for understanding the C/C++ interface.

Let's summarize a bit. In theory now we can use `clangd` to parse C/C++ headers, generate the FFI declarations and glue code.

But why don't we push the experience further, that we simply declare we want to work with a library, say, `xyz`, then we can directly write Lean code, mimicking its C/C++ interface, with the help from our language server which talks to `clangd` and translates the C/C++ interface into Lean interface for code completion and navigation, then our code generation take hints from call site then generate and cache the binding declaration and glue code. We can instantly work with any C/C++ library without creating its binding upfront.

Of course, a more traditional binding can still be generate in a similar approach, the binding developer simply declare some wildcards that match namespaces, classes, functions, operators etc. and serve as the "call site", then anything that match the wildcards and their dependencies will be emitted into Lean code, ready for releasing it as a binding, yet still can be regenerated by tweaking the wildcards.

The above is inspired by [alloy](https://github.com/tydeu/lean4-alloy), which implements a C parser as Lean DSL, then generates the Lean and C glue code for bindings, it uses `clangd` to support the code editing experience in the DSL (code highlight, completion, navigation etc.). But it doesn't support C++ yet (but in its roadmap), and we wish to bypass the part writing a C/C++ parser in Lean. Put it in another way, alloy provides a "C in Lean" to "C as IR" solution, and we want a Lean to "C++ as IR" solution.

The feasibility of hacking `alloy` to support parsing a small subset of C++ then generate C++ IR code has been confirmed by [this quick-and-dirty POC](https://github.com/utensil/lean4-alloy/commit/2dcb4d0f885fd3f5556e81ad891454b7e4993bdf), which parses `new`, `delete`, then generates the corresponding `extern "C"` functions that we can write `new`, `delete` in it.

But how do we write Lean code in the DSL instead of C++ so we don't need a full C++ parser? For now we guess we can make any legal Lean Syntax to be a legal syntax of the DSL, but by inspecting the syntax tree, we can identify the call sites so we can achieve what is described above.

The end-user code might look like this (conceptually, not necessarily syntactically):

```
alloy cpp section

with "xyz"
    from <string> import xyz.string as Xyz.String
    open Xyz

def reverse (str : String) : String :=
    let s := String.mk str
    s.reverse

end
```

where `"xyz"` is the library name (and linkage), `<xyz/string>` is the header file, `xyz` is the namespace, `string` is the class name, `String` is the Lean type name, `reverse` is the method name, `s.reverse` is the call site where the end-user can be prompted by code completion to call non-existing Lean `String.reverse` then everything is automatically generated and when we finish the line, we have called into the C++ `xyz::string::reverse` method.
