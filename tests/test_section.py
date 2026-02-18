from pathlib import Path

from pytest import raises

from seedcase_flower.section import Content, Mode, Section

content = Content(
    jsonpath="$.resources",
    template_path=Path("resource_template.html.jinja"),
    jinja_variable="resource",
    mode=Mode.many,
)


def test_create_section():
    section = Section(
        output_path=Path("resources/"),
        contents=[content],
    )
    assert section.output_path == Path("resources/")
    assert section.contents == [content]

    section = Section(
        contents=[content] * 2,
    )
    assert section.output_path is None
    assert section.contents == [content] * 2


def test_cannot_create_section_with_absolute_output_path():
    with raises(ValueError):
        Section(
            output_path=Path("/absolute/path/resources/"),
            contents=[content],
        )


def test_cannot_create_content_with_bad_jsonpath():
    with raises(ValueError):
        Content(
            jsonpath="<><>bad.path",
            template_path=Path("template.qmd.jinja"),
            jinja_variable="data",
            mode=Mode.one,
        )


def test_cannot_create_content_with_absolute_template_path():
    with raises(ValueError):
        Content(
            jsonpath="$",
            template_path=Path("/absolute/path/template.qmd.jinja"),
            jinja_variable="data",
            mode=Mode.one,
        )
