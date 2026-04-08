"""Main entry point for sum_even_numbers."""

import argparse
import sys


def sum_even_numbers(numbers: list[int]) -> int:
    """Calculates the sum of even numbers in a list."""
    if not numbers:
        return 0
    return sum(n for n in numbers if n % 2 == 0)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Sum even numbers from a list of integers.")
    parser.add_argument("numbers", metavar="N", type=int, nargs="*", help="A list of integers.")

    try:
        args = parser.parse_args()
        result = sum_even_numbers(args.numbers)
        print(result)
    except SystemExit:
        # argparse default behavior for invalid types is SystemExit(2)
        sys.exit(2)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
