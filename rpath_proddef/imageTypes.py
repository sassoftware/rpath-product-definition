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
