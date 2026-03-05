from enum import Enum


class BuildStyle(Enum):
    """Built-in styles for outputting to file."""

    quarto_one_page = "quarto_one_page"
    quarto_resource_listing = "quarto_resource_listing"
    quarto_resource_tables = "quarto_resource_tables"


class ViewStyle(Enum):
    """Built-in styles for outputting to the terminal."""

    quarto_one_page = "quarto_one_page"
