from asgards.src.main import sum_even_numbers


def test_sum_even_numbers():
    assert sum_even_numbers([1, 2, 3, 4, 5, 6]) == 12
    assert sum_even_numbers([1, 3, 5]) == 0
    assert sum_even_numbers([2, 4, 8]) == 14
    assert sum_even_numbers([]) == 0
