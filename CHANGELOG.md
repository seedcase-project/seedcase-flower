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
