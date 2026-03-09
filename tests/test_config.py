from pathlib import Path

from seedcase_flower.config import Config
from seedcase_flower.styles import Style


def test_creates_config():
    config = Config()
    assert config.style == Style.quarto_one_page
    assert config.template_dir is None
    assert config.output_dir == Path("docs/")

    config = Config(
        style=Style.quarto_resource_listing,
        template_dir=Path("templates/"),
        output_dir=Path("my-docs/"),
    )
    assert config.style == Style.quarto_resource_listing
    assert config.template_dir == Path("templates/")
    assert config.output_dir == Path("my-docs/")

    config = Config(template_dir=Path("templates/"))
    assert config.style == Style.quarto_one_page
    assert config.template_dir == Path("templates/")
    assert config.output_dir == Path("docs/")
