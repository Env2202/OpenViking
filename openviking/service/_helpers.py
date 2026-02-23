# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""
Shared helpers for the service layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from openviking.storage.queuefs.named_queue import QueueStatus
from openviking_cli.exceptions import NotInitializedError

if TYPE_CHECKING:
    from openviking.storage.viking_fs import VikingFS


def serialize_queue_status(status: Dict[str, QueueStatus]) -> Dict[str, Any]:
    """Serialize queue completion status to a JSON-friendly dict.

    Args:
        status: Mapping of queue name to QueueStatus, as returned by
            ``QueueManager.wait_complete()``.

    Returns:
        A dict keyed by queue name, each value containing ``processed``,
        ``error_count``, and ``errors`` fields.
    """
    return {
        name: {
            "processed": s.processed,
            "error_count": s.error_count,
            "errors": [{"message": e.message} for e in s.errors],
        }
        for name, s in status.items()
    }


class VikingFSService:
    """Base class for services that depend on a single VikingFS instance.

    Provides a shared ``__init__``, ``set_viking_fs``, and
    ``_ensure_initialized`` so that each sub-service does not need to
    duplicate the same boilerplate.
    """

    def __init__(self, viking_fs: Optional[VikingFS] = None) -> None:
        self._viking_fs = viking_fs

    def set_viking_fs(self, viking_fs: VikingFS) -> None:
        """Set VikingFS instance (for deferred initialization)."""
        self._viking_fs = viking_fs

    def _ensure_initialized(self) -> VikingFS:
        """Return the VikingFS instance, raising if not yet set."""
        if not self._viking_fs:
            raise NotInitializedError("VikingFS")
        return self._viking_fs
