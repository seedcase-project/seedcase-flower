import re
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional, Self

from jsonpath import JSONPathSyntaxError, compile
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    field_validator,
    model_validator,
)


def _check_path_relative(value: Path) -> Path:
    if value.is_absolute():
        raise ValueError(
            f"{value!r} is an absolute path. Please provide a path relative to the "
            "parent folder."
        )
    return value


type RelativePath = Annotated[Path, AfterValidator(_check_path_relative)]


def _check_template_extension(value: Path) -> Path:
    if len(value.suffixes) < 2 or value.suffix != ".jinja":
        raise ValueError(
            f"The template name '{value.name}' must be of the form "
            "`<name>.<ext>.jinja`."
        )
    return value


type TemplatePath = Annotated[RelativePath, AfterValidator(_check_template_extension)]


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
    template_path: TemplatePath
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


class ManyContent(str, Enum):
    """Content item to include within a `Many` section."""

    resources = "resources"
    fields = "fields"

    @property
    def jsonpath(self) -> str:
        """The JSON path that selects this content item."""
        return {
            self.resources: "$.resources[*]",
            self.fields: "$.resources[*].schema.fields[*]",
        }[self]

    @property
    def placeholder(self) -> str:
        """The placeholder for this content item in the the output path."""
        return {
            self.resources: "{resource-name}",
            self.fields: "{field-name}",
        }[self]

    @property
    def allowed_placeholders(self) -> list[list[str]]:
        """The allowed placeholders in the output path for this content item."""
        resource = ManyContent.resources.placeholder
        field = ManyContent.fields.placeholder
        return {
            self.resources: [[resource]],
            self.fields: [[resource], [field], [resource, field]],
        }[self]


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
            If a directory is provided, the output files will be saved in that
            directory. If the path includes a placeholder in curly brackets (e.g.
            `resources/{resource-name}.qmd`), the output files will be named following
            this template.
        content: The content item to display in this section; choices are `resources`
            and `fields`.

    Examples:
        ```{python}
        import seedcase_flower as fl
        from pathlib import Path

        # A section that displays each resource in a separate file within the
        # `resources/` folder.
        section = fl.Many(
            output_path=Path("resources/"),
            content=fl.ManyContent.resources,
            template_path=Path("resource.md.jinja"),
            jinja_variable="resource",
        )
        ```
    """

    output_path: Optional[RelativePath] = None
    content: ManyContent
    template_path: TemplatePath
    jinja_variable: str

    @property
    def extension(self) -> str:
        """The extension of the files to create."""
        return "".join(self.template_path.suffixes[:-1])

    @model_validator(mode="after")
    def _check_extensions(self) -> Self:
        if not self.output_path or not self.output_path.suffixes:
            return self
        if "".join(self.output_path.suffixes) != self.extension:
            raise ValueError(
                f"The file generated from the template '{self.template_path}' must "
                f"have the same file extension as the output path '{self.output_path}'."
            )
        return self

    @model_validator(mode="after")
    def _check_placeholders(self) -> Self:
        if not self.output_path:
            return self

        posix_path = self.output_path.as_posix()
        placeholders = re.findall(r"\{[^\}]*\}", posix_path)
        if placeholders and placeholders not in self.content.allowed_placeholders:
            # e.g. `resources/{not-resource-name}.qmd`
            raise ValueError(
                f"The output path '{self.output_path}' contains incorrect "
                "placeholders. Check that you're using the correct placeholders "
                # TODO: Add link
                "for the content type in the correct order. See LINK for more details."
            )

        if not self.output_path.suffix:
            # Normalise folder paths
            # e.g. `resources/` -> `resources/{resource-name}.qmd`
            object.__setattr__(
                self,
                "output_path",
                self.output_path / (self.content.placeholder + self.extension),
            )
            return self

        if not placeholders:
            # e.g. `resources/concrete-file.qmd`
            raise ValueError(
                f"The output path '{self.output_path}' points to a file. Output "
                "paths in `many` sections must point to a folder or use a "
                "placeholder for the filename."
            )
        if self.content.placeholder not in placeholders:
            # e.g. `folder/{resource-name}.qmd` in a fields section
            raise ValueError(
                f"The output path '{self.output_path}' uses the wrong placeholder "
                "in the filename. Files displaying fields should use the placeholder "
                f"{ManyContent.fields.placeholder!r} in the filename."
            )

        return self
