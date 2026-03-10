from pathlib import Path

from pydantic import ValidationError
from pytest import fixture, mark, raises

from seedcase_flower.build_sections import BuiltSection, build_sections
from seedcase_flower.config import Config
from seedcase_flower.styles import Style

content = """
[[section.contents]]
jsonpath = "$"
template-path = "template.qmd.jinja"
jinja-variable = "package"
mode = "one"
"""

one_content_toml = f"""
[[section]]
output-path = "section1.qmd"
{content}
"""

multi_content_toml = f"""
{one_content_toml}
{content}
"""

multi_section_toml = f"""
[[section]]
output-path = "section1.qmd"
{content}
{content}
[[section]]
output-path = "section2.qmd"
{content}
"""

properties = {
    "name": "example-datapackage",
    "resources": [
        {
            "name": "example-resource",
            "path": "data/example-resource.csv",
        }
    ],
}


@fixture
def _template(tmp_path):
    (tmp_path / "template.qmd.jinja").write_text("{{ package.name }}")


@mark.parametrize(
    "sections_toml, expected",
    [
        (
            one_content_toml,
            [
                BuiltSection(
                    output_path=Path("section1.qmd"), content="example-datapackage"
                )
            ],
        ),
        (
            multi_content_toml,
            [
                BuiltSection(
                    output_path=Path("section1.qmd"),
                    content="example-datapackage\nexample-datapackage",
                ),
            ],
        ),
        (
            multi_section_toml,
            [
                BuiltSection(
                    output_path=Path("section1.qmd"),
                    content="example-datapackage\nexample-datapackage",
                ),
                BuiltSection(
                    output_path=Path("section2.qmd"), content="example-datapackage"
                ),
            ],
        ),
    ],
)
def test_matches_sections_toml_config(sections_toml, expected, tmp_path, _template):
    (tmp_path / "sections.toml").write_text(sections_toml)
    config = Config(template_dir=tmp_path)

    built_sections = build_sections(properties, config)

    assert built_sections == expected


def test_can_use_multiple_templates_with_different_jsonpaths(tmp_path, _template):
    sections_toml = """
    [[section]]
    output-path = "section1.qmd"

    [[section.contents]]
    jsonpath = "$"
    template-path = "template.qmd.jinja"
    jinja-variable = "package"
    mode = "one"

    [[section.contents]]
    jsonpath = "$.resources"
    template-path = "resources.qmd.jinja"
    jinja-variable = "resources"
    mode = "one"
    """
    (tmp_path / "sections.toml").write_text(sections_toml)
    (tmp_path / "resources.qmd.jinja").write_text("{{ resources | length }}")
    config = Config(template_dir=tmp_path)

    built_sections = build_sections(properties, config)

    assert built_sections == [
        BuiltSection(
            output_path=Path("section1.qmd"), content="example-datapackage\n1"
        ),
    ]


def test_uses_style_when_no_template_dir_given():
    config = Config(style=Style.quarto_one_page)

    built_sections = build_sections(properties, config)

    assert len(built_sections) == 1
    assert built_sections[0].output_path == Path("index.qmd")
    assert "example-datapackage" in built_sections[0].content


def test_handles_no_match_for_jsonpath_gracefully(tmp_path, _template):
    (tmp_path / "sections.toml").write_text(
        one_content_toml.replace('jsonpath = "$"', 'jsonpath = "$.nonexistent"')
    )
    config = Config(template_dir=tmp_path)

    built_sections = build_sections(properties, config)

    assert built_sections == [
        BuiltSection(output_path=Path("section1.qmd"), content=""),
    ]


def test_rejects_bad_sections_toml(tmp_path):
    (tmp_path / "sections.toml").write_text(
        "[[section]]\noutput-path = 'no-content.qmd'"
    )
    config = Config(template_dir=tmp_path)

    with raises(ValidationError):
        build_sections(properties, config)


def test_flags_missing_template_folder():
    config = Config(template_dir=Path("nonexistent-folder"))

    with raises(NotADirectoryError):
        build_sections(properties, config)


def test_flags_missing_sections_toml(tmp_path):
    config = Config(template_dir=tmp_path)

    with raises(FileNotFoundError):
        build_sections(properties, config)


def test_flags_missing_template_file(tmp_path):
    (tmp_path / "sections.toml").write_text(one_content_toml)
    config = Config(template_dir=tmp_path)

    with raises(FileNotFoundError):
        build_sections(properties, config)


def test_flags_bad_jsonpath_for_mode_one(tmp_path, _template):
    (tmp_path / "sections.toml").write_text(
        one_content_toml.replace('jsonpath = "$"', 'jsonpath = "$.resources[*]"')
    )
    config = Config(template_dir=tmp_path)
    multi_resource_properties = {
        "name": "example-datapackage",
        "resources": [
            {
                "name": "example-resource",
                "path": "data/example-resource.csv",
            },
            {
                "name": "another-resource",
                "path": "data/another-resource.csv",
            },
        ],
    }

    with raises(ValueError):
        build_sections(multi_resource_properties, config)
