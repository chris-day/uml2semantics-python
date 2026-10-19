# Documentation migration record

## Scope and ownership

Migration inspected on 2026-10-19. Canonical repository:
https://github.com/chris-day/uml2semantics-python (matches origin; no credentials).
`docs/` is the maintained source after migration. The remote wiki and local wiki
are retained unchanged as historical sources; no wiki push, deletion, repository
push, publication, or hosting-setting change is part of this migration.

The user clarified that the supplied path is a wiki source, not a published URL.
The old MkDocs config and Pages workflow establish the intended production URL,
https://chris-day.github.io/uml2semantics-python/. An HTTP HEAD request returned
200 on 2026-10-19. There is no CNAME or custom domain configuration in this
checkout. Preserve the project subpath and `use_directory_urls = false`.

The additional-requirements input contained only a placeholder; no additional
requirement was inferred. No applicable AGENTS.md was present in this checkout.
The untracked GDSN investigation and existing Python caches were not modified.

## Inventory and plan

[map.json](map.json) records every discovered source page and asset, its original
SHA-256, destination, and disposition. It was created before content editing.
Entries for new support pages/assets were added after creation. No bulk page
moves are needed: retain filenames to preserve public `.html` URLs and organize
by explicit navigation instead. No case collisions or attachment/image links
were found in the wiki. The supplied favicon is the only pre-existing image.

| Source | Destination / decision |
| --- | --- |
| `docs/index.md`, local and remote `Home.md` | `docs/index.md`: consolidate introduction, diagram, navigation |
| `Getting-Started.md` in docs and both wikis | Same docs path; installation and CLI corrections |
| `CLI-Usage.md` in docs and both wikis | Same docs path; correct options and validation behavior |
| `Examples.md` in docs and both wikis | Same docs path; retain newer ISO 20022 section from docs |
| `TSV-Specification.md` in docs and both wikis | Same docs path |
| `Choice-Patterns.md` in docs and both wikis | Same docs path |
| `Datatypes-and-Facets.md` in docs and both wikis | Same docs path |
| `Enumerations.md` in docs and both wikis | Same docs path |
| `Annotations.md` in docs and both wikis | Same docs path |
| `Architecture.md` in docs and both wikis | Same docs path; distinguish implementation from extension ideas |
| `Golden-Tests.md` in docs and both wikis | Same docs path |
| `Troubleshooting.md` in docs and both wikis | Same docs path |
| Local wiki `_Sidebar.md` | Navigation input, not a published page |
| Root `README.md` | Concise entry point; API moved to `docs/Python-API.md`, chains to `docs/Property-Chains.md` |
| `examples/README.md` | Retained; corrected placeholder text and linked to examples |
| `CHANGELOG.md`, `LICENSE` | Retained canonical repository files, linked from site |
| `docs/GDSN-TSV-Mapping-v0.1.0.md` | Excluded: untracked investigation with local paths, pending publication review |
| `mkdocs.yml` | Replaced by `zensical.toml`; rollback copy in `mkdocs.yml.legacy` |
| `.github/workflows/docs.yml` | Adapt existing deployment; add PR build/browser checks |
| Supplied `favicon.png` | `docs/assets/images/favicon.png`, byte-identical copy |
| New Mermaid bundle and license | `docs/assets/vendor/mermaid/`, intentionally vendored for privacy |

Excluded from source inventory: `.git`, `.venv`, `build`, `dist`, Python caches,
node dependencies and generated outputs. Application TSV/OWL example data stay
in the repository and are referenced, not copied into the documentation site.
No other maintained documentation directories, custom templates, math notation,
tabs, remote embeds, or wiki assets were discovered. Existing tables, HTML,
code fences and Mermaid diagrams are preserved. The generated site and caches
are ignored rather than committed.

## Wiki verification

The public `.wiki.git` repository was accessible, not absent or auth-blocked.
Remote HEAD: `ff189bcbb114e98918d26a56717364dcb2a24131`.
A temporary clone was compared with `/var/software/gitrepos/uml2semantics-python.wiki`.
All 12 content pages match; only the local `_Sidebar.md` is additional. Existing
`docs/` pages match their wiki counterparts except the newer Examples section and
home page. Both are retained and consolidated; no unique wiki prose discarded.
The original sources remain in the local wiki and remote Git history. GitHub Wiki
URLs cannot be redirected by this Pages site. No site URLs have been moved, so
site redirects are unnecessary.

## Compatibility and content corrections

- Native Zensical search and llmstxt replace MkDocs equivalents; no standalone
  mkdocs-llmstxt installation or preprocessing hook.
- The graph plugin and revision-date plugin have no retained equivalent. The
  existing pipeline diagrams and explicit navigation provide orientation;
  repository history remains the source for revision metadata.
- Remove the minify plugin dependency; use Zensical's own output pipeline.
- Remove the missing `stylesheets/extra.css` reference.
- Convert wiki links to Markdown links; retain headings and page names.
- Correct README's obsolete XMI invocation and nonexistent options. Current
  entry point is TSV-based, `-i` is ontology IRI, `-p` is profile, `--prefixes`
  declares namespaces, and Turtle output requires `--format turtle`.
- Clarify that profiles are currently no-ops, `--no-imports` suppresses explicit
  imports, and `--no-validate` does not bypass builder validation.
- Architecture now identifies the actual builder/loader, explicit format choice,
  propagated exceptions, and graph-equivalence rather than byte determinism.
- Preserve modelling examples and conceptual SHACL extension material. SHACL is
  external/proposed, not an implemented output mode. Example table snippets use
  visual spacing: save real tab-separated input before executing them.
- No copyright owner/year was inferred from the Apache license template. Existing
  author and Henriette Harmse attribution are preserved; Mermaid's MIT license
  and embedded dependency notices are included.

## Privacy decisions

Followed https://zensical.org/docs/setup/data-privacy/.
Native consent offers accept/reject/manage, with GitHub statistics unchecked.
Accept saves selected categories. Reopening is always available in the footer.
No analytics were added. Fonts are local system fonts. Search, favicon, scripts,
and Mermaid 11.17.2 are served locally. Mermaid's automatic unpkg request was
observed in the first browser probe and eliminated by loading the pinned bundle
before diagram rendering. No executable-code, lightbox, or other CDN features are enabled.

The only intended optional external browser service is api.github.com for
repository statistics after consent. Hosting necessarily contacts GitHub Pages;
external text links contact third parties only when followed. Browser storage
holds consent/preferences. Server-side hosting logs and legal policy remain
operator decisions, not a claim of GDPR compliance.

## Dependencies, commands, deployment and rollback

Zensical 0.0.71 is installed only in the healthy repository `.venv` (Python 3.14.4).
Application packages were preserved. `requirements-docs.txt` pins the transitive
documentation closure; optional browser tools are pinned separately. The native
llmstxt implementation is documented at
https://zensical.org/docs/compatibility/mkdocs/plugins/#llmstxt and
https://pawamoy.github.io/mkdocs-llmstxt/.

See [maintenance instructions](../docs/Documentation.md) for exact setup, preview,
build, update, deploy and rollback commands. CI uses the same `.venv`, locks,
config and checks. Existing Pages deployment is retained for main/manual runs;
pull requests build and verify without deployment. Nothing was published here.

## Verification results

- Clean strict build (`zensical build -f zensical.toml --clean --strict`): passes
  with no issues. CLI help was inspected before selecting flags.
- Static checker: 17 HTML pages (including 404), 16 selected Markdown exports;
  internal links, anchors, images, nav, migration destinations, LLM sections,
  production base paths and favicon all pass. `llms-full.txt` is nonempty.
- Browser: all 16 content pages visited; all 12 Mermaid diagrams rendered with
  visible SVGs; no JavaScript errors or HTTP errors. Zensical renders diagrams
  and search in closed shadow roots; the test records references without
  changing their mode. Search for `datatype` returns the datatypes page.
- Favicon: PNG decodes to 57 x 38 pixels, matches supplied bytes, and is linked
  in generated HTML. Repository link is correct; generator notice is absent.
- Consent: before selection no external requests and no consent storage; reject
  saves `{}`; selecting GitHub and accepting saves `{"github":true}` and permits
  only the repository and latest-release API requests; reopening restores the
  selection and rejecting again prevents external requests. See
  [browser-verification.json](browser-verification.json).
- Screenshots inspected: desktop home, migrated TSV specification (tables,
  code fences, diagram) and mobile home; examples screenshot also captured.
  Local screenshots and full test artifacts are under `.cache/docs-verification/`.
- Application: 13 tests pass; sample CLI conversion generates and reparses an
  80-triple Turtle graph. Existing application dependencies remain healthy.
- Migration coverage: all 12 remote wiki pages, 13 local wiki files, maintained
  docs pages, READMEs and canonical repository files accounted for. Excluded
  GDSN draft SHA-256 is unchanged. No unconverted wiki links remain in published
  pages. No missing source attachments or case collisions were discovered.
- `git diff --check` passes. Generated site/cache files are ignored; no unrelated
  application source files were edited. LICENSE and CHANGELOG are untouched.

## Remaining limits

No full ISO 20022 conversion or OWL reasoner run was part of this documentation
migration. Existing modelling prose and examples are preserved; they are not a
formal semantic audit. Blank-node serialisation is not guaranteed byte-stable.
The untracked GDSN draft requires a separate publication review. The extra
requirements placeholder supplies no actionable instruction. Deployment was not
executed; the existing reachable Pages URL is preserved as the production target.
There is no claim that static-site consent controls alone establish legal
compliance. Remote third-party text links were retained, not exhaustively checked
for availability. Wiki redirects require separate owner action on GitHub Wiki.

Reproducibility check: force-reinstalled the exact `requirements-docs.txt` versions
with `.venv/bin/python -m pip install --force-reinstall --no-deps -r requirements-docs.txt`,
then reran `pip check`, the clean strict build, static checks and browser checks.
This reused `.venv` and did not reinstall or remove application packages.
