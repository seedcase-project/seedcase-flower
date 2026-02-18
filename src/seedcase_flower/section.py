from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

from jsonpath import JSONPathSyntaxError, compile
from pydantic import AfterValidator, BaseModel, field_validator


def _check_path_relative(value: Path) -> Path:
    if value.is_absolute():
        raise ValueError(
            f"{value!r} is an absolute path. Please provide a path relative to the "
            "parent folder."
        )
    return value


type RelativePath = Annotated[Path, AfterValidator(_check_path_relative)]


class Mode(Enum):
    """Output mode for a content item within a section."""

    one = "one"
    many = "many"


class Content(BaseModel, frozen=True):
    """Content to include within a `Section`.

    The `Content` class defines what Data Package properties and
    [Jinja2](https://jinja.palletsprojects.com/en/stable/) template file belong within
    a specific section (an output file or folder) in the documentation. You can use
    this class to customise how different parts of the `datapackage.json` file
    are displayed in the documentation and to create common presets when
    styles share similar content structures.

    Attributes:
        jsonpath (str): The JSON path, expressed using
            [JSON path syntax](https://jg-rp.github.io/python-jsonpath/syntax/),
            to the Data Package property that should be sent to the `template_path`
            Jinja2 file.
        template_path (Path): The path to the Jinja2 template file for this content
            item, relative to `Config.template_dir`.
        jinja_variable (str): The Jinja2 variable name that will be used in the template
            to reference this content item.
        mode (Mode): Whether this content item is used to output one file or many files.
            This determines how the Jinja2 template should be structured and how it
            references the Data Package property. `Mode.one` will generate one output
            file for the whole content item, while `Mode.many` will generate one output
            file for each element in a content item that is an array.

    Examples:
        ```{python}
        import seedcase_flower as fl
        from pathlib import Path

        # A content item displaying the metadata of the whole package in a single
        # output file
        package_content = fl.Content(
            jsonpath="$",
            template_path=Path("package.qmd.jinja"),
            jinja_variable="package",
            mode=fl.Mode.one,
        )

        # A content item displaying the metadata of each resource in a separate
        # output file
        resource_content = fl.Content(
            jsonpath="$.resources",
            template_path=Path("resource.qmd.jinja"),
            jinja_variable="resource",
            mode=fl.Mode.many,
        )
        ```
    """

    jsonpath: str
    template_path: RelativePath
    jinja_variable: str
    mode: Mode

    @field_validator("jsonpath", mode="after")
    @classmethod
    def _check_jsonpath(cls, value: str) -> str:
        try:
            compile(value)
        except JSONPathSyntaxError:
            raise ValueError(
                f"{value!r} is not a correct JSON path. See "
                "https://jg-rp.github.io/python-jsonpath/syntax/ for the expected "
                "syntax."
            )
        return value


class Section(BaseModel, frozen=True):
    """A section of the documentation with specific `datapackage.json` properties.

    See the [design](https://flower.seedcase-project.org/docs/design/interface/config#section)
    for an explanation of the design of `Section`.
    See the [guide](https://flower.seedcase-project.org/docs/guide/custom-styles) on
    how to set up custom styles and sections.
    See `Config` for more details on the top-level settings and `Content` for
    more details on the content items.

    Attributes:
        output_path (Optional[Path]): The output path for the section relative to
            `Config.output_dir`. Can be `None` when a style outputs to the terminal
            such as when using `view()`. If a directory is provided, files will be
            created for each content item that has a `name` property (e.g. `resources`
            or `resource-schema-fields`). For example, if `output_path` is
            `Path("docs/")` and `contents` is `["resources"]`, then each resource will
            be output to `docs/{resource_name}.md` (or whichever output format is used
            in the Jinja2 template files). If a file path is provided, all contents
            within the `Section` will be output to that single file.
        contents (list[Content]): List of content items to include in this
            section. See `Content` for more details about what to include. If more than
            one content item is included, they will be concatenated in the order
            provided, so that the `output_path` file will contain the
            output of the rendered Jinja2 templates for each content item, appended one
            after the other.

    Examples:
        ```{python}
        import seedcase_flower as fl
        from pathlib import Path

        # A section that contains only the package and contributors content items,
        # saved to the `package.qmd` file.
        section = fl.Section(
            output_path=Path("package.qmd"),
            contents=[
                fl.Content(
                    jsonpath="$",
                    template_path=Path("package.qmd.jinja"),
                    jinja_variable="package",
                    mode=fl.Mode.one,
                ),
                fl.Content(
                    jsonpath="$.contributors",
                    template_path=Path("contributors.qmd.jinja"),
                    jinja_variable="contributors",
                    mode=fl.Mode.one,
                ),
            ],
        )
        ```
    """

    output_path: Optional[RelativePath] = None
    contents: list[Content]
