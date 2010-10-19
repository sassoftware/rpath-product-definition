#
# Copyright (c) 2006-2010 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
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

version = '4.2'
defaultNamespaceList = [ "http://www.rpath.com/permanent/rpd-%s.xsd" % version ]
xmlSchemaNamespace = "http://www.w3.org/2001/XMLSchema-instance"
xmlSchemaLocation = ("http://www.rpath.com/permanent/rpd-%s.xsd rpd-%s.xsd" %
    (version, version))
