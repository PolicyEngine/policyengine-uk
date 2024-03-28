from argparse import ArgumentParser


def convert_to_index(pct_change_series: list, rounding: int) -> list:
    """
    Convert a list of percentage changes to an index
    """
    index = [1]
    for pct in pct_change_series:
        index.append(index[-1] * (1 + pct / 100))

    index = [round(i, rounding) for i in index]
    return index


def main():
    parser = ArgumentParser(
        description="Convert a list of percentage changes to an index"
    )
    parser.add_argument(
        "pct_change_series",
        type=float,
        nargs="+",
        help="A list of percentage changes",
    )
    parser.add_argument(
        "--rounding",
        type=int,
        default=2,
        help="Number of decimal places to round to",
    )
    args = parser.parse_args()
    print(
        " ".join(
            map(str, convert_to_index(args.pct_change_series, args.rounding))
        )
    )


if __name__ == "__main__":
    main()
