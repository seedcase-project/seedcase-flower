from pathlib import Path

from seedcase_flower.config import Config
from seedcase_flower.styles import Style


def test_creates_config():
    config = Config()
    assert config.style == Style.quarto_one_page
    assert config.style_dir is None
    assert config.output_dir == Path("docs/")

    config = Config(
        style=Style.quarto_resource_listing,
        style_dir=Path("style/"),
        output_dir=Path("my-docs/"),
    )
    assert config.style == Style.quarto_resource_listing
    assert config.style_dir == Path("style/")
    assert config.output_dir == Path("my-docs/")

    config = Config(style_dir=Path("style/"))
    assert config.style == Style.quarto_one_page
    assert config.style_dir == Path("style/")
    assert config.output_dir == Path("docs/")
