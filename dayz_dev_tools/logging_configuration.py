import logging


def configure_logging(*, debug: bool) -> None:
    if debug:
        logging.basicConfig(
            format="%(asctime)s %(levelname)s:%(module)s:%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S%z",
            level=logging.DEBUG)
    else:
        logging.basicConfig(
            format="%(asctime)s %(levelname)s:%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S%z",
            level=logging.INFO)
