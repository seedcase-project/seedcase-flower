from pathlib import Path
from typing import cast

from seedcase_soil import fmap, keep

from seedcase_flower.build_sections import BuiltSection


def write_sections(built_sections: list[BuiltSection], output_dir: Path) -> list[Path]:
    """Writes each built section to a file in the output directory.

    Args:
        built_sections: The list of built sections to be written to files.
        output_dir: The directory where the built sections should be written.

    Returns:
        A list of paths to the output files that were created.

    Raises:
        ValueError: If any of the built sections do not have an output path.
    """
    if keep(built_sections, lambda section: section.output_path is None):
        raise ValueError(
            "At least one section in `sections.toml` is missing an output path. "
            "When using the `build` command, all sections must have an output path."
        )

    return fmap(built_sections, lambda section: _write_section(section, output_dir))


def _write_section(built_section: BuiltSection, output_dir: Path) -> Path:
    output_path = output_dir / cast(Path, built_section.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(built_section.content)
    return output_path
