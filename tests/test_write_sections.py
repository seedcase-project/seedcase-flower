from pathlib import Path

from pytest import raises

from seedcase_flower.build_sections import BuiltSection
from seedcase_flower.write_sections import write_sections


def test_writes_sections_to_file(tmp_path):
    built_sections = [
        BuiltSection(
            content="Section 1 content.",
            output_path=Path("section1.qmd"),
        ),
        BuiltSection(
            content="Section 2 content.",
            output_path=Path("some-folder") / "section2.qmd",
        ),
    ]

    output_files = write_sections(built_sections, tmp_path)

    assert output_files == [
        tmp_path / "section1.qmd",
        tmp_path / "some-folder" / "section2.qmd",
    ]
    assert output_files[0].read_text() == "Section 1 content."
    assert output_files[1].read_text() == "Section 2 content."


def test_throws_error_if_no_output_path(tmp_path):
    built_sections = [
        BuiltSection(
            content="Section 1 content.",
        ),
        BuiltSection(
            content="Section 2 content.",
            output_path=Path("section2.qmd"),
        ),
    ]

    with raises(ValueError):
        write_sections(built_sections, tmp_path)

    assert not (tmp_path / "section2.qmd").exists()
    assert not (tmp_path / "section1.qmd").exists()
