

<p align="center">
    <a href="https://flower.seedcase-project.org/">
        <img src="https://raw.githubusercontent.com/seedcase-project/seedcase-flower/main/_extensions/seedcase-project/seedcase-theme/logos/flower/navbar.svg" alt="Link to Flower website" height="150"/>
    </a>
</p>

# seedcase-flower: Turn your Data Package metadata into human-readable documentation

<!-- TODO: Include DOI after uploading -->

<!-- [![PyPI Version](https://img.shields.io/pypi/v/seedcase-flower.svg)](https://pypi.org/project/seedcase-flower/) -->

[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-teal.json?raw=true.svg)](https://github.com/copier-org/copier)
[![Python Version from PEP 621
TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https://raw.githubusercontent.com/seedcase-project/seedcase-flower/refs/heads/main/pyproject.toml)](https://github.com/seedcase-project/seedcase-flower/blob/main/pyproject.toml)
[![GitHub
License](https://img.shields.io/github/license/seedcase-project/seedcase-flower.svg)](https://github.com/seedcase-project/seedcase-flower/blob/main/LICENSE.md)
[![GitHub
Release](https://img.shields.io/github/v/release/seedcase-project/seedcase-flower.svg)](https://github.com/seedcase-project/seedcase-flower/releases/latest)
[![Build
documentation](https://github.com/seedcase-project/seedcase-flower/actions/workflows/build-website.yml/badge.svg)](https://github.com/seedcase-project/seedcase-flower/actions/workflows/build-website.yml)
[![Check
package](https://github.com/seedcase-project/seedcase-flower/actions/workflows/check-package.yml/badge.svg)](https://github.com/seedcase-project/seedcase-flower/actions/workflows/check-package.yml)
[![OpenSSF
Scorecard](https://api.scorecard.dev/projects/github.com/seedcase-project/seedcase-flower/badge?raw=true.svg)](https://scorecard.dev/viewer/?uri=github.com/seedcase-project/seedcase-flower)
[![CodeQL](https://github.com/seedcase-project/seedcase-flower/actions/workflows/github-code-scanning/codeql/badge.svg?branch=main)](https://github.com/seedcase-project/seedcase-flower/actions/workflows/github-code-scanning/codeql)
[![code
coverage](https://raw.githubusercontent.com/seedcase-project/seedcase-flower/coverage/coverage.svg?raw=true)](https://htmlpreview.github.io/?https://raw.githubusercontent.com/seedcase-project/seedcase-flower/coverage/index.html)
[![pre-commit.ci
status](https://results.pre-commit.ci/badge/github/seedcase-project/seedcase-flower/main.svg)](https://results.pre-commit.ci/latest/github/seedcase-project/seedcase-flower/main)
[![lifecycle](https://lifecycle.r-lib.org/articles/figures/lifecycle-experimental.svg)](https://lifecycle.r-lib.org/articles/stages.html#experimental)
[![Project Status: WIP – Initial development is in progress, but there
has not yet been a stable, usable release suitable for the
public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
<!-- [![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active) -->

Create human-friendly documentation from your machine-readable Data
Package metadata (kept within `datapackage.json`). Flower does two
things:

- Display the metadata in a nicer way on the Terminal with the `view`
  command
- Generate documentation files using built-in or custom styles with the
  `build` command.

For building documentation, Flower reads the metadata and outputs it
into a nicer, more human-centric format. You can choose how you want the
output to look and be structured by using either built-in styles or
custom styles defined by you. By default, it outputs Markdown files that
you can then use to create a website, a PDF, or any other format you
want by using other tools like [Quarto](https://quarto.org/).

Check out the [website](https://flower.seedcase-project.org/) for more
information about the project, including the design of it, how to use
it, and a reference to the API.

> [!TIP]
>
> This Python package was generated from the
> [`template-python-package`](https://github.com/seedcase-project/template-python-package)
> Seedcase template :tada:

## Project files and folders

- `.github/`: Contains GitHub-specific files, such as issue and pull
  request templates, workflows,
  [dependabot](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/dependabot-quickstart-guide)
  configuration, pull request templates, and a
  [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
  file.
- `tools/vulture-allowlist.py`: List of variables that shouldn’t be
  flagged by [Vulture](https://github.com/jendrikseipp/vulture) as
  unused.
- `tools/get-contributors.sh`: Script to get list of project
  contributors.
- `tests/`: Test files for the package.
- `src/`: Source code for the package.
- `docs/`: Documentation about using and developing the Python package.
- `_renderer.py`: Custom
  [`quartodoc`](https://machow.github.io/quartodoc/) renderer.
- `pytest.ini`: Pytest configuration file.
- `mypy.ini`: [`mypy`](https://mypy.readthedocs.io/en/stable/)
  configuration file for type checking Python code.
- `.copier-answers.yml`: Contains the answers you gave when copying the
  project from the template. **You should not modify this file
  directly.**
- `.cz.toml`:
  [Commitizen](https://commitizen-tools.github.io/commitizen/)
  configuration file for managing versions and changelogs.
- `.pre-commit-config.yaml`: [Pre-commit](https://pre-commit.com/)
  configuration file for managing and running checks before each commit.
- `.typos.toml`: [typos](https://github.com/crate-ci/typos) spell
  checker configuration file.
- `justfile`: [`just`](https://just.systems/man/en/) configuration file
  for scripting project tasks.
- `.editorconfig`: Editor configuration file for
  [EditorConfig](https://editorconfig.org/) to maintain consistent
  coding styles across different editors and IDEs.
- `CHANGELOG.md`: Changelog file for tracking changes in the project.
- `CITATION.cff`: Structured citation metadata for your project.
- `CONTRIBUTING.md`: Guidelines for contributing to the project.
- `_metadata.yml`: Quarto metadata file for the website, including
  information about the project, such as the titles and GitHub names.
- `pyproject.toml`: Main Python project configuration file defining
  metadata and dependencies.
- `_quarto.yml`: Quarto configuration file for the website, including
  settings for the website, such as the theme, navigation, and other
  options.
- `ruff.toml`: [Ruff](https://docs.astral.sh/ruff/) configuration file
  for linting and formatting Python code.
- `uv.lock`: Lockfile used by [`uv`](https://docs.astral.sh/uv/) to
  record exact versions of installed dependencies.
- `.rumdl.toml`: [rumdl](https://rumdl.dev/) configuration file for
  formatting Markdown files so that they are standardized and consistent

## Contributing

Check out our [contributing document](CONTRIBUTING.md) for information
on how to contribute to the project, including how to set up your
development environment.

Please note that this project is released with a [Contributor Code of
Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree
to abide by its terms.

### Contributors

The following people have contributed to this project by submitting pull
requests :tada:

[@lwjohnst86](https://github.com/lwjohnst86),
[@signekb](https://github.com/signekb),
[@joelostblom](https://github.com/joelostblom),
[@martonvago](https://github.com/martonvago)

## Licensing

This project is licensed under the [MIT License](LICENSE.md).

## Changelog

For a list of changes, see our [changelog](CHANGELOG.md) page.
