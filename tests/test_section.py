from pathlib import Path

from pytest import mark, raises

from seedcase_flower.sections import Content, Many, ManyContent, One

# One section ====

content = Content(
    jsonpath="$.resources",
    template_path=Path("resource_template.html.jinja"),
    jinja_variable="resource",
)


def test_creates_one_section():
    section = One(
        output_path=Path("resources/"),
        contents=[content],
    )
    assert section.output_path == Path("resources/")
    assert section.contents == [content]

    section = One(
        contents=[content] * 2,
    )
    assert section.output_path is None
    assert section.contents == [content] * 2


def test_cannot_create_section_with_absolute_output_path():
    with raises(ValueError):
        One(
            output_path=Path("/absolute/path/resources/"),
            contents=[content],
        )


def test_cannot_create_content_with_bad_jsonpath():
    with raises(ValueError):
        Content(
            jsonpath="<><>bad.path",
            template_path=Path("template.qmd.jinja"),
            jinja_variable="data",
        )


def test_cannot_create_content_with_absolute_template_path():
    with raises(ValueError):
        Content(
            jsonpath="$",
            template_path=Path("/absolute/path/template.qmd.jinja"),
            jinja_variable="data",
        )


@mark.parametrize("template_path", ["", "template.qmd", "template.jinja", "template"])
def test_cannot_create_content_without_extension_in_template_path(template_path):
    with raises(ValueError):
        Content(
            jsonpath="$",
            template_path=Path(template_path),
            jinja_variable="data",
        )


# Many section ====


@mark.parametrize(
    "output_path_in, output_path_out",
    [
        (None, None),
        (Path("resources/"), Path("resources/{resource-name}.qmd")),
        (Path("resources/{resource-name}.qmd"), Path("resources/{resource-name}.qmd")),
        (
            Path("resources/{resource-name}/index.qmd"),
            Path("resources/{resource-name}/index.qmd"),
        ),
        (
            Path("resources/{resource-name}/folder"),
            Path("resources/{resource-name}/folder/{resource-name}.qmd"),
        ),
    ],
)
def test_creates_many_section_for_resources(output_path_in, output_path_out):
    section = Many(
        output_path=output_path_in,
        content=ManyContent.resources,
        template_path=Path("resource.qmd.jinja"),
        jinja_variable="resource",
    )
    assert section.output_path == output_path_out


@mark.parametrize(
    "output_path_in, output_path_out",
    [
        (None, None),
        (Path("fields/"), Path("fields/{field-name}.qmd")),
        (Path("fields/{field-name}.qmd"), Path("fields/{field-name}.qmd")),
        (
            Path("resources/{resource-name}/fields/"),
            Path("resources/{resource-name}/fields/{field-name}.qmd"),
        ),
        (
            Path("resources/{resource-name}/fields/{field-name}.qmd"),
            Path("resources/{resource-name}/fields/{field-name}.qmd"),
        ),
        (
            Path("resources/{resource-name}/{field-name}/index.qmd"),
            Path("resources/{resource-name}/{field-name}/index.qmd"),
        ),
        (
            Path("resources/{resource-name}/{field-name}/folder"),
            Path("resources/{resource-name}/{field-name}/folder/{field-name}.qmd"),
        ),
    ],
)
def test_creates_many_section_for_fields(output_path_in, output_path_out):
    section = Many(
        output_path=output_path_in,
        content=ManyContent.fields,
        template_path=Path("field.qmd.jinja"),
        jinja_variable="field",
    )
    assert section.output_path == output_path_out


@mark.parametrize(
    "many_content, output_path",
    [
        (ManyContent.resources, "resources/{not-resource-name}.qmd"),
        (ManyContent.resources, "resources/{field-name}.qmd"),
        (ManyContent.resources, "{resource-name}/{resource-name}.qmd"),
        (ManyContent.resources, "points/to/file/index.qmd"),
        (ManyContent.resources, "resources/{resource-name}"),
        (ManyContent.fields, "fields/{not-field-name}.qmd"),
        (ManyContent.fields, "{field-name}/{resource-name}/index.qmd"),
        (ManyContent.fields, "{field-name}/{field-name}/index.qmd"),
        (ManyContent.fields, "{resource-name}/{resource-name}/index.qmd"),
        (ManyContent.fields, "points/to/file/index.qmd"),
        (ManyContent.fields, "fields/{field-name}"),
    ],
)
def test_cannot_create_many_section_with_bad_output_path(many_content, output_path):
    with raises(ValueError):
        Many(
            output_path=output_path,
            content=many_content,
            template_path=Path("template.qmd.jinja"),
            jinja_variable="field",
        )
