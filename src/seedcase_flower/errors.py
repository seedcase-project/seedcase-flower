"""Custom exception handling for seedcase-flower."""

import sys
from urllib.error import HTTPError, URLError

from check_datapackage import (
    DataPackageError,
    create_no_traceback_hook,
    create_no_traceback_ipython_handler,
)


sys.excepthook = create_no_traceback_hook(
    DataPackageError, FileNotFoundError, HTTPError, URLError
)


def _is_running_from_ipython() -> bool:
    """Checks whether running in IPython interactive console or not."""
    try:
        from IPython import get_ipython
    except ImportError:
        return False
    else:
        return get_ipython() is not None


if _is_running_from_ipython():
    get_ipython().set_custom_exc(  # type: ignore[misc]
        (Exception,),
        create_no_traceback_ipython_handler(
            DataPackageError, FileNotFoundError, HTTPError, URLError
        ),
    )
