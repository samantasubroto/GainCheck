import logging


def setup_logging():
    """Make log messages print to the terminal with a time and a level."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
