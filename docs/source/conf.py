"""Sphinx configuration."""

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
import typing

import sphinx.config
from disnake.ext import commands, components

from docs.source import util

sys.modules["components"] = components
sys.modules["commands"] = commands
sys.path.append(os.path.abspath("./extensions"))

project = "disnake-ext-components"
copyright = "2023, Sharp-Eyes"
author = "Sharp-Eyes"
release = "0.5.0a1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # In sphinx.
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.linkcode",
    "sphinx.ext.napoleon",
    # External.
    "sphinxcontrib_trio",
    "sphinx_inline_tabs",
    "sphinx_copybutton",
    "hoverxref.extension",
    "sphinx_autodoc_typehints",
    "enum_tools.autoenum",
    # Custom.
    "attributetable",
]
exclude_patterns = []

# add_module_names = False
pygments_style = "friendly"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_theme_options = {
    "source_repository": "https://github.com/DisnakeCommunity/disnake-ext-components",
    "source_branch": "master",
    # Taken directly from Furo docs at https://github.com/pradyunsg/furo/blob/main/docs/conf.py.
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/DisnakeCommunity/disnake-ext-components/",
            "html": """
                    <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                    </svg>
                """,  # noqa: E501
            "class": "",
        },
    ],
}
html_show_sourcelink = False

html_static_path = ["_static"]
html_css_files = ["./css/custom.css", "./css/attributetable.css"]
html_js_files = ["./js/custom.js"]

# -- Intersphinx config -------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "disnake": ("https://docs.disnake.dev/en/stable/", None),
    "attrs": ("https://www.attrs.org/en/stable/", None),
}

# -- Autodoc config -----------------------------------------------------------

autodoc_member_order = "groupwise"
autodoc_typehints = "signature"
autodoc_default_options = {"show-inheritance": True, "inherited-members": False}

# -- Hoverxref config ---------------------------------------------------------

hoverx_default_type = "tooltip"
hoverxref_domains = ["py"]
hoverxref_role_types = dict.fromkeys(
    ["ref", "class", "func", "meth", "attr", "exc", "data", "obj"],
    "tooltip",
)
hoverxref_tooltip_theme = ["tooltipster-custom"]
hoverxref_tooltip_lazy = True

# These have to match the keys on intersphinx_mapping, and those projects must
# be hosted on readthedocs.
hoverxref_intersphinx = list(intersphinx_mapping)


# -- Linkcode config ----------------------------------------------------------

repo_url = "https://github.com/DisnakeCommunity/disnake-ext-components"

git_ref = util.get_git_ref()
module_path = util.get_module_path()
linkcode_resolve = util.make_linkcode_resolver(module_path, repo_url, git_ref)


# -- sphinx-autodoc-typehints config ------------------------------------------

# Apply monkeypatch.
util.apply_patch()

typehints_document_rtype = False
typehints_use_rtype = False
simplify_optional_unions = False


# Customise display for specific types.
import attrs
import disnake
from disnake.ext.components.api import component, parser

util.make_generic(attrs.Attribute)


aliases: typing.Dict[object, str] = {
    # Idk why this is needed, but it is...
    disnake.ButtonStyle: ":class:`~disnake.ButtonStyle`",
    component.ComponentT: ":data:`~.ComponentT`",  # pyright: ignore
    parser.ParserType: ":data:`.ParserType`",  # pyright: ignore
}


def typehints_formatter(ann: object, _: sphinx.config.Config) -> typing.Optional[str]:
    """Format typehints."""
    if typehint := aliases.get(ann):
        return typehint

    return None
