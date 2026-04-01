def sum_even_numbers(numbers: list[int]) -> int:
    """Sums all even numbers in a list."""
    return sum(num for num in numbers if num % 2 == 0)

if __name__ == "__main__":
    nums = [1, 2, 3, 4, 5, 6]
    print(f"Sum of even numbers in {nums}: {sum_even_numbers(nums)}")
