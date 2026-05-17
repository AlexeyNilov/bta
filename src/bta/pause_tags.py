from __future__ import annotations

import re
from dataclasses import dataclass

PAUSE_TAG_PATTERN = re.compile(r"\[(\d+(?:\.\d+)?)s\]")
UTF8_BOM = "\ufeff"


@dataclass(frozen=True)
class TextEvent:
    text: str


@dataclass(frozen=True)
class PauseEvent:
    seconds: float


PauseTagEvent = TextEvent | PauseEvent


def parse_pause_tags(text: str) -> list[PauseTagEvent]:
    text = text.removeprefix(UTF8_BOM)
    events: list[PauseTagEvent] = []
    cursor = 0

    for match in PAUSE_TAG_PATTERN.finditer(text):
        if match.start() > cursor:
            events.append(TextEvent(text[cursor : match.start()]))
        events.append(PauseEvent(float(match.group(1))))
        cursor = match.end()

    if cursor < len(text):
        events.append(TextEvent(text[cursor:]))

    return events
