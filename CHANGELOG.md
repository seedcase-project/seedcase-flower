# Changelog

Since we follow
[Conventional Commits](https://decisions.seedcase-project.org/why-conventional-commits/)
when writing commit messages, we're able to automatically create formal
releases of the Python package based on the commit messages. The
releases are also published to Zenodo for easier discovery, archival,
and citation purposes. We use
[Commitizen](https://decisions.seedcase-project.org/why-semantic-release-with-commitizen/)
to be able to automatically create these releases, which uses
[SemVar](https://semverdoc.org) as the version numbering scheme.

Because releases are created based on commit messages, we release quite
often, sometimes several times in a day. This also means that any
individual release will not have many changes within it. Below is a list
of the releases we've made so far, along with what was changed within
each release.

## 0.29.0 (2026-06-04)

## 0.28.1 (2026-05-05)

### Fix

- :bug: swap `field-display-names` in multi-page styles (#329)

## 0.28.0 (2026-05-04)

## 0.27.1 (2026-04-30)

### Refactor

- ♻️ simplify style layout of foreign keys (#302)

## 0.27.0 (2026-04-23)

### Feat

- ✨ allow shared templates for built-in styles (#298)

## 0.26.1 (2026-04-15)

### Refactor

- ♻️ import functionals from soil (#289)

## 0.26.0 (2026-04-13)

### Feat

- ✨ `quarto_resource_listing` style (#282)

## 0.25.2 (2026-04-13)

### Refactor

- ♻️ `read_properties()` and `parse_source()` from soil (#273)

## 0.25.1 (2026-04-13)

### Refactor

- ♻️ quarto one page field table column order (#283)

## 0.25.0 (2026-04-13)

### Feat

- ✨ `quarto_resource_tables` style (#268)

## 0.24.0 (2026-04-10)

### Feat

- ✨ indicate which params are positional and which are keyword (#271)

## 0.23.1 (2026-04-08)

### Refactor

- :fire: remove CLI beautification, import from `seedcase-soil` (#254)

## 0.23.0 (2026-03-31)

### Feat

- :sparkles: improve colors used in the CLI help (#245)

## 0.22.0 (2026-03-31)

### Feat

- :sparkles: add `flower` short-form (#244)

## 0.21.5 (2026-03-26)

### Fix

- 🐛 escape newlines to prevent tables breaking (#223)

## 0.21.4 (2026-03-26)

### Refactor

- :pencil2: more explanatory names for args and functions (#233)

## 0.21.3 (2026-03-26)

### Fix

- 🐛 make styles follow commonmark/rumdl format (#222)

## 0.21.2 (2026-03-26)

### Refactor

- ♻️ clarify HTTP errors include other status codes (#227)

## 0.21.1 (2026-03-26)

### Refactor

- ♻️ split the error message for readability (#226)

## 0.21.0 (2026-03-25)

### Feat

- ✨ show better error message when the input is not JSON (#224)

## 0.20.0 (2026-03-25)

### Feat

- ✨ match cyclopts error decorations (#219)

## 0.19.0 (2026-03-25)

### Feat

- ✨ suppress tracebacks from all errors when running from the CLI
  (#216)

## 0.18.0 (2026-03-25)

### Feat

- ✨ prettify error outputs (#200)

## 0.17.1 (2026-03-19)

### Fix

- :bug: use a comment instead of hidden callout to discourage manual
  edits (#205)

## 0.17.0 (2026-03-12)

### Feat

- ✨ implement `Many` (#190)

## 0.16.0 (2026-03-11)

### Feat

- :sparkles: implement `--verbose` (#197)

## 0.15.0 (2026-03-10)

### Feat

- ✨ check correctness of `gh`/`github` sources (#199)

## 0.14.0 (2026-03-10)

### Feat

- ✨ parsing support for `gh:` refs like tags and branches (#192)

## 0.13.0 (2026-03-10)

### Feat

- ✨ add shell completions to CLI (#188)

### Refactor

- 🚚 move `build_sections()` into own file (#182)

## 0.12.2 (2026-03-10)

### Refactor

- :recycle: add callout note to not edit output files (#189)

## 0.12.1 (2026-03-10)

### Refactor

- :recycle: move `parse_source()` into own file (#183)

## 0.12.0 (2026-03-09)

### Feat

- ✨ implement `view` (#176)

## 0.11.0 (2026-03-05)

### Feat

- ✨ implement remote and local datapackage reading (#161)

## 0.10.1 (2026-03-04)

### Refactor

- :recycle: switch from URI to source (#173)

## 0.10.0 (2026-03-03)

### Feat

- ✨ `write_sections()` (#160)

## 0.9.0 (2026-03-03)

### Feat

- ✨ `_build_sections()` (#154)

## 0.8.0 (2026-03-03)

### Feat

- :sparkles: beautify CLI help message (#140)

## 0.7.0 (2026-03-02)

### Feat

- ✨ `_parse_uri()` (#152)

## 0.6.0 (2026-02-23)

### Feat

- :sparkles: add `quarto-one-page` style (#141)

## 0.5.2 (2026-02-20)

### Refactor

- :recycle: extend and fix example `datapackage.json` (#139)

## 0.5.1 (2026-02-19)

### Fix

- :bug: use relative path for `output-path` in docs (#135)

## 0.5.0 (2026-02-18)

### Feat

- ✨ add `Section` and `Content` (#124)

## 0.4.0 (2026-02-18)

### Feat

- :sparkles: add `Config` (#116)

## 0.3.0 (2026-02-18)

### Feat

- :sparkles: add cyclopts skeleton (#117)

## 0.2.0 (2026-02-16)

### Feat

- :sparkles: add skeleton of `build()` (#112)

## 0.1.1 (2026-01-08)

### Fix

- **ci**: 🐛 re-add quartodoc section in Quarto config (#45)
