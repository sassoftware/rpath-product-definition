#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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

version = '4.6'
defaultNamespaceList = [ "http://www.rpath.com/permanent/rpd-%s.xsd" % version ]
xmlSchemaNamespace = "http://www.w3.org/2001/XMLSchema-instance"
xmlSchemaLocation = ("http://www.rpath.com/permanent/rpd-%s.xsd rpd-%s.xsd" %
    (version, version))
