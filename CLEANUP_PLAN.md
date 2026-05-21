# propel-client cleanup plan

Companion doc for branch `chore/cleanup-deps`. Mirrors the post-Wave-2
shape of `valory-xyz/trader` (and `valory-xyz/mech-client`, which is the
closest library-shaped sibling).

## Goal

Get propel-client onto the same tooling baseline as the rest of the
Valory fleet:

- tomte pinned at `v0.7.0` via `tomte tox` runtime wrapper
- one source of truth for lint config (tomte canonical, layered with a
  small repo-specific overlay)
- no dead scripts, no duplicate config files, no unused dependencies
- workflow calls `tomte tox -e <env>` everywhere

## Starting state (main)

- Already migrated to uv ✓ (PR #20)
- OA pinned at `0.21.22` ✓ (PR #19)
- tomte pinned at `0.6.1` (fleet is on v0.7.0)
- `tox.ini` 257 lines of bespoke `[testenv:*]` recipes — no `tomte tox`
- `setup.cfg` (57 lines) + `.flake8` (5 lines, conflicts with setup.cfg)
- `.gitleaks.toml` is the full 1619-line OA canonical copy
- `scripts/spell-check.sh` exists but no `.spelling` and no testenv —
  dead code
- `scripts/check_copyright.py` + `scripts/freeze_dependencies.py` —
  both replaced by tomte canonical CLI / envs in v0.7.0
- `multiaddr==0.0.9` and `pymultihash==0.8.2` declared in
  `[project.dependencies]` but `grep` finds zero imports — unused
- Workflow installs `tomte[tox]==0.6.1` everywhere

## Target state

| File / artefact | Today | After |
|---|---|---|
| `pyproject.toml` | 48 lines, no `[tool.tomte]`, unused deps | `[tool.tomte]` block, drop unused deps, tomte v0.7.0 pin |
| `tox.ini` | 257-line bespoke | ~45 lines: `[tomte-extensions]`, `[pytest]`, `[mypy*]`, `[Authorized Packages]` |
| `setup.cfg` | 57 lines | **deleted** — tomte canonical handles base lint config |
| `.flake8` | 5 lines (conflicts) | **deleted** |
| `.gitleaks.toml` | 1619-line OA canonical clone | **deleted** — `tomte tox -e gitleaks` reads canonical from tomte |
| `liccheck.ini` | 138 lines | **deleted** — tomte canonical liccheck env carries `[Licenses]`; `[Authorized Packages]` moves to `tox.ini` |
| `scripts/spell-check.sh` | dead | **deleted** |
| `scripts/check_copyright.py` | custom | **deleted** — workflow uses `tomte check-copyright --author valory` |
| `scripts/freeze_dependencies.py` | custom | **deleted** — tomte canonical liccheck env calls `tomte freeze-dependencies` |
| `scripts/` | dir | **deleted** (was only the four files above + `__init__.py`) |
| `AUTHORS.md` | present | **deleted** — trader does not carry one |
| `Makefile` | tox-based formatters/code-checks/security | rewritten to call `tomte format-code`, `tomte check-code`, `tomte check-security` (trader pattern) |
| `CONTRIBUTING.md` | minimal | rewritten to match trader's style, library-flavoured |
| `.github/workflows/main_workflow.yml` | `tomte[tox]==0.6.1` + `tox -e <env>` | `tomte[tox,cli] @ v0.7.0` + `tomte tox -e <env>`; modern runners; full Python matrix 3.10–3.14 |

## Concrete diff summary

**Deleted** (8 files):
`.flake8`, `.gitleaks.toml`, `setup.cfg`, `liccheck.ini`, `AUTHORS.md`,
`scripts/spell-check.sh`, `scripts/check_copyright.py`,
`scripts/freeze_dependencies.py`, `scripts/__init__.py` (and now-empty
`scripts/`).

**Rewritten** (5 files):
`pyproject.toml`, `tox.ini`, `Makefile`, `CONTRIBUTING.md`,
`.github/workflows/main_workflow.yml`.

**Touched** (lint side-effects, kept minimal):
- `propel_client/cli.py`, `propel_client/propel.py`,
  `propel_client/utils.py` — isort reordering (canonical treats
  `propel_client.*` as third-party because `known_first_party=autonomy`),
  plus two `# noqa: E226` annotations on `2**i` exponentiation where
  black and flake8 disagree (canonical does not ignore E226).

**Untouched but flagged:**
- Untracked `propel/` directory (charts, infra, services) in the
  worktree — not part of this cleanup. Decide separately.
- Stale local branch `chore/bump-v0.21.14` — superseded by merged PRs
  #19 and #20. Safe to delete.

## Key `[tool.tomte]` block (decided)

```toml
[tool.tomte]
# No packages/ dir — propel-client is a pure-Python library.
packages_paths = "propel_client"
service_specific_packages = ["propel_client"]
pytest_targets = ["tests"]
open_autonomy_version = "0.21.22"
open_aea_version = "2.2.6"
tomte_dep_pin = " @ git+https://github.com/valory-xyz/tomte.git@v0.7.0"
pylint_disables = [
    "too-many-positional-arguments",
    "too-many-arguments",
    "too-many-lines",
    "C0411",  # canonical isort vs pylint disagreement on propel_client.*
]
```

## Verification (run locally before opening PR)

```
uv lock --check
uv sync --all-groups -v
uv run tomte tox -e bandit
uv run tomte tox -e safety
uv run tomte tox -e black-check
uv run tomte tox -e isort-check
uv run tomte tox -e flake8
uv run tomte tox -e mypy
uv run tomte tox -e pylint
uv run tomte tox -e darglint
uv run tomte tox -e liccheck
uv run tomte tox -e gitleaks
uv run tomte tox -e py3.10-darwin     # unit tests
uv run tomte check-copyright --author valory
```

CI workflow runs the same set in `lock_check`,
`copyright_and_dependencies_check`, `linter_checks`, `scan`, `test`,
gated by `all_checks_passed`.

## Risks

Low overall.

- isort canonical reorders three files (cosmetic only).
- flake8 E226 (not ignored in canonical) → handled with two inline
  `# noqa: E226` annotations on `2**i`. Black wants no spaces, flake8
  default wants spaces; noqa is the standard fleet escape hatch.
- mypy strict canonical flags pre-existing `# type: ignore` markers as
  unused. Handled with `warn_unused_ignores = False` /
  `warn_redundant_casts = False` in the tox.ini `[mypy]` overlay —
  exact pattern mech-client carries.
- pylint C0411 conflict (see above) — disabled at the tomte level via
  `pylint_disables`, mirroring mech-client.

None of these are blocking; each is a one-line follow-up if CI surfaces
something else.

## Decisions confirmed with user (2026-05-21)

1. `CONTRIBUTING.md` — match trader's style.
2. `scripts/__init__.py` — delete.
3. `setuptools==75.3.0` pin — drop, accept that tomte canonical may not
   pin it; revisit only if CI breaks.
4. `AUTHORS.md`, `HISTORY.md` — match trader (delete AUTHORS, keep
   HISTORY).
