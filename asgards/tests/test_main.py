import pytest

from asgards.src.main import sum_even_numbers


@pytest.mark.parametrize("numbers, expected", [
    ([1, 2, 3, 4, 5, 6], 12),
    ([1, 3, 5], 0),
    ([2, 4, 8], 14),
    ([], 0),
    ([-2, -4, 1, 3], -6),
    ([-1, -3, -5], 0),
    ([0, 0, 0], 0),
    ([100, 201, 300], 400),
    ([10**6, 10**6 + 1, 10**6 + 2], 2000002),
])
def test_sum_even_numbers(numbers, expected):
    assert sum_even_numbers(numbers) == expected


def test_sum_even_numbers_with_single_element():
    assert sum_even_numbers([2]) == 2
    assert sum_even_numbers([3]) == 0
