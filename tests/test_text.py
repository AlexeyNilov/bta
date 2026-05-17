import pytest

from bta.text import chunk_text, clean_markdown_text


def test_clean_markdown_text_removes_single_line_html_tags():
    source = "Intro <span class='pagebreak'></span> continues."

    cleaned = clean_markdown_text(source)

    assert cleaned == "Intro continues."


def test_clean_markdown_text_removes_multiline_html_tags():
    source = "Intro <span\n  class='pagebreak'\n  id='p1'></span> continues."

    cleaned = clean_markdown_text(source)

    assert cleaned == "Intro continues."


def test_clean_markdown_text_preserves_word_spacing_around_removed_html():
    source = "This <span class='anchor'></span>mission matters."

    cleaned = clean_markdown_text(source)

    assert cleaned == "This mission matters."


def test_clean_markdown_text_preserves_non_html_markdown_content():
    source = "# Title\n\nThis keeps **bold** and [links](https://example.test).\n\n- item"

    cleaned = clean_markdown_text(source)

    assert cleaned == source


def test_clean_markdown_text_removes_utf8_bom_from_start_of_file():
    cleaned = clean_markdown_text("\ufeff[3s]Chapter 02")

    assert cleaned == "[3s]Chapter 02"


def test_chunk_text_groups_paragraphs_up_to_target_character_count():
    source = "Alpha paragraph.\n\nBeta paragraph.\n\nGamma paragraph."

    chunks = chunk_text(source, target_chars=40)

    assert chunks == ["Alpha paragraph.\n\nBeta paragraph.", "Gamma paragraph."]


def test_chunk_text_never_splits_a_sentence():
    source = "First sentence. Second sentence is longer. Third sentence."

    chunks = chunk_text(source, target_chars=30)

    assert chunks == ["First sentence.", "Second sentence is longer.", "Third sentence."]


def test_chunk_text_keeps_single_sentence_longer_than_target_as_oversized_chunk():
    source = "This sentence is deliberately longer than the configured target."

    chunks = chunk_text(source, target_chars=10)

    assert chunks == [source]


def test_chunk_text_rejects_non_positive_target_character_count():
    with pytest.raises(ValueError, match="target_chars"):
        chunk_text("Text.", target_chars=0)
