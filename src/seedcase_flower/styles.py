from enum import Enum


class Style(Enum):
    """Built-in styles for generating documentation."""

    quarto_one_page = "quarto_one_page"
    quarto_resource_listing = "quarto_resource_listing"
    quarto_resource_tables = "quarto_resource_tables"


class ViewStyle(Enum):
    """Built-in styles suitable for terminal output."""

    quarto_one_page = "quarto_one_page"
    quarto_resource_listing = "quarto_resource_listing"
    quarto_resource_tables = "quarto_resource_tables"
