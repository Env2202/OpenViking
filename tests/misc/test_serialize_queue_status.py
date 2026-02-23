# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Tests for openviking.service._helpers.serialize_queue_status."""

from datetime import datetime

from openviking.service._helpers import serialize_queue_status
from openviking.storage.queuefs.named_queue import QueueError, QueueStatus


class TestSerializeQueueStatus:
    """Tests for serialize_queue_status helper."""

    def test_empty_status(self):
        """An empty dict should return an empty dict."""
        assert serialize_queue_status({}) == {}

    def test_single_queue_no_errors(self):
        """A single queue with no errors serializes correctly."""
        status = {
            "semantic": QueueStatus(pending=0, in_progress=0, processed=5, error_count=0),
        }
        result = serialize_queue_status(status)
        assert result == {
            "semantic": {
                "processed": 5,
                "error_count": 0,
                "errors": [],
            },
        }

    def test_single_queue_with_errors(self):
        """Errors are serialized to dicts with a 'message' key."""
        errors = [
            QueueError(timestamp=datetime(2026, 1, 1), message="embedding failed"),
            QueueError(timestamp=datetime(2026, 1, 2), message="timeout"),
        ]
        status = {
            "vectorize": QueueStatus(
                pending=0, in_progress=0, processed=3, error_count=2, errors=errors
            ),
        }
        result = serialize_queue_status(status)
        assert result == {
            "vectorize": {
                "processed": 3,
                "error_count": 2,
                "errors": [
                    {"message": "embedding failed"},
                    {"message": "timeout"},
                ],
            },
        }

    def test_multiple_queues(self):
        """Multiple queues are all serialized."""
        status = {
            "semantic": QueueStatus(processed=10, error_count=0),
            "vectorize": QueueStatus(processed=8, error_count=1, errors=[
                QueueError(timestamp=datetime(2026, 1, 1), message="bad vector"),
            ]),
        }
        result = serialize_queue_status(status)
        assert len(result) == 2
        assert result["semantic"]["processed"] == 10
        assert result["semantic"]["errors"] == []
        assert result["vectorize"]["processed"] == 8
        assert result["vectorize"]["error_count"] == 1
        assert result["vectorize"]["errors"] == [{"message": "bad vector"}]
