# Releasing

How a release is cut in this repository, and why there are no `make` targets for it.

## The flow

1. **`/release` (rhiza-claude)** derives the next version, rewrites
   `[project].version` in `pyproject.toml`, regenerates `CHANGELOG.md` with
   [git-cliff](https://git-cliff.org/) from `cliff.toml`, and creates the tag
   locally — all in a single commit, so the tagged commit already carries its own
   changelog entry.
2. **Pushing the tag** triggers `.github/workflows/rhiza_release.yml`, which
   regenerates the release notes for that tag (`uvx git-cliff --latest`) and
   publishes the GitHub release.

Version bumping and tagging are deliberately *not* `make` targets. Keeping them in
one command is what lets the bump, the changelog and the tag land together; a
sequence of make targets would let a release be cut with a stale or missing
changelog entry.

`[tool.bumpversion]` in `pyproject.toml` carries the matching rationale: there is no
`current_version` key, because bump-my-version reads and rewrites the PEP 621
`[project].version` natively, so the version string is declared in exactly one place
and cannot go stale.

## Checking on a release

| What you want | Command |
| --- | --- |
| Recent runs of the release workflow | `make workflow-status` |
| The latest published release | `make latest-release` |

Both come from `.rhiza/make.d/github.mk`.

## Two targets that used to exist

Until the rhiza template reached v1.3.3 this repo carried
`.rhiza/make.d/releasing.mk`, which provided:

- **`make changelog`** — ran `git-cliff --output CHANGELOG.md` by hand. Superseded by
  `/release`, which regenerates the changelog as part of the version bump, and by
  `rhiza_release.yml`, which regenerates the release notes in CI. Running it
  standalone risked a `CHANGELOG.md` that disagreed with the tag.
- **`make release-status`** — paged `workflow-status` followed by `latest-release`.
  Both targets survive individually in `github.mk`; only the combined pager view is
  gone.

The template dropped that file when releasing moved into the rhiza-claude `/release`
command, but a v1.2.1 sync-conflict resolution resurrected it locally. Because
`.rhiza/rhiza.mk` includes `.rhiza/make.d/*.mk` by glob rather than by the manifest in
`.rhiza/template.lock`, the orphan kept loading — frozen at its v1.2.1 content, and
invisible to `/rhiza:update`, which only refreshes files the lock names. It was
removed in #521.

`cliff.toml` stays: it is still template-owned, and `rhiza_release.yml` reads it.
