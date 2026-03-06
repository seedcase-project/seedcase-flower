from pathlib import Path
from typing import Annotated, Optional

from jsonpath import JSONPathSyntaxError, compile
from pydantic import AfterValidator, BaseModel, ConfigDict, field_validator


def _check_path_relative(value: Path) -> Path:
    if value.is_absolute():
        raise ValueError(
            f"{value!r} is an absolute path. Please provide a path relative to the "
            "parent folder."
        )
    return value


type RelativePath = Annotated[Path, AfterValidator(_check_path_relative)]


class KebabModel(BaseModel, frozen=True):
    """Allow creating Pydantic model from kebab-case data."""

    model_config = ConfigDict(
        alias_generator=lambda string: string.replace("_", "-"),
        populate_by_name=True,
    )


class Content(KebabModel, frozen=True):
    """Content to include within a `One` or `Many` section.

    The `Content` class defines what Data Package properties and
    [Jinja2](https://jinja.palletsprojects.com/en/stable/) template file belong within
    a specific section (an output file or folder) in the documentation. You can use
    this class to customise how different parts of the `datapackage.json` file
    are displayed in the documentation and to create common presets when
    styles share similar content structures.

    Attributes:
        jsonpath: The JSON path, expressed using
            [JSON path syntax](https://jg-rp.github.io/python-jsonpath/syntax/),
            to the Data Package property that should be sent to the `template_path`
            Jinja2 file.
        template_path: The path to the Jinja2 template file for this content
            item, relative to `Config.template_dir`.
        jinja_variable: The Jinja2 variable name that will be used in the template
            to reference this content item.

    Examples:
        ```{python}
        import seedcase_flower as fl
        from pathlib import Path

        # A content item displaying the metadata of the whole package
        package_content = fl.Content(
            jsonpath="$",
            template_path=Path("package.qmd.jinja"),
            jinja_variable="package",
        )
        ```
    """

    jsonpath: str
    template_path: RelativePath
    jinja_variable: str

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


class One(KebabModel, frozen=True):
    """A section of the documentation that outputs to one file.

    See the [design](https://flower.seedcase-project.org/docs/design/interface/config#section)
    for an explanation of the design of `One`.
    See the [guide](https://flower.seedcase-project.org/docs/guide/custom-styles) on
    how to set up custom styles and sections.
    See `Config` for more details on the top-level settings and `Content` for
    more details on the content items.

    Attributes:
        output_path: The output path for the section relative to
            `Config.output_dir`. Can be `None` when a style outputs to the terminal
            such as when using `view()`.
        contents: List of content items to include in this
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
        section = fl.One(
            output_path=Path("package.qmd"),
            contents=[
                fl.Content(
                    jsonpath="$",
                    template_path=Path("package.qmd.jinja"),
                    jinja_variable="package",
                ),
                fl.Content(
                    jsonpath="$.contributors",
                    template_path=Path("contributors.qmd.jinja"),
                    jinja_variable="contributors",
                ),
            ],
        )
        ```
    """

    output_path: Optional[RelativePath] = None
    contents: list[Content]


class Many(KebabModel, frozen=True):
    """A section of the documentation that outputs to multiple files.

    See the [design](https://flower.seedcase-project.org/docs/design/interface/config#section)
    for an explanation of the design of `Many`.
    See the [guide](https://flower.seedcase-project.org/docs/guide/custom-styles) on
    how to set up custom styles and sections.
    See `Config` for more details on the top-level settings and `Content` for
    more details on the content items.

    Attributes:
        output_path: The output path for the section relative to `Config.output_dir`.
            If a directory is provided, a file will be created for each metadata item
            matched by `content.jsonpath`. These metadata items must have a `name`
            property, which will be used in the filename (e.g., resources or resource
            schema fields). For example, if `output_path` is `Path("docs/")` and
            `jsonpath` is `$.resources`, then each resource will be output to
            `docs/{resource_name}.md` (or whichever output format is used
            in the Jinja2 template files).
        content: The content item to display in this section.

    Examples:
        ```{python}
        import seedcase_flower as fl
        from pathlib import Path

        # A section that displays each resource in a separate file within the
        # `resources/` folder.
        section = fl.Many(
            output_path=Path("resources/"),
            content=fl.Content(
                jsonpath="$.resources",
                template_path=Path("resource.md.jinja"),
                jinja_variable="resource",
            ),
        )
        ```
    """

    # TODO: check template name ext and output path ext match
    output_path: Optional[RelativePath] = None
    content: Content
