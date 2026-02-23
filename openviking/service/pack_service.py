# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""
Pack Service for OpenViking.

Provides ovpack export/import operations.
"""

from openviking.service._helpers import VikingFSService
from openviking.storage.local_fs import export_ovpack as local_export_ovpack
from openviking.storage.local_fs import import_ovpack as local_import_ovpack
from openviking_cli.utils import get_logger

logger = get_logger(__name__)


class PackService(VikingFSService):
    """OVPack export/import service."""

    async def export_ovpack(self, uri: str, to: str) -> str:
        """Export specified context path as .ovpack file.

        Args:
            uri: Viking URI
            to: Target file path

        Returns:
            Exported file path
        """
        viking_fs = self._ensure_initialized()
        return await local_export_ovpack(viking_fs, uri, to)

    async def import_ovpack(
        self, file_path: str, parent: str, force: bool = False, vectorize: bool = True
    ) -> str:
        """Import local .ovpack file to specified parent path.

        Args:
            file_path: Local .ovpack file path
            parent: Target parent URI (e.g., viking://user/alice/resources/references/)
            force: Whether to force overwrite existing resources
            vectorize: Whether to trigger vectorization

        Returns:
            Imported root resource URI
        """
        viking_fs = self._ensure_initialized()
        return await local_import_ovpack(
            viking_fs, file_path, parent, force=force, vectorize=vectorize
        )
