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
@var defaultNamespaceList: List of supported namespaces, the preferred
    namespace being first. Normally, augmenting the schema in a
    backwards-compatible way (i.e. with pure additions) should not result in a
    new namespace being generated.
@type defaultNamespaceList: list
@var xmlSchemaNamespace: XML Schema namespace
@type xmlSchemaNamespace: C{str}
@var xmlSchemaLocation: XML Schema location
@type xmlSchemaLocaltion: C{str}
"""

version = '4.3'
defaultNamespaceList = [ "http://www.rpath.com/permanent/rpd-%s.xsd" % version ]
xmlSchemaNamespace = "http://www.w3.org/2001/XMLSchema-instance"
xmlSchemaLocation = ("http://www.rpath.com/permanent/rpd-%s.xsd rpd-%s.xsd" %
    (version, version))
