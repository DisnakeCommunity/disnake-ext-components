# pyright: reportImportCycles = false
# pyright: reportWildcardImportFromLibrary = false
# ^ This is a false positive as it is confused with site-packages' disnake.

"""The main disnake-ext-components module.

An extension for disnake aimed at making component interactions with
listeners somewhat less cumbersome.
"""

__title__ = "disnake-ext-components"
__author__ = "Chromosomologist"
__version__ = "0.5.0a1"
__license__ = "MIT"
__copyright__ = "2022, Chromosomologist"


from disnake.ext.components import api as api
from disnake.ext.components import internal as internal
from disnake.ext.components.fields import *
from disnake.ext.components.impl import *
from disnake.ext.components.interaction import *
