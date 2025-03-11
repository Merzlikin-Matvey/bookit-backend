import os
import sys
import pytest

pytest_plugins = ["pytest_asyncio"]

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
