# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""
Shared helpers for the service layer.
"""

from typing import Any, Dict

from openviking.storage.queuefs.named_queue import QueueStatus


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
