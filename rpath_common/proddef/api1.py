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
    defaultNamespace = _xmlConstants.defaultNamespace
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
        binder = xmllib.DataBinder()
        binder.registerType(_ProductDefinition, 'productDefinition')
        xmlObj = binder.parseFile(stream)
        self.baseFlavor = getattr(xmlObj, 'baseFlavor', None)
        self.stages = getattr(xmlObj, 'stages', [])
        self.upstreamSources = getattr(xmlObj, 'upstreamSources', [])
        self.buildDefinition = getattr(xmlObj, 'buildDefinition', [])

    def _initFields(self):
        self.baseFlavor = None
        self.stages = []
        self.upstreamSources = []
        self.buildDefinition = []

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
                'http://www.rpath.com/permanent/pd.xsd')

    def _setNameSpaceXsi(self):
        setattr(self.xmlobj.__class__, 'xmlns:xsi',
                'http://www.w3.org/2001/XMLSchema-instance')

    def _setXsiSchemaLocation(self):
        setattr(self.xmlobj.__class__, 'xsi:schemaLocation',
                'http://www.rpath.com/permanent/pd.xsd pd.xsd')

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

    @staticmethod
    def _genElemObj(elementList):        
        """
        Create an object (using the cls helper function) that has elements set
        as attributes and xml attributes set as class attributes for each item
        in elementList.  Returns the list of objects.
        """
        elementObjList = []

        # For each item in that list, we expect a dict representing the
        # attributes (or possible more child elements).
        for element in elementList:
            # Append an object created from the element dict to elementObjList.
            elementObjList.append(cls(**element))

        return elementObjList

    def toXml(self):
        return self.xmldb.toXml(self.xmlobj, 'productDefinition')

    def setXmlObj(self, xmlobj):
        self.xmlobj = xmlobj

    def setStages(self, stages):
        elementObject = self._genElemObj(stages)
        self._setElemObj('stages', 'stage', elementObject)

    def getStages(self): 
        stages = []
        for stage in getattr(self.xmlobj.stages[0], 'stage', []):
            stages.append(dict(name=stage.name, label=stage.label))
        return stages

    def setUpstreamSources(self, sources):
        elementObject = self._genElemObj(sources)
        self._setElemObj('upstreamSources', 'upstreamSource', elementObject)

    def getUpstreamSources(self):
        upstreamSources = []
        for source in getattr(self.xmlobj.upstreamSources[0],
                'upstreamSource', []):
            upstreamSources.append(dict(troveName=source.troveName,
                                        label=source.label))
        return upstreamSources

    def setBaseFlavor(self, baseFlavor):
        self.xmlobj.baseFlavor = [baseFlavor]

    def getBaseFlavor(self):
        return self.xmlobj.baseFlavor[0]

    def setBuildDefinition(self, builddef):
        elementObject = self._genElemObj(builddef)
        self._setElemObj('buildDefinition', 'build', elementObject)

    def getBuildDefinition(self):
        builds = []
        for build in getattr(self.xmlobj.buildDefinition[0], 'build', []):
            buildData = {}
            for key in dir(build):
                if key.startswith('_'):
                    continue
                value = getattr(build, key)
                if type(value) == type([]):
                    buildDataValue = {}
                    for k in dir(value[0]):
                        if k.startswith('_'):
                            continue
                        else:
                            buildDataValue[k] = getattr(value[0], k)
                    buildData[key] = buildDataValue
                else:
                    buildData[key] = value

            builds.append(buildData)                    

        return builds                               

#{ Objects for the representation of ProductDefinition fields
class _Stage(object):
    __slots__ = [ 'name', 'label' ]

    def __init__(self, name = None, label = None):
        self.name = name
        self.label = label

class _UpstreamSource(object):
    __slots__ = [ 'troveName', 'label' ]

    def __init__(self, troveName = None, label = None):
        self.troveName = troveName
        self.label = label

class _BuildDefinition(object):
    __slots__ = [ 'name', 'baseFlavor', 'imageType', 'byDefault' ]

    def __init__(self, name = None, baseFlavor = None,
                 imageType = None, byDefault = None):
        self.name = name
        self.baseFlavor = baseFlavor
        self.imageType = imageType
        if byDefault is None:
            byDefault = True
        self.byDefault = byDefault

#}

class _ProductDefinition(xmllib.BaseNode):
    ndNameBaseFlavor = "{%s}%s" % (ProductDefinition.defaultNamespace,
                                   'baseFlavor')
    ndNameStages = "{%s}%s" % (ProductDefinition.defaultNamespace,
                               'stages')
    ndNameUpstreamSources = "{%s}%s" % (ProductDefinition.defaultNamespace,
                                        'upstreamSources')
    ndNameBuildDefinition = "{%s}%s" % (ProductDefinition.defaultNamespace,
                                        'buildDefinition')

    ndNameInstIso = "{%s}%s" % (ProductDefinition.defaultNamespace,
                                'installbleIsoImage')

    ndNameRawFs = "{%s}%s" % (ProductDefinition.defaultNamespace,
                             'rawFsImage')
    ndNameRawHd = "{%s}%s" % (ProductDefinition.defaultNamespace,
                             'rawHdImage')


    def addChild(self, childNode):
        chName = childNode.getAbsoluteName()
        if chName == self.ndNameBaseFlavor:
            self.baseFlavor = childNode.getText()
            return

        if chName == self.ndNameStages:
            children = childNode.getChildren('stage')
            self._addStages(children)
            return

        if chName == self.ndNameUpstreamSources:
            children = childNode.getChildren('upstreamSource')
            self._addUpstreamSources(children)
            return

        if chName == self.ndNameBuildDefinition:
            children = childNode.getChildren('build')
            self._addBuildDefinition(children)
            return

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
        builds = self.buildDefinition = []
        for node in buildNodes:
            imgType = None
            for subNode in node.iterChildren():
                if not isinstance(subNode, xmllib.BaseNode):
                    continue
                imgType = _imageTypes.ImageType_Dispatcher.dispatch(subNode)
                if imgType is not None:
                    break
            if imgType is None:
                raise Exception("")
            byDefault = node.getAttribute('byDefault')
            if byDefault is None:
                byDefault = True
            else:
                byDefault = byDefault.upper() in ['TRUE', 1] and True or False
            pyobj = _BuildDefinition(
                baseFlavor = node.getAttribute('baseFlavor'),
                byDefault = byDefault,
                imageType = imgType)
            builds.append(pyobj)
