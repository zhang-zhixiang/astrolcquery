import argparse
import warnings

import astropy.units as u

from .client import LCQueryClient

_IGNORED = (DeprecationWarning, FutureWarning, PendingDeprecationWarning)


def main(argv=None):
    for cat in _IGNORED:
        warnings.filterwarnings("ignore", category=cat)
    parser = argparse.ArgumentParser(
        prog="lcquery",
        description="Query and download multi-survey light curves for a target.",
    )
    parser.add_argument(
        "--survey",
        "-s",
        nargs="+",
        default=None,
        metavar="SURVEY",
        help="Surveys to query (e.g. ztf asassn). Defaults to all surveys.",
    )
    parser.add_argument(
        "--radius", type=float, default=5.0, help="Search radius in arcseconds."
    )
    parser.add_argument("--plot", action="store_true", help="Plot after download.")
    parser.add_argument(
        "--cache", action="store_true", help="Use the local cache directory."
    )
    parser.add_argument(
        "--target",
        "-t",
        nargs="+",
        required=True,
        metavar="TARGET",
        help="Target as '<ra> <dec>' or a resolvable name.",
    )
    args = parser.parse_args(argv)

    target = args.target if len(args.target) == 2 else args.target[0]
    cache_dir = None
    if args.cache:
        import os

        cache_dir = os.path.expanduser("~/.astrolcquery/cache")

    client = LCQueryClient(surveys=args.survey, cache_dir=cache_dir)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        collection = client.get_lightcurve(
            target,
            radius=args.radius * u.arcsec,
            surveys=args.survey,
            use_cache=args.cache,
        )
        for w in caught:
            if isinstance(w.message, _IGNORED):
                continue
            print(f"WARNING: {w.message}")

    if not collection.lcs:
        print("No data retrieved for the requested target/surveys.")
        return

    print(collection)
    for lc in collection:
        print(lc)

    if args.plot:
        if len(collection.lcs) == 1:
            collection.lcs[0].plot()
        else:
            collection.plot_atlas()
        import matplotlib.pyplot as plt

        plt.show()


if __name__ == "__main__":
    main()
