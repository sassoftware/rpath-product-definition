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
"""

from rpath_common import xmllib
from rpath_common.proddef import _xmlConstants

#{ Image Type Class
class Image(xmllib.SerializableObject):
    _defaultNamespace = _xmlConstants.defaultNamespaceList[0]
    tag = "image"

    _attributes = {
        'containerFormat'           : (str, ),

        'amiHugeDiskMountpoint'     : (str, ),
        'anacondaCustomTrove'       : (str, ),
        'anacondaTemplatesTrove'    : (str, ),
        'autoResolve'               : (bool, ),
        'baseFileName'              : (str, ),
        'betaNag'                   : (bool, ),
        'bugsUrl'                   : (str, ),
        'buildOVF10'               : (bool, ),
        'diskAdapter'               : (str, ),
        'freespace'                 : (int, ),
        'installLabelPath'          : (str, ),
        'maxIsoSize'                : (int, ),
        'mediaTemplateTrove'        : (str, ),
        'name'                      : (str, ),
        'natNetworking'             : (bool, ),
        'showMediaCheck'            : (bool, ),
        'swapSize'                  : (int, ),
        'unionfs'                   : (bool, ),
        'vhdDiskType'               : (str, ),
        'vmMemory'                  : (int, ),
        'vmSnapshots'               : (bool, ),
        'zisofs'                    : (bool, ),
    }

    def __init__(self, node = None):
        """
        Initialize an ImageType object, either from a Node, or from a
        dictionary of fields.
        """

        self.fields = flds = {}
        self.containerFormat = None

        if node is None:
            return

        if isinstance(node, dict):
            getAttribute = node.get
            self.containerFormat = node.get('containerFormat')
        else:
            getAttribute = node.getAttribute
            self.containerFormat = getAttribute('containerFormat')

        for attrName, values in sorted(self._attributes.items()):
            # containerFormat isn't a build option, but may appear in the
            # fields due to API nuances
            if attrName == 'containerFormat':
                continue
            attrType = values[0]
            val = getAttribute(attrName)
            if val is None:
                continue
            if attrType == bool:
                val = xmllib.BooleanNode.fromString(val)
            elif attrType == int:
                val = int(val)
            flds[attrName] = val

    def __eq__(self, obj):
        if not hasattr(obj, 'containerFormat'):
            return False
        if self.containerFormat != obj.containerFormat:
            return False
        if not hasattr(obj, 'fields'):
            return False
        if self.fields != obj.fields:
            return False
        return True

    def __ne__(self, obj):
        return not self.__eq__(obj)

    @classmethod
    def getTag(kls):
        return kls.tag

    def _getName(self):
        return self.tag

    def _getLocalNamespaces(self):
        return {}

    def _iterAttributes(self):
        if self.containerFormat is not None:
            yield ('containerFormat', self.containerFormat)
        for key, val in self.fields.iteritems():
            yield key, val

    def _iterChildren(self):
        return []
#}


