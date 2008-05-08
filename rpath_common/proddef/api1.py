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
The rPath Common Library Module for Product Definition, API version 1

All interfaces in this modules that do not start with a C{_}
character are public interfaces.
"""

__all__ = [ 'ProductDefinition', 'ProductDefinitionError',
            'UnsupportedImageType' ]

import StringIO

from rpath_common.xmllib import api1 as xmllib
from rpath_common.proddef import _xmlConstants
from rpath_common.proddef import imageTypes

#{ Exception classes
class ProductDefinitionError(Exception):
    "Base class for product definition exceptions"

class UnsupportedImageType(ProductDefinitionError):
    "Raised when an unsupported image type was passed"
#}

class ProductDefinition(object):
    """
    Represents the definition of a product.
    @cvar version:
    @type version: C{str}
    @cvar defaultNamespace:
    @type defaultNamespace: C{str}
    @cvar xmlSchemaNamespace:
    @type xmlSchemaNamespace: C{str}
    @cvar xmlSchemaLocation:
    @type xmlSchemaLocation: C{str}
    @cvar _imageTypeDispatcher: an object factory for imageType objects
    @type _imageTypeDispatcher: C{xmllib.NodeDispatcher}
    """
    version = '1.0'
    defaultNamespace = _xmlConstants.defaultNamespaceList[0]
    xmlSchemaNamespace = _xmlConstants.xmlSchemaNamespace
    xmlSchemaLocation = _xmlConstants.xmlSchemaLocation

    _imageTypeDispatcher = xmllib.NodeDispatcher({})
    _imageTypeDispatcher.registerClasses(imageTypes, imageTypes.ImageType_Base)

    def __init__(self, fromStream = None):
        """
        Initialize a ProductDefinition object, getting data from the optional
        XML stream.
        @param fromStream: An optional XML string or file
        @type fromStream: C{str} or C{file}
        """

        self._initFields()

        if fromStream:
            if isinstance(fromStream, (str, unicode)):
                fromStream = StringIO.StringIO(fromStream)
            self.parseStream(fromStream)

    def parseStream(self, stream):
        """
        Initialize the current object from an XML stream.
        @param stream: An XML stream
        @type stream: C{file}
        """
        self._initFields()
        binder = xmllib.DataBinder()
        binder.registerType(_ProductDefinition, 'productDefinition')
        xmlObj = binder.parseFile(stream)
        self.imageGroup = getattr(xmlObj, 'imageGroup', None)
        self.baseFlavor = getattr(xmlObj, 'baseFlavor', None)
        self.stages.extend(getattr(xmlObj, 'stages', []))
        self.upstreamSources.extend(getattr(xmlObj, 'upstreamSources', []))
        self.buildDefinition.extend(getattr(xmlObj, 'buildDefinition', []))

        ver = xmlObj.getAttribute('version')
        if ver is not None and ver != self.version:
            self.version = ver

        for nsName, nsVal in xmlObj.iterNamespaces():
            if nsName is None and nsVal != self.defaultNamespace:
                self.defaultNamespace = nsVal
                continue
            # XXX We don't support changing the schema location for now

    def serialize(self, stream):
        """
        Serialize the current object as an XML stream.
        @param stream: stream to write the serialized object
        @type stream: C{file}
        """
        attrs = {'version' : self.version,
                 'xmlns' : self.defaultNamespace,
                 'xmlns:xsi' : self.xmlSchemaNamespace,
                 "xsi:schemaLocation" : self.xmlSchemaLocation,
        }
        nameSpaces = {}
        serObj = _ProductDefinitionSerialization("productDefinition",
            attrs, nameSpaces, self)
        binder = xmllib.DataBinder()
        stream.write(binder.toXml(serObj))

    def getImageGroup(self):
        """
        @return: the image group
        @rtype: C{str}
        """
        return self.imageGroup

    def setImageGroup(self, imageGroup):
        """
        Set the image group name
        @param imageGroup: the image group name
        @type imageGroup: C{str}
        """
        self.imageGroup = imageGroup

    def getBaseFlavor(self):
        """
        @return: the base flavor
        @rtype: C{str}
        """
        return self.baseFlavor

    def setBaseFlavor(self, baseFlavor):
        """
        Set the base flavor.
        @param baseFlavor: the base flavor
        @type baseFlavor: C{str}
        """
        self.baseFlavor = baseFlavor

    def getStages(self):
        """
        @return: the stages from this product definition
        @rtype: C{list} of C{_Stage} objects
        """
        return self.stages

    def addStage(self, name = None, label = None):
        """
        Add a stage.
        @param name: the stage's name
        @type name: C{str} or C{None}
        @param label: Label for the stage
        @type label: C{str} or C{None}
        """
        obj = _Stage(name = name, label = label)
        self.stages.append(obj)

    def getUpstreamSources(self):
        """
        @return: the upstream sources from this product definition
        @rtype: C{list} of C{_UpstreamSource} objects
        """
        return self.upstreamSources

    def addUpstreamSource(self, troveName = None, label = None):
        """
        Add an upstream source.
        @param troveName: the trove name for the upstream source.
        @type name: C{str} or C{None}
        @param label: Label for the upstream source
        @type label: C{str} or C{None}
        """
        obj = _UpstreamSource(troveName = troveName, label = label)
        self.upstreamSources.append(obj)

    def getBuildDefinitions(self):
        """
        @return: The build definitions from this product definition
        @rtype: C{list} of C{_Build} objects
        """
        return self.buildDefinition

    def addBuildDefinition(self, name = None, baseFlavor = None,
                           imageType = None, stages = None, imageGroup = None):
        """
        Add a build definition.
        Image types are specified by calling C{ProductDefinition.imageType}.
        @param name: the name for the build definition
        @type name: C{str} or C{None}
        @param baseFlavor: the base flavor
        @type baseFlavor: C{str}
        @param imageType: an image type, as returned by
        C{ProductDefinition.imageType}.
        @type imageType: an instance of an C{imageTypes.ImageType_Base}
        @param stages: Stages for which to build this image type
        @type stages: C{list} of C{str} referring to a C{_Stage} object's name
        @param imageGroup: An optional image group that will override the
        product definition's image group
        @type imageGroup: C{str}
        subclass.
        """
        obj = _Build(name = name, baseFlavor = baseFlavor,
                     imageType = imageType, stages = stages,
                     imageGroup = imageGroup)
        self.buildDefinition.append(obj)

    @classmethod
    def imageType(cls, name, fields = None):
        """
        Image type factory. Given an image type name, it will instantiate an
        object of the proper type.
        @param name: The name of the image type.
        @type name: C{str}
        @param fields: Fields to initialize the image type object
        @type fields: C{dict}
        @raise UnsupportedImageType: when an unsupported image type is passed
        """
        fnode = _ImageTypeFakeNode(name, fields or {})
        obj = cls._imageTypeDispatcher.dispatch(fnode)
        if obj is None:
            raise UnsupportedImageType(name)
        return obj

    def getBuildsForStage(self, stageName):
        """
        Retrieve all build definitions for a stage name.
        @param stageName: stage name
        @type stageName: C{str}
        @return: A list of build definitions for the stage.
        @rtype: C{list} of C{_Build} objects
        """
        ret = []
        for build in self.getBuildDefinitions():
            if stageName in build.stages:
                ret.append(build)
        return ret

    def _initFields(self):
        self.baseFlavor = None
        self.stages = _Stages()
        self.imageGroup = None
        self.upstreamSources = _UpstreamSources()
        self.buildDefinition = _BuildDefinition()

#{ Objects for the representation of ProductDefinition fields

class _Stages(xmllib.SerializableList):
    tag = "stages"

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _UpstreamSources(xmllib.SerializableList):
    tag = "upstreamSources"

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _BuildDefinition(xmllib.SerializableList):
    tag = "buildDefinition"

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _Stage(xmllib.SlotBasedSerializableObject):
    __slots__ = [ 'name', 'label' ]
    tag = "stage"

    def __init__(self, name = None, label = None):
        xmllib.SlotBasedSerializableObject.__init__(self)
        self.name = name
        self.label = label

class _UpstreamSource(xmllib.SlotBasedSerializableObject):
    __slots__ = [ 'troveName', 'label' ]
    tag = "upstreamSource"

    def __init__(self, troveName = None, label = None):
        xmllib.SlotBasedSerializableObject.__init__(self)
        self.troveName = troveName
        self.label = label

class _Build(xmllib.SerializableObject):
    __slots__ = [ 'name', 'baseFlavor', 'imageType', 'stages', 'imageGroup' ]
    tag = "build"

    def __init__(self, name = None, baseFlavor = None,
                 imageType = None, stages = None, imageGroup = None):
        xmllib.SlotBasedSerializableObject.__init__(self)
        self.name = name
        self.baseFlavor = baseFlavor
        self.imageType = imageType
        self.stages = stages or []
        self.imageGroup = imageGroup

    def _getName(self):
        return self.tag

    def _getLocalNamespaces(self):
        return {}

    def _iterChildren(self):
        yield self.imageType
        for stage in self.stages:
            yield xmllib.NullNode(dict(ref=stage), name = 'stage')
        if self.imageGroup is not None:
            yield xmllib.StringNode(name = 'imageGroup').characters(
                self.imageGroup)

    def _iterAttributes(self):
        if self.name is not None:
            yield ('name', self.name)
        if self.baseFlavor is not None:
            yield ('baseFlavor', self.baseFlavor)

#}

class _ProductDefinition(xmllib.BaseNode):

    def __init__(self, attributes = None, nsMap = None, name = None):
        xmllib.BaseNode.__init__(self, attributes = attributes, nsMap = nsMap,
                                 name = name)
        self.defaultNamespace = self.getNamespaceMap().get(None)

    def addChild(self, childNode):
        chName = childNode.getAbsoluteName()

        if chName == self._makeAbsoluteName('imageGroup'):
            self.imageGroup = childNode.getText()
            return

        if chName == self._makeAbsoluteName('baseFlavor'):
            self.baseFlavor = childNode.getText()
            return

        if chName == self._makeAbsoluteName('stages'):
            children = childNode.getChildren('stage')
            self._addStages(children)
            return

        if chName == self._makeAbsoluteName('upstreamSources'):
            children = childNode.getChildren('upstreamSource')
            self._addUpstreamSources(children)
            return

        if chName == self._makeAbsoluteName('buildDefinition'):
            children = childNode.getChildren('build')
            self._addBuildDefinition(children)
            return

    def _makeAbsoluteName(self, name):
        return "{%s}%s" % (self.defaultNamespace, name)

    def _addStages(self, stagesNodes):
        stages = self.stages = []
        for node in stagesNodes:
            # XXX getAttribute should be getAbsoluteAttribute
            pyObj = _Stage(name = node.getAttribute('name'),
                           label = node.getAttribute('label'))
            stages.append(pyObj)

    def _addUpstreamSources(self, upstreamSources):
        sources = self.upstreamSources = []
        for node in upstreamSources:
            pyObj = _UpstreamSource(
                troveName = node.getAttribute('troveName'),
                label = node.getAttribute('label'))
            sources.append(pyObj)

    def _addBuildDefinition(self, buildNodes):
        dispatcher = xmllib.NodeDispatcher(self._nsMap)
        dispatcher.registerClasses(imageTypes, imageTypes.ImageType_Base)

        builds = self.buildDefinition = []
        for node in buildNodes:
            imgType = None
            for subNode in node.iterChildren():
                if not isinstance(subNode, xmllib.BaseNode):
                    continue
                imgType = dispatcher.dispatch(subNode)
                if imgType is not None:
                    break
            if imgType is None:
                raise UnsupportedImageType(subNode.getName())
            imageGroup = node.getChildren('imageGroup')
            if imageGroup:
                imageGroup = imageGroup[0].getText()
            else:
                imageGroup = None
            pyobj = _Build(
                name = node.getAttribute('name'),
                baseFlavor = node.getAttribute('baseFlavor'),
                imageType = imgType,
                stages = [ x.getAttribute('ref')
                           for x in node.getChildren('stage') ],
                imageGroup = imageGroup,
                )
            builds.append(pyobj)

class _ProductDefinitionSerialization(xmllib.BaseNode):
    def __init__(self, name, attrs, namespaces, prodDef):
        xmllib.BaseNode.__init__(self, attrs, namespaces, name = name)
        self.stages = prodDef.getStages()
        self.upstreamSources = prodDef.getUpstreamSources()
        self.buildDefinition = prodDef.getBuildDefinitions()

        self.imageGroup = xmllib.StringNode(name = 'imageGroup')
        imageGroup = prodDef.getImageGroup()
        if imageGroup:
            self.imageGroup.characters(imageGroup)

        self.baseFlavor = xmllib.StringNode(name = 'baseFlavor')
        self.baseFlavor.characters(prodDef.getBaseFlavor())

    def iterChildren(self):
        return [ self.imageGroup,
                 self.baseFlavor,
                 self.stages,
                 self.upstreamSources,
                 self.buildDefinition ]

class _ImageTypeFakeNode(object):
    """Internal class for emulating the interface expected by the node
    dispatcher for creating image types"""
    def __init__(self, name, fields = None):
        self.name = name
        self.fields = fields or {}

    def getAbsoluteName(self):
        """
        @return: the absolute node name
        @rtype: C{str}
        """
        return '{}%s' % self.name

    def getAttribute(self, name):
        """
        Get an attribute by name
        @param name: The attribute name
        @type name: C{str}
        @return: The attribute with the specified name, or C{None} if one
        could not be found.
        @rtype: C{str} or C{None}
        """
        return self.fields.get(name)
