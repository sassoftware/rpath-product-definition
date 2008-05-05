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

__all__ = [ 'ProductDefinition' ]

import StringIO

from rpath_common.xmllib import api1 as xmllib
from rpath_common.proddef import _xmlConstants
from rpath_common.proddef import _imageTypes

class ProductDefinition(object):
    """
    Represents the definition of a product.
    """
    version = '1.0'
    defaultNamespace = _xmlConstants.defaultNamespaceList[0]
    xmlSchemaNamespace = _xmlConstants.xmlSchemaNamespace
    xmlSchemaLocation = _xmlConstants.xmlSchemaLocation

    def __init__(self, fromStream = None):
        """
        Pass in either a dictionary as constructed in the example below, or an
        xml string to create an instance.
        """

        self._initFields()

        if fromStream:
            if isinstance(fromStream, (str, unicode)):
                fromStream = StringIO.StringIO(fromStream)
            self.parseStream(fromStream)

    def parseStream(self, stream):
        self._initFields()
        binder = xmllib.DataBinder()
        # We need to dynamically create a class here, so we can set the proper
        # namespace for the class
        binder.registerType(_ProductDefinition, 'productDefinition')
        xmlObj = binder.parseFile(stream)
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
        """Serialize the current object"""
        baseFlavor = xmllib.StringNode(name = 'baseFlavor')
        baseFlavor.characters(self.baseFlavor)
        class N(xmllib.BaseNode):
            def iterChildren(slf):
                return [ baseFlavor,
                         self.stages,
                         self.upstreamSources,
                         self.buildDefinition ]
        attrs = {'version' : self.version,
                 'xmlns' : self.defaultNamespace,
                 'xmlns:xsi' : self.xmlSchemaNamespace,
                 "xsi:schemaLocation" : self.xmlSchemaLocation,
        }
        nameSpaces = {}
        n = N(attrs, nameSpaces, name = "productDefinition")
        binder = xmllib.DataBinder()
        stream.write(binder.toXml(n))

    def getBaseFlavor(self):
        return self.baseFlavor

    def setBaseFlavor(self, baseFlavor):
        self.baseFlavor = baseFlavor

    def getStages(self):
        return self.stages

    def addStage(self, name = None, label = None):
        obj = _Stage(name = name, label = label)
        self.stages.append(obj)

    def getUpstreamSources(self):
        return self.upstreamSources

    def addUpstreamSource(self, troveName = None, label = None):
        obj = _UpstreamSource(troveName = troveName, label = label)
        self.upstreamSources.append(obj)

    def getBuildDefinitions(self):
        return self.buildDefinition

    def addBuildDefinition(self, name = None, baseFlavor = None,
                           byDefault = None, imageType = None):
        obj = _Build(name = name, baseFlavor = baseFlavor,
                               byDefault = byDefault, imageType = imageType)
        self.buildDefinition.append(obj)

    def _initFields(self):
        self.baseFlavor = None
        self.stages = _Stages()
        self.upstreamSources = _UpstreamSources()
        self.buildDefinition = _BuildDefinition()

    def _setFromDict(self):
        # Functions to call to set attributes on the root element.
        self._setNameSpace()
        self._setNameSpaceXsi()
        self._setXsiSchemaLocation()
        self._setVersion()

        self.setBaseFlavor(self.elementDict.pop('baseFlavor', ''))

        # Set each of our 3 possible list elements.
        self.setStages(self.elementDict.pop('stages', []))
        self.setUpstreamSources(self.elementDict.pop('upstreamSources', []))
        self.setBuildDefinition(self.elementDict.pop('buildDefinition', []))

        # Merge any remaining items in self.elementDict into the instance's
        # main dictionary, causing them to show up as elements.
        self.xmlobj.__dict__.update(self.elementDict)

    def _setNameSpace(self):
        setattr(self.xmlobj.__class__, 'xmlns',
                'http://www.rpath.com/permanent/rpd-1.0.xsd')

    def _setNameSpaceXsi(self):
        setattr(self.xmlobj.__class__, 'xmlns:xsi',
                'http://www.w3.org/2001/XMLSchema-instance')

    def _setXsiSchemaLocation(self):
        setattr(self.xmlobj.__class__, 'xsi:schemaLocation',
                'http://www.rpath.com/permanent/rpd-1.0.xsd rpd-1.0.xsd')

    def _setVersion(self):
        setattr(self.xmlobj.__class__, 'version', '1.0')

    def _setElemObj(self, elem, name, elementObject):
        """
        Creates an object with an attribute called name set to elementObject.
        Then, sets that object to an attribute called elem on self.xmlobj.

        This method is typically used in conjuction with self._genElemObj to
        set the returned list at the desired location.
        """
        Elem = type('Elem', (object,), {})
        e = Elem()
        setattr(e, name, elementObject)
        setattr(self.xmlobj, elem, [e])

#{ Objects for the representation of ProductDefinition fields

class _Stages(xmllib.SerializableList):
    tag = "stages"

class _UpstreamSources(xmllib.SerializableList):
    tag = "upstreamSources"

class _BuildDefinition(xmllib.SerializableList):
    tag = "buildDefinition"

class _Stage(xmllib.SlotBasedSerializableObject):
    __slots__ = [ 'name', 'label' ]
    tag = "stage"

    def __init__(self, name = None, label = None):
        self.name = name
        self.label = label

class _UpstreamSource(xmllib.SlotBasedSerializableObject):
    __slots__ = [ 'troveName', 'label' ]
    tag = "upstreamSource"

    def __init__(self, troveName = None, label = None):
        self.troveName = troveName
        self.label = label

class _Build(xmllib.SlotBasedSerializableObject):
    __slots__ = [ 'name', 'baseFlavor', 'imageType', 'byDefault' ]
    tag = "build"

    def __init__(self, name = None, baseFlavor = None,
                 imageType = None, byDefault = None):
        self.name = name
        self.baseFlavor = baseFlavor
        self.imageType = imageType
        if byDefault is None:
            byDefault = True
        self.byDefault = byDefault

    def _iterChildren(self):
        yield self.imageType

#}

class _ProductDefinition(xmllib.BaseNode):
    def __init__(self, attributes = None, nsMap = None, name = None):
        xmllib.BaseNode.__init__(self, attributes = attributes, nsMap = nsMap,
                                 name = name)
        self.defaultNamespace = self.getNamespaceMap().get(None)

    def addChild(self, childNode):
        chName = childNode.getAbsoluteName()
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
        dispatcher = _imageTypes.ImageType_Dispatcher(self._nsMap)
        dispatcher.registerClasses(_imageTypes, _imageTypes.ImageType_Base)

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
                raise Exception("")
            byDefault = node.getAttribute('byDefault')
            if byDefault is None:
                byDefault = True
            else:
                byDefault = xmllib.BooleanNode.fromString(byDefault)
            pyobj = _Build(
                baseFlavor = node.getAttribute('baseFlavor'),
                byDefault = byDefault,
                imageType = imgType)
            builds.append(pyobj)
