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

__all__ = [ 'MissingInformationError',
            'ProductDefinition',
            'ProductDefinitionError',
            'StageNotFoundError',
            'UnsupportedImageType',
            'ProductDefinitionTroveNotFound',
            'ProductDefinitionFileNotFound',
            'RepositoryError',
            ]

import StringIO

from conary import changelog
from conary import errors as conaryErrors
from conary import versions as conaryVersions
from conary.conaryclient import filetypes

from rpath_common.xmllib import api1 as xmllib
from rpath_common.proddef import _xmlConstants
from rpath_common.proddef import imageTypes

#{ Exception classes
class ProductDefinitionError(Exception):
    "Base class for product definition exceptions"

class MissingInformationError(ProductDefinitionError):
    """
    Raised when attempting to synthesize a label when there isn't enough
    information to generate it.
    """

class StageNotFoundError(ProductDefinitionError):
    " Raised when no such stage exists. "

class UnsupportedImageType(ProductDefinitionError):
    "Raised when an unsupported image type was passed"

class ProductDefinitionTroveNotFound(ProductDefinitionError):
    """
    Raised when the trove containing the product definition file could not
    be found in the repository
    """

class ProductDefinitionFileNotFound(ProductDefinitionError):
    "Raised when the product definition file was not found in the repository"

class RepositoryError(ProductDefinitionError):
    "Generic error raised when a repository error was caught"

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

    _troveName = 'product-definition'
    _troveFileName = 'product-definition.xml'

    _recipe = """
#
# Copyright (c) 2008 rPath, Inc.
#

class Recipe_@NAME@(PackageRecipe):
    name = "@NAME@"
    version = "@VERSION@"

    def setup(r):
        pass
"""

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
        self.productName = getattr(xmlObj, 'productName', None)
        self.productDescription = getattr(xmlObj, 'productDescription', None)
        self.productShortname = getattr(xmlObj, 'productShortname', None)
        self.productVersion = getattr(xmlObj, 'productVersion', None)
        self.productVersionDescription = getattr(xmlObj,
            'productVersionDescription', None)
        self.conaryRepositoryHostname = getattr(xmlObj,
            'conaryRepositoryHostname', None)
        self.conaryNamespace = getattr(xmlObj, 'conaryNamespace', None)
        self.imageGroup = getattr(xmlObj, 'imageGroup', None)
        self.baseFlavor = getattr(xmlObj, 'baseFlavor', None)
        self.stages.extend(getattr(xmlObj, 'stages', []))
        self.upstreamSources.extend(getattr(xmlObj, 'upstreamSources', []))
        self.factorySources.extend(getattr(xmlObj, 'factorySources', []))
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

    def saveToRepository(self, client, message = None):
        """
        Save a C{ProductDefinition} object to a Conary repository.
        @param client: A Conary client object
        @type client: C{conaryclient.ConaryClient}
        @param message: An optional commit message
        @type message: C{str}
        """
        label = self._getProductDefinitionLabel()
        return self._saveToRepository(client, label, message = message)

    def loadFromRepository(self, client):
        """
        Load a C{ProductDefinition} object to a Conary repository.
        Prior to calling this method, the C{ProductDefinition} object should
        be initialized by calling C{setProductShortname},
        C{setProductVersion}, C{setConaryRepositoryHostname} and
        C{setConaryNamespace}.
        @param client: A Conary client object
        @type client: C{conaryclient.ConaryClient}
        @param message: An optional commit message
        @type message: C{str}
        @raises C{RepositoryError}:
        @raises C{ProductDefinitionTroveNotFound}:
        @raises C{ProductDefinitionFileNotFound}:
        """
        label = self._getProductDefinitionLabel()
        stream = self._getStreamFromRepository(client, label)
        stream.seek(0)
        self.parseStream(stream)

    def getProductName(self):
        """
        @return: the product name
        @rtype: C{str}
        """
        return self.productName

    def setProductName(self, productName):
        """
        Set the product name
        @param productName: the product name
        @type productName: C{str}
        """
        self.productName = productName

    def getProductDescription(self):
        """
        @return: the product description
        @rtype: C{str}
        """
        return self.productDescription

    def setProductDescription(self, productDescription):
        """
        Set the product description
        @param productDescription: the product description
        @type productDescription: C{str}
        """
        self.productDescription = productDescription

    def getProductShortname(self):
        """
        @return: the product shortname
        @rtype: C{str}
        """
        return self.productShortname

    def setProductShortname(self, productShortname):
        """
        @param productShortname: the product's shortname
        @type productShortname: C{str}
        """
        self.productShortname = productShortname

    def getProductVersion(self):
        """
        @return: the product version
        @rtype: C{str}
        """
        return self.productVersion

    def setProductVersion(self, productVersion):
        """
        Set the product version
        @param productVersion: the product version
        @type productVersion: C{str}
        """
        self.productVersion = productVersion

    def getProductVersionDescription(self):
        """
        @return: the product version description
        @rtype: C{str}
        """
        return self.productVersionDescription

    def setProductVersionDescription(self, productVersionDescription):
        """
        Set the product version description
        @param productVersionDescription: the product version description
        @type productVersionDescription: C{str}
        """
        self.productVersionDescription = productVersionDescription

    def getConaryRepositoryHostname(self):
        """
        @return: the Conary repository's hostname (e.g. conary.example.com)
        @rtype: C{str}
        """
        return self.conaryRepositoryHostname

    def setConaryRepositoryHostname(self, conaryRepositoryHostname):
        """
        Set the Conary repository hostname
        @param conaryRepositoryHostname: the fully-qualified hostname for
           the repository
        @type conaryRepositoryHostname: C{str}
        """
        self.conaryRepositoryHostname = conaryRepositoryHostname

    def getConaryNamespace(self):
        """
        @return: the Conary namespace to use for this product
        @rtype: C{str}
        """
        return self.conaryNamespace

    def setConaryNamespace(self, conaryNamespace):
        """
        Set the Conary namespace
        @param conaryNamespace: the Conary namespace
        @type conaryNamespace: C{str}
        """
        self.conaryNamespace = conaryNamespace

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

    def getStage(self, stageName):
        """
        Returns a C{_Stage} object for the given stageName.
        @return: the C{_Stage} object for stageName
        @rtype: C{_Stage} or C{None} if not found
        @raises StageNotFoundError: if no such stage exists
        """
        ret = None
        stages = self.getStages()
        for stage in stages:
            if stage.name == stageName:
                return stage
        raise StageNotFoundError

    def addStage(self, name = None, labelSuffix = None):
        """
        Add a stage.
        @param name: the stage's name
        @type name: C{str} or C{None}
        @param labelSuffix: Label suffix (e.g. '-devel') for the stage
        @type labelSuffix: C{str} or C{None}
        """
        obj = _Stage(name = name, labelSuffix = labelSuffix)
        self.stages.append(obj)

    def getUpstreamSources(self):
        """
        @return: the upstream sources from this product definition
        @rtype: C{list} of C{_UpstreamSource} objects
        """
        return self.upstreamSources

    def getFactorySources(self):
        """
        @return: the factory sources from this product definition
        @rtype: C{list} of C{_FactorySource} objects
        """
        return self.factorySources


    def getLabelForStage(self, stageName):
        """
        Synthesize the label for a particular stage based upon
        the existing product information. Raises an exception
        if there isn't enough information in the product definition
        object to create the label.
        @return: a Conary label string where for the given stage
        @rtype: C{str}
        @raises StageNotFoundError: if no such stage exists
        @raises MissingInformationError: if there isn't enough information
            in the product definition to generate the label
        """
        return self._getLabelForStage(self.getStage(stageName))

    def getDefaultLabel(self):
        """
        Return the default label for commits.
        @return: a label string representing the default label for this
            product definition
        @rtype: C{str}
        @raises StageNotFoundError: if no such stage exists
        @raises MissingInformationError: if there isn't enough information
            in the object to generate the default label
        """
        # TODO: Currently, this is the development stage's label,
        #       i.e. the one with suffix '-devel'.
        #
        #       Eventually the XML schema will explicitly define the
        #       default label, either via a 'default' attribute on
        #       the stage or via the stage's order.
        ret = None
        stages = self.getStages()
        for stage in stages:
            if stage.labelSuffix == '-devel':
                return self._getLabelForStage(stage)
        raise StageNotFoundError

    def addUpstreamSource(self, troveName = None, label = None):
        """
        Add an upstream source.
        @param troveName: the trove name for the upstream source.
        @type name: C{str} or C{None}
        @param label: Label for the upstream source
        @type label: C{str} or C{None}
        """
        self._addSource(troveName, label, _UpstreamSource, self.upstreamSources)

    def addFactorySource(self, troveName = None, label = None):
        """
        Add a factory source.
        @param troveName: the trove name for the factory source.
        @type name: C{str} or C{None}
        @param label: Label for the factory source
        @type label: C{str} or C{None}
        """
        self._addSource(troveName, label, _FactorySource, self.factorySources)

    def _addSource(self, troveName, label, cls, intList):
        "Internal function for adding a Source"
        if label is not None:
            if isinstance(label, conaryVersions.Label):
                label = str(label)
        obj = cls(troveName = troveName, label = label)
        intList.append(obj)

    def getBuildDefinitions(self):
        """
        @return: The build definitions from this product definition
        @rtype: C{list} of C{Build} objects
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
        obj = Build(name = name, baseFlavor = baseFlavor,
                     imageType = imageType, stages = stages,
                     imageGroup = imageGroup,
                     parentImageGroup = self.imageGroup)
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
        @rtype: C{list} of C{Build} objects
        """
        ret = []
        for build in self.getBuildDefinitions():
            if stageName in build.stages:
                ret.append(build)
        return ret

    #{ Internal methods
    def _getProductDefinitionLabel(self):
        """
        Private method that returns the product definition's label
        @return: a Conary label string
        @rtype: C{str}
        @raises MissingInformationError: if there isn't enough information
            in the product definition to generate the label
        """
        hostname = self.getConaryRepositoryHostname()
        shortname = self.getProductShortname()
        namespace = self.getConaryNamespace()
        version = self.getProductVersion()

        if not (hostname and shortname and namespace and version):
            raise MissingInformationError
        return "%s@%s:%s-%s" % (hostname, namespace, shortname, version)

    def _getLabelForStage(self, stageObj):
        """
        Private method that works similarly to L{getLabelForStage},
        but works on a given C{_Stage} object.
        @return: a Conary label string where for the given stage object
        @rtype: C{str}
        @raises MissingInformationError: if there isn't enough information
            in the product definition to generate the label
        """
        prefix = self._getProductDefinitionLabel()
        labelSuffix = stageObj.labelSuffix or '' # this can be blank
        return prefix + labelSuffix

    def _initFields(self):
        self.baseFlavor = None
        self.stages = _Stages()
        self.productName = None
        self.productShortname = None
        self.productDescription = None
        self.productVersion = None
        self.productVersionDescription = None
        self.conaryRepositoryHostname = None
        self.conaryNamespace = None
        self.imageGroup = None
        self.upstreamSources = _UpstreamSources()
        self.factorySources = _FactorySources()
        self.buildDefinition = _BuildDefinition()

    def _saveToRepository(self, conaryClient, label, message = None):
        version = '0.1'

        if message is None:
            message = "Automatic checkin\n"

        recipe = self._recipe.replace('@NAME@', self._troveName)
        recipe = recipe.replace('@VERSION@', version)

        stream = StringIO.StringIO()
        self.serialize(stream)
        pathDict = {
            "%s.recipe" % self._troveName : filetypes.RegularFile(
                contents = self._recipe),
            self._troveFileName : filetypes.RegularFile(
                contents = stream.getvalue()),
        }
        cLog = changelog.ChangeLog(name = conaryClient.cfg.name,
                                   contact = conaryClient.cfg.contact,
                                   message = message)
        troveName = '%s:source' % self._troveName
        cs = conaryClient.createSourceTrove(troveName, label, version,
            pathDict, cLog)

        repos = conaryClient.getRepos()
        repos.commitChangeSet(cs)

    def _getStreamFromRepository(self, conaryClient, label):
        repos = conaryClient.getRepos()
        troveName = '%s:source' % self._troveName
        troveSpec = (troveName, label, None)
        try:
            troves = repos.findTroves(None, [ troveSpec ])
        except conaryErrors.TroveNotFound:
            raise ProductDefinitionTroveNotFound("%s=%s" % (troveName, label))
        except conaryErrors.RepositoryError, e:
            raise RepositoryError(str(e))
        nvfs = troves[troveSpec]
        if not nvfs:
            raise ProductDefinitionTroveNotFound("%s=%s" % (troveName, label))
        trvCsSpec = (nvfs[0][0], (None, None), (nvfs[0][1], nvfs[0][2]), True)
        cs = conaryClient.createChangeSet([ trvCsSpec ], withFiles = True,
                                          withFileContents = True)
        for thawTrvCs in cs.iterNewTroveList():
            paths = [ x for x in thawTrvCs.getNewFileList()
                      if x[1] == self._troveFileName ]
            if not paths:
                continue
            # Fetch file from changeset
            fileSpecs = [ (fId, fVer) for (_, _, fId, fVer) in paths ]
            fileContents = repos.getFileContents(fileSpecs)
            return fileContents[0].get()

        # Couldn't find the file we expected; die
        raise ProductDefinitionFileNotFound("%s=%s" % (troveName, label))
    #}


#{ Objects for the representation of ProductDefinition fields

class _Stages(xmllib.SerializableList):
    tag = "stages"

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _UpstreamSources(xmllib.SerializableList):
    tag = "upstreamSources"

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _FactorySources(xmllib.SerializableList):
    tag = "factorySources"


# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _BuildDefinition(xmllib.SerializableList):
    tag = "buildDefinition"

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _Stage(xmllib.SlotBasedSerializableObject):
    __slots__ = [ 'name', 'labelSuffix' ]
    tag = "stage"

    def __init__(self, name = None, labelSuffix = None):
        xmllib.SlotBasedSerializableObject.__init__(self)
        self.name = name
        self.labelSuffix = labelSuffix

class _UpstreamSource(xmllib.SlotBasedSerializableObject):
    __slots__ = [ 'troveName', 'label' ]
    tag = "upstreamSource"

    def __init__(self, troveName = None, label = None):
        xmllib.SlotBasedSerializableObject.__init__(self)
        self.troveName = troveName
        self.label = label

class _FactorySource(_UpstreamSource):
    tag = "factorySource"

class Build(xmllib.SerializableObject):
    __slots__ = [ 'name', 'baseFlavor', 'imageType', 'stages', 'imageGroup',
                  'parentImageGroup', ]
    tag = "build"

    def __init__(self, name = None, baseFlavor = None,
                 imageType = None, stages = None, imageGroup = None,
                 parentImageGroup = None):
        xmllib.SlotBasedSerializableObject.__init__(self)
        self.name = name
        self.baseFlavor = baseFlavor
        self.imageType = imageType
        self.stages = stages or []
        self.imageGroup = imageGroup
        self.parentImageGroup = parentImageGroup

    def getBuildImageGroup(self):
        if self.imageGroup is None:
            return self.parentImageGroup
        return self.imageGroup

    def getBuildImageType(self):
        return self.imageType

    def getBuildStages(self):
        return list(self.stages)

    def getBuildName(self):
        return self.name

    def getBuildBaseFlavor(self):
        return self.baseFlavor

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

        if chName == self._makeAbsoluteName('productName'):
            self.productName = childNode.getText()
            return

        if chName == self._makeAbsoluteName('productShortname'):
            self.productShortname = childNode.getText()
            return

        if chName == self._makeAbsoluteName('productDescription'):
            self.productDescription = childNode.getText()
            return

        if chName == self._makeAbsoluteName('productVersion'):
            self.productVersion = childNode.getText()
            return

        if chName == self._makeAbsoluteName('productVersionDescription'):
            self.productVersionDescription = childNode.getText()
            return

        if chName == self._makeAbsoluteName('conaryRepositoryHostname'):
            self.conaryRepositoryHostname = childNode.getText()
            return

        if chName == self._makeAbsoluteName('conaryNamespace'):
            self.conaryNamespace = childNode.getText()
            return

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

        if chName == self._makeAbsoluteName('factorySources'):
            children = childNode.getChildren('factorySource')
            self._addFactorySources(children)
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
                           labelSuffix = node.getAttribute('labelSuffix'))
            stages.append(pyObj)

    def _addUpstreamSources(self, upstreamSources):
        sources = self.upstreamSources = []
        for node in upstreamSources:
            pyObj = _UpstreamSource(
                troveName = node.getAttribute('troveName'),
                label = node.getAttribute('label'))
            sources.append(pyObj)

    def _addFactorySources(self, factorySources):
        sources = self.factorySources = []
        for node in factorySources:
            pyObj = _FactorySource(
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
            pyobj = Build(
                name = node.getAttribute('name'),
                baseFlavor = node.getAttribute('baseFlavor'),
                imageType = imgType,
                stages = [ x.getAttribute('ref')
                           for x in node.getChildren('stage') ],
                imageGroup = imageGroup,
                parentImageGroup = self.imageGroup,
                )
            builds.append(pyobj)

class _ProductDefinitionSerialization(xmllib.BaseNode):
    def __init__(self, name, attrs, namespaces, prodDef):
        xmllib.BaseNode.__init__(self, attrs, namespaces, name = name)
        self.stages = prodDef.getStages()
        self.upstreamSources = prodDef.getUpstreamSources()
        self.factorySources = prodDef.getFactorySources()
        self.buildDefinition = prodDef.getBuildDefinitions()

        self.productName = xmllib.StringNode(name = 'productName')
        productName = prodDef.getProductName()
        if productName:
            self.productName.characters(productName)

        self.productShortname = \
                xmllib.StringNode(name = 'productShortname')
        productShortname = prodDef.getProductShortname()
        if productShortname:
            self.productShortname.characters(productShortname)

        self.productDescription = \
                xmllib.StringNode(name = 'productDescription')
        productDescription = prodDef.getProductDescription()
        if productDescription:
            self.productDescription.characters(productDescription)

        self.productVersion = \
                xmllib.StringNode(name = 'productVersion')
        productVersion  = prodDef.getProductVersion()
        if productVersion:
            self.productVersion.characters(productVersion)

        self.productVersionDescription = \
                xmllib.StringNode(name = 'productVersionDescription')
        productVersionDescription = prodDef.getProductVersionDescription()
        if productVersionDescription:
            self.productVersionDescription.characters(productVersionDescription)

        self.conaryRepositoryHostname = \
                xmllib.StringNode(name = 'conaryRepositoryHostname')
        conaryRepositoryHostname = prodDef.getConaryRepositoryHostname()
        if conaryRepositoryHostname:
            self.conaryRepositoryHostname.characters(conaryRepositoryHostname)

        self.conaryNamespace = xmllib.StringNode(name = 'conaryNamespace')
        conaryNamespace = prodDef.getConaryNamespace()
        if conaryNamespace:
            self.conaryNamespace.characters(conaryNamespace)

        self.imageGroup = xmllib.StringNode(name = 'imageGroup')
        imageGroup = prodDef.getImageGroup()
        if imageGroup:
            self.imageGroup.characters(imageGroup)

        self.baseFlavor = xmllib.StringNode(name = 'baseFlavor')
        self.baseFlavor.characters(prodDef.getBaseFlavor())

    def iterChildren(self):
        ret =  [ self.productName,
                 self.productShortname,
                 self.productDescription,
                 self.productVersion,
                 self.productVersionDescription,
                 self.conaryRepositoryHostname,
                 self.conaryNamespace,
                 self.imageGroup,
                 self.baseFlavor,
                 self.stages,
                 self.upstreamSources, ]
        if len(self.factorySources):
            ret.append(self.factorySources)
        ret.append(self.buildDefinition)
        return ret

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
