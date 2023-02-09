from dataclasses import dataclass
from typing import Any
import pytest

from main import NotIsbnError, get_isbn_10_and_13


@dataclass
class ISBN:
    text: str
    input: list[str]
    exp: tuple[list[str], list[str]]
    err: Any


test_cases = [
    ISBN(
        text="A single ISBN 10",
        input=["0002217317"],
        exp=(["0002217317"], []),
        err=None,
    ),
    ISBN(
        text="Two ISBN 10s",
        input=["0002217317", "0030050456"],
        exp=(["0002217317", "0030050456"], []),
        err=None,
    ),
    ISBN(
        text="A single ISBN 13",
        input=["9780030050459"],
        exp=([], ["9780030050459"]),
        err=None,
    ),
    ISBN(
        text="Two ISBN 13s",
        input=["9780002217316", "9780030050459"],
        exp=([], ["9780002217316", "9780030050459"]),
        err=None,
    ),
    ISBN(
        text="Mixed ISBN 10 and 13",
        input=["0002217317", "0030050456", "9780002217316", "9780030050459"],
        exp=(["0002217317", "0030050456"], ["9780002217316", "9780030050459"]),
        err=None,
    ),
    ISBN(
        text="Invalid ISBN should raise an error",
        input=["1234"],
        exp=([], []),
        err=NotIsbnError,
    ),
    ISBN(
        text="bad check digit",
        input=["0030802791"],
        exp=(["0030802792"], []),
        err=None
        ),
]


@pytest.mark.parametrize(
    "tc,exp", [(test_case, test_case.exp) for test_case in test_cases]
)
def test_get_isbn_10_and_13(tc, exp) -> None:
    if not tc.err:
        result = get_isbn_10_and_13(tc.input)
        assert (
            result == exp
        ), f"For test case {tc.input}, expected {exp}, but got {result}"

    else:
        with pytest.raises(tc.err):
            get_isbn_10_and_13(["1234"])
