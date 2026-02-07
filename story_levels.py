from dataclasses import dataclass


@dataclass(frozen=True)
class StoryLevel:
    size: int
    grid_initial: str
    difficulty: int


def _normalize_rows(rows: list[str]) -> tuple[int, str]:
    if not rows:
        raise ValueError("Story level rows cannot be empty")
    size = len(rows)
    normalized: list[str] = []
    for row in rows:
        cleaned = row.replace(" ", ".")
        if len(cleaned) != size:
            raise ValueError(f"Story level row length mismatch: {cleaned!r}")
        for ch in cleaned:
            if ch not in {"0", "1", "."}:
                raise ValueError(f"Invalid story level char: {ch!r}")
        normalized.append(cleaned)
    return size, "".join(normalized)


_LEVEL_ROWS: list[list[str]] = [
    [
        "101.",
        ".10.",
        "110.",
        "....",
    ],
    [
        "..1.",
        ".0..",
        "..1.",
        ".0..",
    ],
    [
        "......",
        ".10.0.",
        "..11..",
        ".1....",
        "..11..",
        "......",
    ],
    [
        "1...0.",
        ".100..",
        ".01.0.",
        "00..1.",
        "..0.1.",
        ".....1",
    ],
    [
        "11001001",
        "00101100",
        "00......",
        "11......",
        "01......",
        "00......",
        "10......",
        "11......",
    ],
    [
        "........",
        ".1...0..",
        ".1......",
        "...0.1..",
        "..110..0",
        "........",
        "...11...",
        "........",
    ],
]


STORY_LEVELS: list[StoryLevel] = []
for rows in _LEVEL_ROWS:
    size, grid = _normalize_rows(rows)
    STORY_LEVELS.append(
        StoryLevel(size=size, grid_initial=grid, difficulty=max(1, size // 2))
    )
