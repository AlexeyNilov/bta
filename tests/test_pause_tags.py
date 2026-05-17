from bta.pause_tags import PauseEvent, TextEvent, parse_pause_tags


def test_parse_pause_tags_returns_single_text_event_when_no_tags_are_present():
    events = parse_pause_tags("Hello world.")

    assert events == [TextEvent("Hello world.")]


def test_parse_pause_tags_splits_text_around_seconds_tags():
    events = parse_pause_tags("Hello [1s] world [0.25s] again.")

    assert events == [
        TextEvent("Hello "),
        PauseEvent(1.0),
        TextEvent(" world "),
        PauseEvent(0.25),
        TextEvent(" again."),
    ]


def test_parse_pause_tags_preserves_leading_and_trailing_pause_events():
    events = parse_pause_tags("[1.5s]Hello.[2s]")

    assert events == [
        PauseEvent(1.5),
        TextEvent("Hello."),
        PauseEvent(2.0),
    ]


def test_parse_pause_tags_leaves_unsupported_syntax_as_text():
    events = parse_pause_tags("Wait [1 sec] then [s].")

    assert events == [TextEvent("Wait [1 sec] then [s].")]
