# pyright: reportImportCycles = false
# pyright: reportWildcardImportFromLibrary = false
# ^ This is a false positive as it is confused with site-packages' disnake.

"""Protocols for disnake-ext-components internals.

These are provided to decouple the implementation details from their respective
implementations, so that custom implementations can be created accordingly.
This allows users to slot their own implementations into the library that
properly interface with the existing logic, thus maintaining functionality.
"""

from __future__ import annotations

from disnake.ext.components.api.component import *
from disnake.ext.components.api.custom_id import *
from disnake.ext.components.api.parser import *
