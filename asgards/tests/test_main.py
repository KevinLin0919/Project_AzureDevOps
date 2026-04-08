import sys

import pytest

from asgards.src.main import main, sum_even_numbers


@pytest.mark.parametrize(
    "numbers, expected",
    [
        ([1, 2, 3, 4, 5, 6], 12),
        ([1, 3, 5], 0),
        ([2, 4, 8], 14),
        ([], 0),
        ([-2, -4, 1, 3], -6),
        ([-1, -3, -5], 0),
        ([0, 0, 0], 0),
        ([100, 201, 300], 400),
        ([10**6, 10**6 + 1, 10**6 + 2], 2000002),
    ],
)
def test_sum_even_numbers(numbers, expected):
    assert sum_even_numbers(numbers) == expected


def test_sum_even_numbers_with_single_element():
    assert sum_even_numbers([2]) == 2
    assert sum_even_numbers([3]) == 0


def test_main_success(capsys, monkeypatch):
    """Test the main function with valid arguments."""
    monkeypatch.setattr(sys, "argv", ["main.py", "1", "2", "3", "4"])
    main()
    captured = capsys.readouterr()
    assert captured.out.strip() == "6"


def test_main_empty_args(capsys, monkeypatch):
    """Test the main function with no arguments."""
    monkeypatch.setattr(sys, "argv", ["main.py"])
    main()
    captured = capsys.readouterr()
    assert captured.out.strip() == "0"


def test_main_invalid_args(capsys, monkeypatch):
    """Test the main function with invalid argument types."""
    monkeypatch.setattr(sys, "argv", ["main.py", "abc"])
    with pytest.raises(SystemExit) as e:
        main()
    assert e.value.code == 2
