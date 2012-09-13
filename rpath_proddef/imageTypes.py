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
