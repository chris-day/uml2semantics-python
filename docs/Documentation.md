# Documentation maintenance

`docs/` is the maintained documentation source. `zensical.toml` controls the site.
The separate wiki is retained for historical reference; do not maintain parallel
copies. The [migration record](https://github.com/chris-day/uml2semantics-python/tree/main/documentation-migration)
accounts for sources, exclusions, compatibility changes, and verification.

## Setup

Use the repository's existing `.venv`; create it only if absent:

```bash
# Only when .venv does not already exist:
python3 -m venv .venv

.venv/bin/python -m pip install -r requirements-docs.txt
.venv/bin/python -m pip check
```

Python 3.14 is used in CI and was used for migration validation. Installing the
documentation requirements does not replace the application environment.

## Preview and build

```bash
.venv/bin/zensical serve -f zensical.toml
.venv/bin/zensical build -f zensical.toml --clean --strict
.venv/bin/python scripts/check_docs.py
```

The preview at `http://localhost:8000` is local only. Production is configured for
`https://chris-day.github.io/uml2semantics-python/`, inherited from MkDocs and
confirmed reachable during migration. Existing `.html` paths are retained.
`site/` and caches are generated, ignored files.

## Browser checks

```bash
.venv/bin/python -m pip install -r requirements-docs-browser.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python scripts/check_docs_browser.py
```

The browser check serves the site under the production subpath, checks all
Mermaid pages, search, favicon, repository links, and consent states, and records
network requests and local storage. It requires a browser-capable environment.

## Dependency updates

Update the Zensical pin in `requirements-docs.in`, install it in `.venv`, and
regenerate the transitive lock with:

```bash
.venv/bin/python -m pip install --upgrade -r requirements-docs.in
.venv/bin/python scripts/lock_docs.py
.venv/bin/python -m pip install -r requirements-docs.txt
```

Then run the clean strict build, link checks, browser checks, and application
tests before committing the lock. No separate mkdocs-llmstxt package is needed:
Zensical implements the configured export natively. `llms.txt`, `llms-full.txt`,
and page Markdown files are generated under `site/` using the production base URL.

## Deployment and rollback

The existing GitHub Pages workflow builds pull requests without deploying.
Pushes to `main` and manual dispatch build and deploy using the checkout's `.venv`
and pinned requirements. Pages must remain configured to use GitHub Actions.
No hosting settings or remote wiki are changed by the migration.

To roll back after a future deployment, revert the migration commit and rerun
the Pages workflow for that revision. Before committing, the legacy config is
available at `documentation-migration/mkdocs.yml.legacy`; restore it as
`mkdocs.yml` together with the previous workflow and docs from Git. The original
wiki remains available separately. Never deploy both configurations as competing
sources. GitHub Wiki URLs cannot be redirected by this Pages site.
