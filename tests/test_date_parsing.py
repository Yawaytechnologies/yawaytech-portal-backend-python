from datetime import datetime
import pytest

import importlib.util
from pathlib import Path

# Ensure project root is on sys.path so `app` package imports work
import sys
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the module by file path so tests remain stable even when run from different cwd
router_path = project_root / "app" / "routes" / "leave_employee_router.py"
spec = importlib.util.spec_from_file_location("leave_employee_router", str(router_path))
leave_employee_router = importlib.util.module_from_spec(spec)
spec.loader.exec_module(leave_employee_router)
_parse_flexible_datetime = leave_employee_router._parse_flexible_datetime


def test_parse_iso_date():
    assert _parse_flexible_datetime("2024-06-04") == datetime(2024, 6, 4)


def test_parse_ddmmyyyy_dash():
    assert _parse_flexible_datetime("04-06-2024") == datetime(2024, 6, 4)


def test_parse_ddmmyyyy_slash():
    assert _parse_flexible_datetime("04/06/2024") == datetime(2024, 6, 4)


def test_parse_invalid_raises():
    with pytest.raises(Exception):
        _parse_flexible_datetime("bad-date")
