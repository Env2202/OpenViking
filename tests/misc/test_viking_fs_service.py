# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Tests for VikingFSService base class.

Uses importlib.util to load ``_helpers.py`` directly, bypassing the heavy
``openviking.__init__`` import chain so that the test can run in
environments that lack optional C/Go dependencies.
"""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Minimal import bootstrap – load _helpers.py directly to avoid the heavy
# openviking.__init__ chain that requires PIL, apscheduler, etc.
# ---------------------------------------------------------------------------
_root = Path(__file__).resolve().parents[2]

# 1. Load openviking_cli.exceptions (lightweight, no heavy deps)
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
from openviking_cli.exceptions import NotInitializedError  # noqa: E402

# 2. Load _helpers module directly by file path
_helpers_path = _root / "openviking" / "service" / "_helpers.py"
_spec = importlib.util.spec_from_file_location("_helpers", _helpers_path)
_helpers = importlib.util.module_from_spec(_spec)

# Stub out the QueueStatus import that _helpers needs at module level
_queue_mod_name = "openviking.storage.queuefs.named_queue"
if _queue_mod_name not in sys.modules:
    _qs_path = _root / "openviking" / "storage" / "queuefs" / "named_queue.py"
    _qs_spec = importlib.util.spec_from_file_location(_queue_mod_name, _qs_path)
    _qs_mod = importlib.util.module_from_spec(_qs_spec)
    sys.modules[_queue_mod_name] = _qs_mod
    _qs_spec.loader.exec_module(_qs_mod)

_spec.loader.exec_module(_helpers)
VikingFSService = _helpers.VikingFSService


class TestVikingFSServiceInit:
    """VikingFSService.__init__ and set_viking_fs."""

    def test_default_init_has_no_viking_fs(self):
        svc = VikingFSService()
        assert svc._viking_fs is None

    def test_init_with_viking_fs(self):
        fake_vfs = MagicMock()
        svc = VikingFSService(viking_fs=fake_vfs)
        assert svc._viking_fs is fake_vfs

    def test_set_viking_fs(self):
        svc = VikingFSService()
        fake_vfs = MagicMock()
        svc.set_viking_fs(fake_vfs)
        assert svc._viking_fs is fake_vfs


class TestVikingFSServiceEnsureInitialized:
    """VikingFSService._ensure_initialized."""

    def test_raises_when_not_initialized(self):
        svc = VikingFSService()
        with pytest.raises(NotInitializedError):
            svc._ensure_initialized()

    def test_returns_viking_fs_when_initialized(self):
        fake_vfs = MagicMock()
        svc = VikingFSService(viking_fs=fake_vfs)
        result = svc._ensure_initialized()
        assert result is fake_vfs

    def test_returns_viking_fs_after_set(self):
        svc = VikingFSService()
        fake_vfs = MagicMock()
        svc.set_viking_fs(fake_vfs)
        result = svc._ensure_initialized()
        assert result is fake_vfs


class TestSubclassBehavior:
    """Verify subclass inherits VikingFSService behaviour correctly."""

    def test_subclass_inherits_init(self):
        """A subclass without its own __init__ gets the base one."""

        class MyService(VikingFSService):
            pass

        svc = MyService()
        assert svc._viking_fs is None

        fake_vfs = MagicMock()
        svc2 = MyService(viking_fs=fake_vfs)
        assert svc2._viking_fs is fake_vfs

    def test_subclass_inherits_ensure_initialized(self):
        """A subclass instance uses the inherited _ensure_initialized."""

        class MyService(VikingFSService):
            pass

        svc = MyService()
        with pytest.raises(NotInitializedError):
            svc._ensure_initialized()

        fake_vfs = MagicMock()
        svc.set_viking_fs(fake_vfs)
        assert svc._ensure_initialized() is fake_vfs

    def test_subclass_can_add_methods(self):
        """A subclass can add its own methods that use _ensure_initialized."""

        class MyService(VikingFSService):
            def do_something(self):
                vfs = self._ensure_initialized()
                return vfs.some_method()

        fake_vfs = MagicMock()
        fake_vfs.some_method.return_value = 42
        svc = MyService(viking_fs=fake_vfs)
        assert svc.do_something() == 42
        fake_vfs.some_method.assert_called_once()
