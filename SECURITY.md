# Security policy

## Reporting a vulnerability

Please report security problems privately through GitHub's private vulnerability reporting:
**[Report a vulnerability](https://github.com/retronative/refrozen/security/advisories/new)**
(the repository's **Security** tab, then **Report a vulnerability**). Don't open a public issue,
pull request or discussion for a suspected vulnerability.

Include what you can of:

- the affected component (see Scope) and the commit or build you tested;
- steps to reproduce, and what happens versus what you expected;
- the impact as you understand it, and any suggested fix.

**Never attach game files, maps, CD keys, installers or recompiled code** to a report, even
privately. Describe them instead (name, version, where they are published), or reduce the
problem to a small file of your own.

reFrozen is maintained by volunteers, so responses are best effort. We'll acknowledge the
report, keep you updated in the private advisory, and credit you when a fix is published unless
you'd rather stay anonymous. Please give us a reasonable chance to fix the problem before you
disclose it publicly.

## Supported versions

reFrozen has not made a release yet. Only the `main` branch is supported; fixes land there.

## Scope

In scope: code in this repository and what it builds:

- the runtime patches and Win32 reimplementation (`patches/x86recomp/`), and the game project
  (`src/`, `CMakeLists.txt`);
- the install, patch, lift and audit scripts (`scripts/`), for example unsafe handling of
  installer, archive or map contents;
- the website (`.website/`) and the GitHub Actions workflow (`.github/`).

Out of scope:

- problems in Warcraft III itself, Blizzard Entertainment's services, Battle.net, iCCup or other
  third-party servers; report those to their owners;
- problems that exist only in the upstream projects reFrozen uses (x86recomp, SDL3, Wine and
  others); report those upstream, and tell us if reFrozen is affected;
- requests to bypass CD-key checks, anti-cheat or client-integrity checks; reFrozen doesn't
  bypass them.

reFrozen aims to behave like the original 1.26a client, including how it runs map scripts. Only
play maps from sources you trust.
