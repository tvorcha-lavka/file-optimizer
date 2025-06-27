#!/usr/bin/env python
"""
Runs pytest with provided flags `--pytest` and `--pytest-cov`.

Flag `--pytest` runs only pytest.
Flag `--pytest-cov` runs pytest with coverage.
"""
from argparse import ArgumentParser, RawTextHelpFormatter
from itertools import chain


def run_pytest(cov_report: bool = False) -> None:
    from pytest import main as run

    _base_params = [
        ["--config-file=/tmp/pyproject.toml"],
        ["--rootdir=/src"],
    ]
    _cov_params = [
        ["--cov-config=/tmp/pyproject.toml"],
        ["-m", "not (xfail or skip)"],
        ["--cov"],
    ]

    base_params = list(chain.from_iterable(_base_params))
    cov_params = list(chain.from_iterable(_cov_params))

    run(base_params + cov_params if cov_report else base_params)


def main() -> None:
    parser = ArgumentParser(formatter_class=RawTextHelpFormatter)

    parser.add_argument(
        "--pytest",
        required=False,
        action="store_true",
        help="Runs pytest.",
    )
    parser.add_argument(
        "--pytest-cov",
        required=False,
        action="store_true",
        help="Runs pytest with coverage.",
    )

    args = parser.parse_args()

    if args.pytest:
        run_pytest()

    elif args.pytest_cov:
        run_pytest(cov_report=True)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
