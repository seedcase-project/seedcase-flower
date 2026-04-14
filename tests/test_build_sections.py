from pathlib import Path
from typing import Any

from pydantic import ValidationError
from pytest import fixture, mark, raises
from seedcase_soil import flat_fmap, fmap

from seedcase_flower.build_sections import BuiltSection, build_sections
from seedcase_flower.config import Config
from seedcase_flower.styles import Style

# One section ====

content = """
[[one.contents]]
jsonpath = "$"
template-path = "template.qmd.jinja"
jinja-variable = "package"
"""

one_content_toml = f"""
[[one]]
output-path = "section1.qmd"
{content}
"""

multi_content_toml = f"""
{one_content_toml}
{content}
"""

multi_section_toml = f"""
[[one]]
output-path = "section1.qmd"
{content}
{content}
[[one]]
output-path = "section2.qmd"
{content}
"""

properties: dict[str, Any] = {
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
    [[one]]
    output-path = "section1.qmd"

    [[one.contents]]
    jsonpath = "$"
    template-path = "template.qmd.jinja"
    jinja-variable = "package"

    [[one.contents]]
    jsonpath = "$.resources"
    template-path = "resources.qmd.jinja"
    jinja-variable = "resources"
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
    (tmp_path / "sections.toml").write_text("[[one]]\noutput-path = 'no-content.qmd'")
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


def test_flags_bad_jsonpath_for_one_section(tmp_path, _template):
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


# Many section ====

many_section_resources = """
[[many]]
output-path = "resources/"
content = "resources"
template-path = "resource.qmd.jinja"
jinja-variable = "resource"
"""

many_section_fields = """
[[many]]
output-path = "fields/"
content = "fields"
template-path = "field.qmd.jinja"
jinja-variable = "field"
"""

many_section_both = f"""
{many_section_resources}
{many_section_fields}
"""


def _get_resource_sections(properties: dict[str, Any]) -> list[BuiltSection]:
    return fmap(
        properties["resources"],
        lambda resource: BuiltSection(
            content=resource["name"],
            output_path=Path(f"resources/{resource['name']}.qmd"),
        ),
    )


def _get_field_sections(properties: dict[str, Any]) -> list[BuiltSection]:
    return fmap(
        flat_fmap(
            properties["resources"], lambda resource: resource["schema"]["fields"]
        ),
        lambda field: BuiltSection(
            content=field["name"], output_path=Path(f"fields/{field['name']}.qmd")
        ),
    )


@mark.parametrize(
    "sections_toml, get_expected_sections",
    [
        (many_section_resources, lambda props: _get_resource_sections(props)),
        (many_section_fields, lambda props: _get_field_sections(props)),
        (
            many_section_both,
            lambda props: _get_resource_sections(props) + _get_field_sections(props),
        ),
    ],
)
def test_builds_many_section(
    sections_toml, get_expected_sections, tmp_path, datapackage
):
    (tmp_path / "sections.toml").write_text(sections_toml)
    (tmp_path / "resource.qmd.jinja").write_text("{{ resource.name }}")
    (tmp_path / "field.qmd.jinja").write_text("{{ field.name }}")
    config = Config(template_dir=tmp_path)

    built_sections = build_sections(datapackage, config)

    assert built_sections == get_expected_sections(datapackage)


def test_handles_no_fields_gracefully(tmp_path):
    (tmp_path / "sections.toml").write_text(many_section_fields)
    (tmp_path / "resource.qmd.jinja").write_text("{{ resource.name }}")
    (tmp_path / "field.qmd.jinja").write_text("{{ field.name }}")
    config = Config(template_dir=tmp_path)

    built_sections = build_sections(properties, config)

    assert built_sections == []


@mark.parametrize(
    ("output_path_in, output_path_out"),
    [
        ("resources/{resource-name}.qmd", "resources/example-resource.qmd"),
        ("resources/my-{resource-name}.qmd", "resources/my-example-resource.qmd"),
        ("resources/{resource-name}/index.qmd", "resources/example-resource/index.qmd"),
        (
            "resources/{resource-name}/folder",
            "resources/example-resource/folder/example-resource.qmd",
        ),
    ],
)
def test_resolves_placeholder_for_resource_files(
    tmp_path, output_path_in, output_path_out
):
    (tmp_path / "sections.toml").write_text(
        many_section_resources.replace("resources/", output_path_in)
    )
    (tmp_path / "resource.qmd.jinja").write_text("{{ resource.name }}")
    config = Config(template_dir=tmp_path)

    built_sections = build_sections(properties, config)

    assert built_sections[0].output_path == Path(output_path_out)


@mark.parametrize(
    ("output_path_in, output_path_out"),
    [
        ("fields/", "fields/example-field.qmd"),
        ("fields/{field-name}.qmd", "fields/example-field.qmd"),
        (
            "resources/{resource-name}/fields/",
            "resources/example-resource/fields/example-field.qmd",
        ),
        (
            "resources/{resource-name}/fields/{field-name}.qmd",
            "resources/example-resource/fields/example-field.qmd",
        ),
        (
            "resources/{resource-name}/{field-name}/index.qmd",
            "resources/example-resource/example-field/index.qmd",
        ),
        (
            "resources/{resource-name}/{field-name}/folder",
            "resources/example-resource/example-field/folder/example-field.qmd",
        ),
    ],
)
def test_resolves_placeholder_for_field_files(
    tmp_path, output_path_in, output_path_out
):
    (tmp_path / "sections.toml").write_text(
        many_section_fields.replace("fields/", output_path_in)
    )
    (tmp_path / "field.qmd.jinja").write_text("{{ field.name }}")
    config = Config(template_dir=tmp_path)
    one_field_properties = {
        "name": "example-datapackage",
        "resources": [
            {
                "name": "example-resource",
                "path": "data/example-resource.csv",
                "schema": {"fields": [{"name": "example-field", "type": "integer"}]},
            }
        ],
    }

    built_sections = build_sections(one_field_properties, config)

    assert built_sections[0].output_path == Path(output_path_out)


def test_builds_toml_with_one_and_many_sections(tmp_path, _template, datapackage):
    toml = f"{multi_section_toml}\n{many_section_both}"
    (tmp_path / "sections.toml").write_text(toml)
    (tmp_path / "resource.qmd.jinja").write_text("{{ resource.name }}")
    (tmp_path / "field.qmd.jinja").write_text("{{ field.name }}")
    config = Config(template_dir=tmp_path)
    package_name = datapackage["name"]

    built_sections = build_sections(datapackage, config)

    assert built_sections == [
        BuiltSection(
            output_path=Path("section1.qmd"),
            content=f"{package_name}\n{package_name}",
        ),
        BuiltSection(output_path=Path("section2.qmd"), content=package_name),
    ] + _get_resource_sections(datapackage) + _get_field_sections(datapackage)


def test_flags_missing_template_file_in_many_section(tmp_path):
    (tmp_path / "sections.toml").write_text(many_section_resources)
    config = Config(template_dir=tmp_path)

    with raises(FileNotFoundError):
        build_sections(properties, config)
