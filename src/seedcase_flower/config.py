from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from seedcase_flower.styles import Style


class Config(BaseModel, frozen=True):
    """Configuration settings for styling the metadata.

    See the
    [design](https://flower.seedcase-project.org/docs/design/interface/config#config)
    for an explanation of how Config is designed. See the
    [guide](https://flower.seedcase-project.org/docs/guide/custom-styles) on how to
    set up custom styles and sections.
    See `One`, `Many`, and `Content` help for more details on how to set up the
    sections.

    Attributes:
        style: The built-in style to use for outputting the
            documentation. Ignored when `style_dir` is set.
        style_dir: When using a custom style, this should be the
            relative directory path to the
            [Jinja2](https://jinja.palletsprojects.com/en/stable/) template files.
            The directory **must** contain at least one template Jinja2 file and
            a `sections.toml` file that contains attributes for the `One` and `Many`
            classes.
        output_dir: The directory where output files will be saved.

    Examples:
        ```{python}
        import seedcase_flower as fl
        from pathlib import Path

        # A config using the built-in `quarto-resource-listing` style and outputting
        # to the `my-docs/` folder.
        config = fl.Config(
            style=fl.Style.quarto_resource_listing, output_dir=Path("my-docs/")
        )

        # A custom style that points to a style folder and outputs
        # to the default `docs/` folder.
        config = fl.Config(style_dir=Path("style/"))

        # A custom style that points to a style folder and outputs
        # to the `my-docs/` folder.
        config = fl.Config(style_dir=Path("style/"), output_dir=Path("my-docs/"))
        ```
    """

    style: Style = Style.quarto_one_page
    style_dir: Optional[Path] = None
    output_dir: Path = Path("docs")
