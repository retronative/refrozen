# Contributing to reFrozen

Thanks for your interest. reFrozen is an unofficial, pre-release fan project; read the
[README](README.md) and the [disclaimer](docs/disclaimer.md) first.

## Before you start

- **Licence.** reFrozen is GPL-3.0-or-later (see [COPYING](COPYING) and [NOTICE](NOTICE)). By
  contributing, you agree that your contribution is licensed under the same terms. For
  significant work, please open an issue first so we can agree on the change.
- **Security problems** go through private reporting, never a public issue: see
  [SECURITY.md](SECURITY.md).
- **No game files.** Never attach, commit or link game files, maps (`*.w3x`, `*.w3m`), MPQs,
  executables, installers, CD keys or recompiled code, in issues, pull requests or commits. You
  need your own legally obtained copy of the game to build and test reFrozen.
- **No cheats or bypasses.** Contributions that bypass CD-key checks, anti-cheat or
  client-integrity checks, or that target online services, will not be accepted.

## Reporting bugs

Open an issue with your macOS version, Mac model, the commit you built, what you did, what
happened and what you expected. Attach logs and screenshots only if they contain no game files
or keys. Crash reports are saved in `~/Library/Application Support/refrozen/crashes/` (or
`$XDG_DATA_HOME/refrozen/crashes/` when `XDG_DATA_HOME` is set).

## Development

The project layout, setup and test commands are in [AGENTS.md](AGENTS.md). In short:

```sh
scripts/setup_tools.sh   # x86recomp at a pinned commit plus patches/x86recomp/*.patch
```

- Runtime and recompiler changes are patches in `patches/x86recomp/`, each a diff against the
  tree with the earlier patches applied, in order.
- Missing Win32 functions are implemented properly, never stubbed to report success.
- Fix recompiler problems with real fixes (configuration, function bounds, documented patches),
  never by suppressing errors.
- Milestones in [reference/ROADMAP.md](reference/ROADMAP.md) are gated: a criterion passes only
  when it has been observed.

## Tests

Every behaviour change comes with a focused test whose expected values come from an independent
source (Microsoft's documentation, Wine's conformance tests, the ISA manual, published vectors or
the original program's output), never from reFrozen's own output.

New or changed runtime behaviour also needs mutants in `tests/mutants.py`. The mutation gate
(`tests/mutate.py`) plants each one in a scratch copy, and every mutant must be killed by the
tests (or documented as equivalent). Results are recorded in
[reference/TEST_COVERAGE.md](reference/TEST_COVERAGE.md). Never weaken an assertion or change
production behaviour only to make a test pass.

## Commits and pull requests

- One logical change per commit, with a single-line
  [Conventional Commits](https://www.conventionalcommits.org/) message, e.g.
  `fix(runtime): ...` or `docs: ...`.
- Keep pull requests small and focused, describe what you verified and how, and include the
  test output.
- Keep detailed reverse-engineering notes and game addresses out of documentation; describe
  behaviour instead.
