"""Custom exception handling for seedcase-flower."""

from urllib.error import HTTPError, URLError

from check_datapackage import setup_no_traceback_hooks


setup_no_traceback_hooks(FileNotFoundError, HTTPError, URLError)
