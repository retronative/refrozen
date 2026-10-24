# AGENTS.md

reFrozen: a static recompilation of *Warcraft III: The Frozen Throne* 1.26a (x86 Win32) to
native arm64 macOS, aimed at playing *DotA Allstars* v6.83. The method and conventions follow
ReCarbon (`../recarbon`); reusable lessons are in `../game-port-knowledge`.

## Workspace

| Path | Role | Rules |
|---|---|---|
| `../recarbon/` | Precedent port (Xbox 360 → arm64) | **Read-only.** Learn from its process, docs and validation; never copy its title-specific hooks or addresses. |
| `../game-port-knowledge/` | Port knowledge base | Read `INDEX.md` and `general/bring-up-checklist.md` before each stage. Follow its `AGENTS.md` to add knowledge. |
| `../DOTA/` | The player's own game installers, client pack and maps | **Read-only.** Never commit anything from it. |
| `game/` | Installed/extracted game files and survey output | git-ignored, proprietary-derived |
| `tools/` | Pinned third-party tool checkouts | git-ignored |
| `reference/` | Feasibility, architecture, roadmap | |

## Conventions

- Milestones (`reference/ROADMAP.md`) are gated. Don't start the next one without the user's
  approval. A criterion passes only when observed, never inferred.
- Label claims in reference docs as in game-port-knowledge: VERIFIED, OBSERVED, HYPOTHESIS,
  FALSIFIED, UNRESOLVED.
- Fix recompiler problems with real fixes (config, function bounds, documented tool patches).
  Never suppress errors.
- Every new instruction gets hand-computed tests, with expected values from the ISA manual,
  never from the recompiler's output.
- Python runs with `/opt/homebrew/bin/python3 -I` on anything that reads game files.

## CD keys and distribution

- The game's CD/install-key flow stays as the original implements it; the port doesn't bypass it.
- Development uses the test keys from the player's readme in `../DOTA/`. Never copy any key into
  this repository, a log, a commit or a doc.
- A distribution never includes a CD key, game code (original or recompiled), assets or maps.
- The player's pipeline is native macOS only: no Wine, VM or Windows tools to install, extract or
  patch their game. Wine (`tools/wine/`) is a development oracle only, e.g. to produce reference
  1.26a binaries that the native installer must reproduce byte for byte.

## Git

- One atomic commit per verified logical change; Conventional Commits, single-line messages,
  no co-author trailers. Review `git status`/`git diff` first.
- Never commit game data, maps (`*.w3x`, `*.w3m`), MPQs, executables, generated code, `game/`,
  `tools/` or build output.
- Commit locally only. Never push, amend or rewrite history without approval.
- Record debugging attempts and findings in `WORKLOG.local.md` (untracked, git-ignored).
