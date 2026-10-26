from __future__ import annotations

from agentmd_import.parser import Import, SyntaxIssue, parse


def test_plain_lines_are_ignored() -> None:
    assert parse("# Title\n\nSome text.\n") == []


def test_directive_line_numbers_are_one_based() -> None:
    items = parse("# Title\n\n@a.md\n@docs/b.md\n")
    assert items == [Import(path="a.md", line=3), Import(path="docs/b.md", line=4)]


def test_leading_and_trailing_spaces_are_trimmed() -> None:
    assert parse("   @a.md   \n") == [Import(path="a.md", line=1)]


def test_inline_mention_is_not_a_directive() -> None:
    assert parse("See @a.md for details.\n") == []


def test_empty_directive_is_a_syntax_issue() -> None:
    assert parse("@\n") == [SyntaxIssue(line=1, text="@")]


def test_whitespace_inside_path_is_a_syntax_issue() -> None:
    items = parse("@two words.md\n")
    assert items == [SyntaxIssue(line=1, text="@two words.md")]


def test_trailing_text_is_a_syntax_issue() -> None:
    items = parse("@notes.md please\n")
    assert items == [SyntaxIssue(line=1, text="@notes.md please")]


def test_directives_inside_backtick_fence_are_ignored() -> None:
    text = "```md\n@ghost.md\n```\n@real.md\n"
    assert parse(text) == [Import(path="real.md", line=4)]


def test_directives_inside_tilde_fence_are_ignored() -> None:
    text = "~~~\n@ghost.md\n~~~\n@real.md\n"
    assert parse(text) == [Import(path="real.md", line=4)]


def test_unclosed_fence_hides_the_rest_of_the_file() -> None:
    text = "```\n@ghost.md\n@ghost2.md\n"
    assert parse(text) == []


def test_other_fence_character_does_not_close_the_fence() -> None:
    text = "```\n~~~\n@ghost.md\n```\n@real.md\n"
    assert parse(text) == [Import(path="real.md", line=5)]


def test_fence_closes_only_with_a_marker_at_least_as_long() -> None:
    text = "````\n```\n@ghost.md\n````\n@real.md\n"
    assert parse(text) == [Import(path="real.md", line=5)]


def test_fence_inside_indented_content_is_detected() -> None:
    text = "  ```\n  @ghost.md\n  ```\n@real.md\n"
    assert parse(text) == [Import(path="real.md", line=4)]


def test_crlf_line_endings_keep_correct_line_numbers() -> None:
    assert parse("# Title\r\n@a.md\r\n") == [Import(path="a.md", line=2)]


def test_bom_is_stripped() -> None:
    assert parse("\ufeff@a.md\n") == [Import(path="a.md", line=1)]


def test_double_at_is_a_path_not_a_directive_marker() -> None:
    assert parse("@@a.md\n") == [Import(path="@a.md", line=1)]
