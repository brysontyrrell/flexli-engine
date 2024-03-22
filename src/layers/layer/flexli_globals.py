from typing import Any

ITERATOR_VALUE: Any = None


def reset() -> None:
    global ITERATOR_VALUE
    ITERATOR_VALUE = None
