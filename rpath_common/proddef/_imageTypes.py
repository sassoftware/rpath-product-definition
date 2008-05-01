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
Private interface.
"""

from rpath_common import xmllib
from rpath_common.proddef import _xmlConstants

class ImageType_Dispatcher(object):
    _dispatcher = {}

    @classmethod
    def addImageType(kls, imageType):
        key = "{%s}%s" % (imageType._defaultNamespace, imageType.tag)
        kls._dispatcher[key] = imageType

    @classmethod
    def dispatch(kls, node):
        absName = node.getAbsoluteName()
        if absName not in kls._dispatcher:
            return None
        nodeClass = kls._dispatcher.get(absName)

        fields = {}
        for attrName, values in nodeClass._attributes.items():
            attrType = values[0]
            val = node.getAttribute(attrName)
            if val is None:
                continue
            if attrType == bool:
                val = (val.strip().upper() in ["TRUE", "1"] and True) or False
            elif attrType == int:
                val = int(val)
            fields[attrName] = val
        obj = nodeClass(fields)
        return obj

#{ Image Type Classes
class ImageType_Base(xmllib.SerializableObject):
    _defaultNamespace = _xmlConstants.defaultNamespace

    _attributes = {
        'name'              : (str, ),
        'autoResolve'       : (bool, ),
        'baseFileName'      : (str, ),
        'installLabelPath'  : (str, ),
    }

    def __init__(self, fields):
        self.fields = fields

    def _getName(self):
        return self.tag

    def _getLocalNamespaces(self):
        return {}

    def _iterAttributes(self):
        return self.fields.iteritems()

    def _iterChildren(self):
        return []


class ImageType_AMI(ImageType_Base):
    tag = "amiImage"
    _attributes = ImageType_Base._attributes.copy()
    _attributes.update({
        'amiHugeDiskMountpoint'     : (str, ),
        'freespace'                 : (int, ),
    })

class ImageType_InstallableISO(ImageType_Base):
    tag = "installableIsoImage"
    _attributes = ImageType_Base._attributes.copy()
    _attributes.update({
        'maxIsoSize'                : (int, ),
        'bugsUrl'                   : (str, ),
        'showMediaCheck'            : (bool, ),
        'betaNag'                   : (bool, ),
        'mediaTemplateTrove'        : (str, ),
        'anacondaCustomTrove'       : (str, ),
        'anacondaTemplatesTrove'    : (str, ),
    })

class ImageType_LiveIso(ImageType_Base):
    tag = "liveIsoImage"
    _attributes = ImageType_Base._attributes.copy()
    _attributes.update({
        'unionfs'                   : (bool, ),
        'zisofs'                    : (bool, ),
    })

class ImageType_Netboot(ImageType_Base):
    tag = "netbootImage"
    _attributes = ImageType_Base._attributes.copy()
    _attributes.update({
    })

class ImageType_RawFs(ImageType_Base):
    tag = "rawFsImage"
    _attributes = ImageType_Base._attributes.copy()
    _attributes.update({
        'swapSize'          : (int, ),
        'freespace'         : (int, ),
    })

class ImageType_RawHd(ImageType_Base):
    tag = "rawHdImage"
    _attributes = ImageType_Base._attributes.copy()
    _attributes.update({
        'swapSize'          : (int, ),
        'freespace'         : (int, ),
    })

class ImageType_Tarball(ImageType_Base):
    tag = "tarballImage"
    _attributes = ImageType_Base._attributes.copy()
    _attributes.update({
        'swapSize'          : (int, ),
    })

class ImageType_UpdateIso(ImageType_Base):
    tag = "updateIsoImage"
    # No inheritance
    _attributes = {
        'baseFileName'          : (str, ),
        'mediaTemplateTrove'    : (str, ),
    }

class ImageType_VHD(ImageType_Base):
    tag = "vhdImage"
    _attributes = ImageType_Base._attributes.copy()
    _attributes.update({
        'swapSize'          : (int, ),
        'freespace'         : (int, ),
        'vhdDiskType'       : (str, ),
    })

class ImageType_VMWare(ImageType_Base):
    tag = "vmwareImage"
    _attributes = ImageType_Base._attributes.copy()
    _attributes.update({
        'swapSize'          : (int, ),
        'freespace'         : (int, ),
        'natNetworking'     : (bool, ),
        'diskAdapter'       : (str, ),
        'vmSnapshots'       : (bool, ),
        'vmMemory'          : (int, ),
    })

class ImageType_VMWareEsx(ImageType_Base):
    tag = "vmwareEsxImage"
    _attributes = ImageType_Base._attributes.copy()
    _attributes.update({
        'swapSize'          : (int, ),
        'freespace'         : (int, ),
        'natNetworking'     : (bool, ),
    })
#}

# Globally register all image types defined in this module
for symVal in globals().values():
    if not isinstance(symVal, type):
        continue
    if issubclass(symVal, ImageType_Base) and symVal != ImageType_Base:
        ImageType_Dispatcher.addImageType(symVal)
