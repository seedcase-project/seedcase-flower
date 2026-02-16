from enum import Enum
from pathlib import Path
from typing import Optional, Self

from pydantic import BaseModel, model_validator


# TODO: share with `build()`
class BuildStyle(Enum):
    """Built-in styles for outputting to file."""

    quarto_one_page = "quarto_one_page"
    quarto_resource_listing = "quarto_resource_listing"
    quarto_resource_tables = "quarto_resource_tables"


class Config(BaseModel, frozen=True):
    """Configuration settings for styling the metadata.

    See the
    [design](https://flower.seedcase-project.org/docs/design/interface/config#config)
    for an explanation of how Config is designed. See the
    [guide](https://flower.seedcase-project.org/docs/guide/custom-styles) on how to
    set up custom styles and sections.
    See `Section` and `Content` help for more details on how to set up the sections.

    Attributes:
        style (Optional[BuildStyle]): The built-in style to use for outputting the
            documentation. When using a custom style, leave this unset and provide the
            template directory in `template_dir`.
        template_dir (Optional[Path]): When using a custom style, this should be the
            relative directory path to the
            [Jinja2](https://jinja.palletsprojects.com/en/stable/) template files.
            The directory **must** contain at least one template Jinja2 file and
            a `sections.toml` file that contains attributes for the `Section` classes.
        output_dir (Path): The directory where output files will be saved.
            Defaults to `docs/` within the current working directory.

    Examples:
        ```{python}
        import seedcase_flower as fl
        from pathlib import Path

        # A config using the built-in `quarto-one-page` style and outputting to the
        # `my-docs/` folder.
        config = fl.Config(
            style=fl.BuildStyle.quarto_one_page, output_dir=Path("my-docs/")
        )

        # A custom style that points to a template folder and outputs
        # to the default `docs/` folder.
        config = fl.Config(template_dir=Path("templates"))

        # A custom style that points to a template folder and outputs
        # to the `my-docs/` folder.
        config = fl.Config(template_dir=Path("templates"), output_dir=Path("my-docs/"))
        ```
    """

    style: Optional[BuildStyle] = None
    template_dir: Optional[Path] = None
    output_dir: Path = Path("docs")

    @model_validator(mode="after")
    def _style_with_template_dir(self) -> Self:
        if self.template_dir and self.style:
            raise ValueError(
                "Cannot use both `style` and `template_dir`. "
                "If you want to use a custom style, leave `style` unset and "
                "provide the template directory in `template_dir`."
            )
        return self
