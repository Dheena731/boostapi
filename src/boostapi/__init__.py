"""BoostAPI - Production FastAPI starter toolkit.

Example Usage::

    from boostapi import create_app

    app = create_app()
    # uvicorn myapp:app --reload

Or with custom settings::

    from boostapi import create_app, Settings

    app = create_app(settings=Settings(
        POSTGRES_DB="mydb",
        SECRET_KEY="my-secret",
    ))
"""

from ._version import __version__
from .app.main import create_app
from .app.core.config import Settings
from .cli import main

__author__ = "Dhinakaran"
__license__ = "MIT"

__all__ = [
    "create_app",
    "Settings",
    "main",
    "__version__",
]

