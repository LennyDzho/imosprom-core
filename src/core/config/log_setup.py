import logging


def setup_logging(debug: bool = False):
    log_level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] #%(levelname)-1s | [%(processName)s] | %(name)s: %(message)s",
        datefmt="%m %d %Y %H:%M:%S",
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
