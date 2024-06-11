# GinacLean

[![build](https://github.com/utensil/ginac-lean/actions/workflows/ci.yml/badge.svg)](https://github.com/utensil/ginac-lean/actions/workflows/ci.yml)

A work-in-progress Lean 4 binding to [GiNaC](https://www.ginac.de/), which is an open-source symbolic computation library in C++, it has extensive algebraic capabilities, and has been specifically developed to be an engine for high energy physics applications.

See [this doc](doc/ffi.md) to learn more.


## Development

```bash
lake -R build
# Follow https://pre-commit.com/ to install pre-commit
# pyenv shell 3.11
# brew install pre-commit
# pre-commit install
```
