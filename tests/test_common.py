"""
test_common
===========

Tests for the `common` module of the `maniphono` package.
"""

# Import Python libraries
import unittest
import pytest

# Import the library itself
import maniphono


def test_codepoint2glyph():
    assert maniphono.codepoint2glyph("U+0283") == "ʃ"


def test_replace_codepoints():
    assert maniphono.replace_codepoints("aU+0283o") == "aʃo"
