#
# Copyright (c) rPath, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


"""
The rPath Common Library Module for Product Definition

This module provides a stable interface for reading and writing
rPath product definition XML files.  This interface will be
backward-compatible within major versions of this package.
The C{VERSION} data element is a string containing the version.
The portion of the string before the initial C{.} character is the
major version.

All interfaces in this modules that do not start with a C{_}
character are public interfaces.

If the C{VERSION} starts with C{0.}, none of the included
interfaces is stable and may change without warning.

To use the latest version of the interface::
    import rpath_proddef
To use a specific API Version of the interface::
    from rpath_proddef import api1 as proddef
"""

# Default to current API version
#pylint: disable-msg=W0401
from rpath_proddef.api1 import *

# Import the automatically-generated VERSION
#pylint: disable-msg=W0212
from rpath_proddef.proddef_constants import _VERSION as VERSION
