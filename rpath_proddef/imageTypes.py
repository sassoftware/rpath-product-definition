#
# Copyright (c) 2008 rPath, Inc.
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
Image types.
Kept for compatibility, you should use the imageType factory from a
ProductDefinition or PlatformDefinition object.
"""

import api1

module = api1.BaseDefinition.loadModule(api1.BaseDefinition.version)
class Image(module.imageTypeSub):
    # Preserve interface for mint - it tries to build its own type maps based
    # on the images
    _schemaToPythonTypeMap = {
        'xsd:string' : str,
        'xsd:boolean' : bool,
        'xsd:positiveInteger' : int,
        'rpd:troveSpecType' : str,
        'xsd:nonNegativeInteger' : int,
    }
    _attributes = dict([(x.name, _schemaToPythonTypeMap[x.data_type])
        for x in module.imageTypeSub.member_data_items_
            if x.name not in ('containerFormat', 'valueOf_')])

    def __init__(self, fields):
        module.imageTypeSub.__init__(self, **fields)
