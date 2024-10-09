# GinacLean

[![build](https://github.com/utensil/ginac-lean/actions/workflows/ci.yml/badge.svg)](https://github.com/utensil/ginac-lean/actions/workflows/ci.yml) [![On Reservoir](https://img.shields.io/badge/On-Reservoir-657584?style=flat)](https://reservoir.lean-lang.org/@utensil/GinacLean)

A work-in-progress Lean 4 binding to [GiNaC](https://www.ginac.de/), which is an open-source symbolic computation library in C++, it has extensive algebraic capabilities, and has been specifically developed to be an engine for high energy physics applications.

See [this doc](doc/ffi.md) to learn more.

## Status

The work started on Sep 18, 2023, and it's still at an early stage, mostly a POC, and nowhere near a complete binding. It's encouraged to draw inspiration from this project, but it's not recommended to use it in production.

This project is still on my thoughts, and I'm still trying to figure out the best way to proceed.

If one is interested in using GiNaC in Lean, discussions are welcome (by opening an issue, or pinging me on Lean Zulip), including about creating other bindings.

## Development

```bash
lake -R build
# Follow https://pre-commit.com/ to install pre-commit
# pyenv shell 3.11
# brew install pre-commit
# pre-commit install
```

## License

TL;DR: Practically, if one uses GinacLean to use GiNaC, one must comply with the GPL license. But this repository itself only contains MIT licensed code.

GinacLean itself is licensed under the MIT license, see [LICENSE](LICENSE) for details. It means any code at rest in this repository can be considered as MIT licensed.

But GiNaC is licensed under the GPL license (version 2 [or later](https://www.ginac.de/pipermail/ginac-list/2024-April/002475.html)), see [COPYING](COPYING) for details. When built or at runtime, GinacLean interacts with the GPL licensed GiNaC library, thus the GPL license applies to all of GinacLean. See [this answer on SE](https://opensource.stackexchange.com/a/4557/35422) for more details.

GiNaC depends on [CLN](https://www.ginac.de/CLN/) which is also GPL licensed. The discussion above applies to CLN as well.

One subtlety is that in [releases of GinacLean](https://github.com/utensil/ginac-lean/releases), GiNaC/CLN might be included (thus redistributed), so any such release should be considered as GPL licensed. But the plan is to make no such releases.
