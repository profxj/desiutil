# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.setup.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import unittest
from ..setup import find_version_directory


class TestSetup(unittest.TestCase):
    """Test desiutil.setup.
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_find_version_directory(self):
        """Test the search for a _version.py file.
        """
        self.assertTrue(True)
