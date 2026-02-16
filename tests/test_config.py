from pathlib import Path

from pytest import raises

from seedcase_flower.config import BuildStyle, Config


def test_creates_config():
    config = Config()
    assert config.style is None
    assert config.template_dir is None
    assert config.output_dir == Path("docs")

    config = Config(style=BuildStyle.quarto_one_page, output_dir=Path("my-docs/"))
    assert config.style == BuildStyle.quarto_one_page
    assert config.template_dir is None
    assert config.output_dir == Path("my-docs/")

    config = Config(template_dir=Path("templates"))
    assert config.style is None
    assert config.template_dir == Path("templates")
    assert config.output_dir == Path("docs")


def test_cannot_create_config_with_both_style_and_template_dir():
    with raises(ValueError):
        Config(style=BuildStyle.quarto_one_page, template_dir=Path("templates"))
