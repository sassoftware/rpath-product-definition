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
            'PlatformLabelMissingError'
            ]

import itertools
import StringIO

from conary import changelog
from conary import errors as conaryErrors
from conary import versions as conaryVersions
from conary.conaryclient import filetypes, cmdline
from conary.deps import deps as conaryDeps

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

class PlatformLabelMissingError(ProductDefinitionError):
    "Raised when the platform label is missing, and a rebase was requested"

#}

class BaseDefinition(object):
    version = '1.1'
    defaultNamespace = _xmlConstants.defaultNamespaceList[0]
    xmlSchemaLocation = _xmlConstants.xmlSchemaLocation

    schemaDir = "/usr/share/rpath_common"

    def __init__(self, fromStream = None, validate = False, schemaDir = None):
        """
        Initialize a ProductDefinition object, getting data from the optional
        XML stream.
        @param fromStream: An optional XML string or file
        @type fromStream: C{str} or C{file}
        @param validate: Validate before parsing (off by default)
        @type validate: C{bool}
        @param schemaDir: A directory where schema files are stored
        @type schemaDir: C{str}
        """

        self._initFields()

        if fromStream:
            if isinstance(fromStream, (str, unicode)):
                fromStream = StringIO.StringIO(fromStream)
            self.parseStream(fromStream, validate = validate,
                             schemaDir = schemaDir)

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

    def getSearchPaths(self):
        """
        @return: the search paths from this product definition
        @rtype: C{list} of C{_SearchPath} objects
        """
        return self.searchPaths

    def clearSearchPaths(self):
        """
        Delete all searchPaths.
        @return: None
        @rtype None
        """
        self.searchPaths = _SearchPaths()

    def getFactorySources(self):
        """
        @return: the factory sources from this product definition
        @rtype: C{list} of C{_FactorySource} objects
        """
        return self.factorySources

    def clearFactorySources(self):
        """
        Delete all factorySources.
        @return: None
        @rtype None
        """
        self.factorySources = _FactorySources()

    def addSearchPath(self, troveName = None, label = None, version = None):
        """
        Add an search path.
        @param troveName: the trove name for the search path.
        @type troveName: C{str} or C{None}
        @param label: Label for the search path
        @type label: C{str} or C{None}
        @param version: Version for the search path
        @param version: C{str} or C{None}
        """
        self._addSource(troveName, label, version, _SearchPath, self.searchPaths)

    def addFactorySource(self, troveName = None, label = None, version = None):
        """
        Add a factory source.
        @param troveName: the trove name for the factory source.
        @type troveName: C{str} or C{None}
        @param label: Label for the factory source
        @type label: C{str} or C{None}
        @param version: Version for the factory source
        @param version: C{str} or C{None}
        """
        self._addSource(troveName, label, version, _FactorySource, self.factorySources)

    def _addSource(self, troveName, label, version, cls, intList):
        "Internal function for adding a Source"
        if label is not None:
            if isinstance(label, conaryVersions.Label):
                label = str(label)
        obj = cls(troveName = troveName, label = label, version = version)
        intList.append(obj)


    def _saveToRepository(self, conaryClient, label, message = None):
        version = '1.1'

        if message is None:
            message = "Automatic checkin\n"

        recipe = self._recipe.replace('@NAME@', self._troveName)
        recipe = recipe.replace('@VERSION@', version)

        stream = StringIO.StringIO()
        self.serialize(stream)
        pathDict = {
            "%s.recipe" % self._troveName : filetypes.RegularFile(
                contents = recipe, config=True),
            self._troveFileName : filetypes.RegularFile(
                contents = stream.getvalue(), config=True),
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
        # At this point, troveSpec is in troves and its value should not be
        # the empty list.
        nvfs = troves[troveSpec]
        #if not nvfs:
        #    raise ProductDefinitionTroveNotFound("%s=%s" % (troveName, label))
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
            return fileContents[0].get(), thawTrvCs.getNewNameVersionFlavor()

        # Couldn't find the file we expected; die
        raise ProductDefinitionFileNotFound("%s=%s" % (troveName, label))

class ProductDefinition(BaseDefinition):
    """
    Represents the definition of a product.
    @cvar version:
    @type version: C{str}
    @cvar defaultNamespace:
    @type defaultNamespace: C{str}
    @cvar xmlSchemaLocation:
    @type xmlSchemaLocation: C{str}
    @cvar _imageTypeDispatcher: an object factory for imageType objects
    @type _imageTypeDispatcher: C{xmllib.NodeDispatcher}
    @cvar schemaDir: Directory where schema definitions are stored
    @type schemaDir: C{str}
    """
    _imageTypeDispatcher = xmllib.NodeDispatcher({})
    _imageTypeDispatcher.registerClasses(imageTypes, imageTypes.ImageType_Base)

    _troveName = 'product-definition'
    _troveFileName = 'product-definition.xml'

    _recipe = '''
#
# Copyright (c) 2008 rPath, Inc.
#

class ProductDefinitionRecipe(PackageRecipe):
    name = "@NAME@"
    version = "@VERSION@"

    def setup(r):
        """
        This recipe is a stub created to allow users to manually
        check in changes to the product definition XML.

        No other recipe actions need to be added beyond this point.
        """
'''

    def __str__(self):
        troveName = self.getTroveName()
        try:
            prodDefLabel = self.getProductDefinitionLabel()
        except MissingInformationError:
            # This is probably the best we can do. we don't want to backtrace
            # in this case.
            prodDefLabel = None
        return "<Product Definition: %s=%s>" % (troveName, prodDefLabel)

    def __eq__(self, obj):
        for key, val in self.__dict__.iteritems():
            val2 = obj.__getattribute__(key)
            if val != val2:
                return False
        return True

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def copy(self):
        outStr = StringIO.StringIO()
        self.serialize(outStr)
        inStr = StringIO.StringIO(outStr.getvalue())
        return ProductDefinition(inStr)

    def parseStream(self, stream, validate = False, schemaDir = None):
        """
        Initialize the current object from an XML stream.
        @param stream: An XML stream
        @type stream: C{file}
        @param validate: Validate before parsing (off by default)
        @type validate: C{bool}
        @param schemaDir: A directory where schema files are stored
        @type schemaDir: C{str}
        """
        self._initFields()
        binder = xmllib.DataBinder()
        binder.registerType(_ProductDefinition, 'productDefinition')
        xmlObj = binder.parseFile(stream, validate = validate,
                                  schemaDir = schemaDir or self.schemaDir)
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
        self.searchPaths.extend(getattr(xmlObj, 'searchPaths', []))
        self.factorySources.extend(getattr(xmlObj, 'factorySources', []))
        self.buildDefinition.extend(getattr(xmlObj, 'buildDefinition', []))
        self.platform = getattr(xmlObj, 'platform', None)

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
                 'xmlns:xsi' : xmllib.DataBinder.xmlSchemaNamespace,
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
        label = self.getProductDefinitionLabel()
        return self._saveToRepository(client, label, message = message)

    def loadFromRepository(self, client):
        """
        Load a C{ProductDefinition} object from a Conary repository.
        Prior to calling this method, the C{ProductDefinition} object should
        be initialized by calling C{setProductShortname},
        C{setProductVersion}, C{setConaryRepositoryHostname} and
        C{setConaryNamespace}.
        @param client: A Conary client object
        @type client: C{conaryclient.ConaryClient}
        @raises C{RepositoryError}:
        @raises C{ProductDefinitionTroveNotFound}:
        @raises C{ProductDefinitionFileNotFound}:
        """
        label = self.getProductDefinitionLabel()
        stream, nvf = self._getStreamFromRepository(client, label)
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
        flv = conaryDeps.parseFlavor('')
        if self.baseFlavor is not None:
            nflv = conaryDeps.parseFlavor(self.baseFlavor)
            flv.union(nflv)
        platFlv = self.getPlatformBaseFlavor()
        if platFlv is not None:
            nflv = conaryDeps.parseFlavor(platFlv)
            flv.union(nflv)
        return str(flv)

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

    def clearStages(self):
        """
        Delete all stages.
        @return: None
        @rtype None
        """
        self.stages = _Stages()

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

    def getSearchPaths(self):
        """
        @return: the search paths from this product definition
        @rtype: C{list} of C{_SearchPath} objects
        """
        if self.searchPaths:
            return self.searchPaths
        return self.getPlatformSearchPaths()

    def getFactorySources(self):
        """
        @return: the factory sources from this product definition
        @rtype: C{list} of C{_FactorySource} objects
        """
        if self.factorySources:
            return self.factorySources
        return self.getPlatformFactorySources()

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

    def clearBuildDefinition(self):
        """
        Delete all buildDefinition.
        @return: None
        @rtype None
        """
        self.buildDefinition = _BuildDefinition()

    def getPlatformSearchPaths(self):
        """
        @return: the search paths from this product definition
        @rtype: C{list} of C{_SearchPath} objects
        """
        if self.platform is None:
            return []
        return self.platform.searchPaths

    def clearPlatformSearchPaths(self):
        """
        Delete all searchPaths.
        @return: None
        @rtype None
        """
        if self.platform is None:
            return
        self.platform.searchPaths = _SearchPaths()

    def addPlatformSearchPath(self, troveName = None, label = None,
                              version = None):
        """
        Add an search path.
        @param troveName: the trove name for the search path.
        @type troveName: C{str} or C{None}
        @param label: Label for the search path
        @type label: C{str} or C{None}
        @param version: Version for the search path
        @param version: C{str} or C{None}
        """
        if self.platform is None:
            self.platform = PlatformDefinition()
        self._addSource(troveName, label, version, _SearchPath,
                        self.platform.searchPaths)

    def getPlatformFactorySources(self):
        """
        @return: the factory sources from this product definition
        @rtype: C{list} of C{_FactorySource} objects
        """
        if self.platform is None:
            return []
        return self.platform.factorySources

    def clearPlatformFactorySources(self):
        """
        Delete all factorySources.
        @return: None
        @rtype None
        """
        if self.platform is None:
            return
        self.platform.factorySources = _FactorySources()

    def addPlatformFactorySource(self, troveName = None, label = None,
                                 version = None):
        """
        Add a factory source.
        @param troveName: the trove name for the factory source.
        @type troveName: C{str} or C{None}
        @param label: Label for the factory source
        @type label: C{str} or C{None}
        @param version: Version for the factory source
        @param version: C{str} or C{None}
        """
        if self.platform is None:
            self.platform = PlatformDefinition()
        self._addSource(troveName, label, version, _FactorySource,
                        self.platform.factorySources)

    def getPlatformBaseFlavor(self):
        if self.platform is None:
            return None
        return self.platform.baseFlavor

    def setPlatformBaseFlavor(self, baseFlavor):
        self._ensurePlatformExists()
        self.platform.baseFlavor = baseFlavor

    def getPlatformSourceTrove(self):
        if self.platform is None:
            return None
        return self.platform.sourceTrove

    def setPlatformSourceTrove(self, sourceTrove):
        self._ensurePlatformExists()
        self.platform.sourceTrove = sourceTrove

    def getPlatformUseLatest(self):
        if self.platform is None:
            return None
        return self.platform.useLatest

    def setPlatformUseLatest(self, useLatest):
        self._ensurePlatformExists()
        self.platform.useLatest = useLatest

    def _ensurePlatformExists(self):
        if self.platform is None:
            self.platform = PlatformDefinition()

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

    def getProductDefinitionLabel(self):
        """
        Method that returns the product definition's label
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
        return str("%s@%s:%s-%s" % (hostname, namespace, shortname, version))

    @classmethod
    def getTroveName(cls):
        """
        @return: The name of the trove containing the product definition XML
        file.
        @rtype: C{str}
        """
        return cls._troveName

    #{ Internal methods
    def _getLabelForStage(self, stageObj):
        """
        Private method that works similarly to L{getLabelForStage},
        but works on a given C{_Stage} object.
        @return: a Conary label string where for the given stage object
        @rtype: C{str}
        @raises MissingInformationError: if there isn't enough information
            in the product definition to generate the label
        """
        prefix = self.getProductDefinitionLabel()
        labelSuffix = stageObj.labelSuffix or '' # this can be blank
        return str(prefix + labelSuffix)

    def toPlatformDefinition(self):
        "Create a PlatformDefinition object from this ProductDefinition"
        nplat = PlatformDefinition()
        baseFlavor = self.getBaseFlavor()
        nplat.setBaseFlavor(baseFlavor)

        # Factory sources defined in the product defintion take precedence
        fSources = self.getFactorySources()
        for fsrc in fSources or []:
            nplat.addFactorySource(troveName = fsrc.troveName,
                                   label = fsrc.label)

        # Build new search path
        label = self.getProductDefinitionLabel()
        sPathsList = []
        sPathsSet = set()

        # Iterate over all builds, and add the image group
        for build in self.buildDefinition:
            if not build.imageGroup:
                continue
            key = (build.imageGroup, label)
            if key not in sPathsSet:
                sPathsList.append(key)
                sPathsSet.add(key)
        # Append the global image group
        key = (self.getImageGroup(), label)
        if key not in sPathsSet:
            sPathsList.append(key)
            sPathsSet.add(key)
        # Now append the search paths from this object, if available, or from
        # the upstream platform, if available

        # We are purposely dropping the versions from the platform definition
        # on creation.

        sPaths = self.getSearchPaths()
        for sp in sPaths or []:
            key = (sp.troveName, sp.label)
            if key not in sPathsSet:
                sPathsList.append(key)
                sPathsSet.add(key)

        for troveName, label in sPathsList:
            nplat.addSearchPath(troveName=troveName, label=label)

        return nplat

    def savePlatformToRepository(self, client, message = None):
        nplat = self.toPlatformDefinition()
        label = self.getProductDefinitionLabel()
        nplat.saveToRepository(client, label, message = message)

    def rebase(self, client, label = None, useLatest = None):
        if label is None:
            troveSpec = self.getPlatformSourceTrove()
            if troveSpec:
                tn, tv, tf = cmdline.parseTroveSpec(troveSpec)
                label = tv
            else:
                label = None
        if label is None:
            raise PlatformLabelMissingError()
        nplat = self.toPlatformDefinition()
        nplat.loadFromRepository(client, label)
        nplat.snapshotVersions(client)
        self._rebase(label, nplat, useLatest = None)

    def _rebase(self, label, nplat, useLatest = None):
        # Create a new platform definition
        self.platform = PlatformDefinition()
        # Fill it in with fields from the upstream one
        self.setPlatformBaseFlavor(nplat.getBaseFlavor())
        self.setPlatformSourceTrove(nplat.sourceTrove)
        self.setPlatformUseLatest(useLatest)
        for sp in nplat.getSearchPaths():
            self.addPlatformSearchPath(troveName=sp.troveName,
                                       label=sp.label,
                                       version=sp.version)
        for sp in nplat.getFactorySources():
            self.addPlatformFactorySource(troveName=sp.troveName,
                                          label=sp.label,
                                          version=sp.version)

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
        self.searchPaths = _SearchPaths()
        self.factorySources = _FactorySources()
        self.buildDefinition = _BuildDefinition()
        self.platform = None

    #}


class PlatformDefinition(BaseDefinition):
    _troveName = 'platform-definition'
    _troveFileName = 'platform-definition.xml'

    _recipe = '''
#
# Copyright (c) 2008 rPath, Inc.
#

class PlatformDefinitionRecipe(PackageRecipe):
    name = "@NAME@"
    version = "@VERSION@"

    def setup(r):
        """
        This recipe is a stub created to allow users to manually
        check in changes to the product definition XML.

        No other recipe actions need to be added beyond this point.
        """
'''

    def _initFields(self):
        self.searchPaths = _SearchPaths()
        self.factorySources = _FactorySources()
        self.baseFlavor = None
        self.useLatest = None
        self.sourceTrove = None

    def parseStream(self, stream, validate = False, schemaDir = None):
        """
        Initialize the current object from an XML stream.
        @param stream: An XML stream
        @type stream: C{file}
        @param validate: Validate before parsing (off by default)
        @type validate: C{bool}
        @param schemaDir: A directory where schema files are stored
        @type schemaDir: C{str}
        """
        self._initFields()
        binder = xmllib.DataBinder()
        binder.registerType(_PlatformDefinition, 'platformDefinition')
        xmlObj = binder.parseFile(stream, validate = validate,
                                  schemaDir = schemaDir or self.schemaDir)
        self.baseFlavor = getattr(xmlObj.platform, 'baseFlavor', None)
        self.sourceTrove = getattr(xmlObj.platform, 'sourceTrove', None)
        self.useLatest = getattr(xmlObj.platform, 'useLatest', None)
        self.searchPaths = getattr(xmlObj.platform, 'searchPaths', None)
        self.factorySources = getattr(xmlObj.platform, 'factorySources', None)

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
                 'xmlns:xsi' : xmllib.DataBinder.xmlSchemaNamespace,
                 "xsi:schemaLocation" : self.xmlSchemaLocation,
        }
        nameSpaces = {}
        serObj = _PlatformSerialization(attrs, nameSpaces, self,
            name="platformDefinition")
        binder = xmllib.DataBinder()
        stream.write(binder.toXml(serObj))

    def saveToRepository(self, client, label, message = None):
        """
        Save a C{PlatformDefinition} object to a Conary repository.
        @param client: A Conary client object
        @type client: C{conaryclient.ConaryClient}
        @param message: An optional commit message
        @type message: C{str}
        @param label: Label where the representation will be saved
        @type label: C{str}
        """
        return self._saveToRepository(client, label, message = message)

    def loadFromRepository(self, client, label):
        """
        Load a C{PlatformDefinition} object from a Conary repository.
        @param client: A Conary client object
        @type client: C{conaryclient.ConaryClient}
        @raises C{RepositoryError}:
        @raises C{ProductDefinitionTroveNotFound}:
        @raises C{ProductDefinitionFileNotFound}:
        """
        stream, nvf = self._getStreamFromRepository(client, label)
        stream.seek(0)
        self.parseStream(stream)
        # Set the source trove version we used
        self.sourceTrove = "%s=%s" % (self._troveName, nvf[1])

    def snapshotVersions(self, conaryClient):
        """
        For each search path or factory source from this platform definition,
        query the repositories for the latest versions and record them.
        @param conaryClient: A Conary client object
        @type conaryClient: C{conaryclient.ConaryClient}
        """
        repos = conaryClient.getRepos()
        troveSpecs = set()
        # XXX We are ignoring the flavors for now.
        for sp in itertools.chain(self.getSearchPaths(),
                                  self.getFactorySources()):
            key = (sp.troveName, sp.label, None)
            troveSpecs.add(key)
        troveSpecs = sorted(troveSpecs)
        try:
            troves = repos.findTroves(None, troveSpecs, allowMissing = True)
        except conaryErrors.RepositoryError, e:
            raise RepositoryError(str(e))

        for sp in itertools.chain(self.getSearchPaths(),
                                  self.getFactorySources()):
            key = (sp.troveName, sp.label, None)
            if key not in troves:
                raise ProductDefinitionTroveNotFound("%s=%s" % (key[0], key[1]))
            nvf = troves[key][0]
            sp.version = str(nvf[1].trailingRevision())

#{ Objects for the representation of ProductDefinition fields

class _Stages(xmllib.SerializableList):
    tag = "stages"

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _SearchPaths(xmllib.SerializableList):
    tag = "searchPaths"

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

class _SearchPath(xmllib.SlotBasedSerializableObject):
    __slots__ = [ 'troveName', 'label', 'version' ]
    tag = "searchPath"

    def __init__(self, troveName = None, label = None, version = None):
        xmllib.SlotBasedSerializableObject.__init__(self)
        self.troveName = troveName
        self.label = label
        self.version = version

class _FactorySource(_SearchPath):
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

    def __eq__(self, build):
        for key in self.__slots__:
            if self.__getattribute__(key) != build.__getattribute__(key):
                return False
        return True

    def __ne__(self, build):
        return not self.__eq__(build)

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

class BaseXmlNode(xmllib.BaseNode):
    def __init__(self, attributes = None, nsMap = None, name = None):
        xmllib.BaseNode.__init__(self, attributes = attributes, nsMap = nsMap,
                                 name = name)
        self.defaultNamespace = self.getNamespaceMap().get(None)

    def _makeAbsoluteName(self, name):
        return "{%s}%s" % (self.defaultNamespace, name)

    def _processSearchPaths(self, searchPaths):
        sources = _SearchPaths()
        for node in searchPaths:
            pyObj = _SearchPath(
                troveName = node.getAttribute('troveName'),
                label = node.getAttribute('label'),
                version = node.getAttribute('version'))
            sources.append(pyObj)
        return sources

    def _processFactorySources(self, factorySources):
        sources = _FactorySources()
        for node in factorySources:
            pyObj = _FactorySource(
                troveName = node.getAttribute('troveName'),
                label = node.getAttribute('label'),
                version = node.getAttribute('version'))
            sources.append(pyObj)
        return sources

    def _addPlatform(self, node):
        self.platform = PlatformDefinition()
        self.platform.sourceTrove = node.getAttribute('sourceTrove')
        useLatest = node.getAttribute('useLatest')
        if useLatest is not None:
            useLatest = xmllib.BooleanNode.fromString(useLatest)
        self.platform.useLatest = useLatest
        listNode = node.getChildren('searchPaths')
        if listNode:
            self.platform.searchPaths = self._processSearchPaths(
                listNode[0].getChildren('searchPath'))
        listNode = node.getChildren('factorySources')
        if listNode:
            self.platform.factorySources = self._processFactorySources(
                listNode[0].getChildren('factorySource'))
        baseFlavorChildren = node.getChildren('baseFlavor')
        if baseFlavorChildren:
            self.platform.baseFlavor = baseFlavorChildren[0].getText()


class _ProductDefinition(BaseXmlNode):

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

        if chName == self._makeAbsoluteName('searchPaths'):
            children = childNode.getChildren('searchPath')
            self._addSearchPaths(children)
            return

        if chName == self._makeAbsoluteName('factorySources'):
            children = childNode.getChildren('factorySource')
            self._addFactorySources(children)
            return

        if chName == self._makeAbsoluteName('buildDefinition'):
            children = childNode.getChildren('build')
            self._addBuildDefinition(children)
            return

        if chName == self._makeAbsoluteName('platform'):
            self._addPlatform(childNode)
            return

    def _addStages(self, stagesNodes):
        stages = self.stages = _Stages()
        for node in stagesNodes:
            # XXX getAttribute should be getAbsoluteAttribute
            pyObj = _Stage(name = node.getAttribute('name'),
                           labelSuffix = node.getAttribute('labelSuffix'))
            stages.append(pyObj)

    def _addSearchPaths(self, searchPaths):
        self.searchPaths = self._processSearchPaths(searchPaths)

    def _addFactorySources(self, factorySources):
        self.factorySources = self._processFactorySources(factorySources)

    def _addBuildDefinition(self, buildNodes):
        dispatcher = xmllib.NodeDispatcher(self._nsMap)
        dispatcher.registerClasses(imageTypes, imageTypes.ImageType_Base)

        builds = self.buildDefinition = _BuildDefinition()
        for node in buildNodes:
            imgType = None
            subNode = None
            for subNode in node.iterChildren():
                if not isinstance(subNode, xmllib.BaseNode):
                    continue
                imgType = dispatcher.dispatch(subNode)
                if imgType is not None:
                    break
            if subNode is None:
                # Build node had no children
                continue
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

class _PlatformDefinition(BaseXmlNode):
    def finalize(self):
        self._addPlatform(self)
        return self

class _PlatformSerialization(xmllib.BaseNode):
    def __init__(self, attrs, namespaces, platform, name='platform'):
        # Some attributes don't make sense for a productDefinition node
        if name == 'platform':
            if platform.useLatest:
                attrs['useLatest'] = True
            if platform.sourceTrove:
                attrs['sourceTrove'] = platform.sourceTrove
        self.searchPaths = platform.searchPaths
        self.factorySources = platform.factorySources
        self.baseFlavor = xmllib.StringNode(name = 'baseFlavor').characters(platform.baseFlavor)
        xmllib.BaseNode.__init__(self, attrs, namespaces, name=name)

    def iterChildren(self):
        ret = [self.baseFlavor]
        if self.searchPaths:
            ret.append(self.searchPaths)
        if self.factorySources:
            ret.append(self.factorySources)
        return ret

class _ProductDefinitionSerialization(xmllib.BaseNode):
    def __init__(self, name, attrs, namespaces, prodDef):
        xmllib.BaseNode.__init__(self, attrs, namespaces, name = name)
        self.stages = prodDef.getStages()
        self.searchPaths = prodDef.searchPaths
        self.factorySources = prodDef.factorySources
        self.buildDefinition = prodDef.getBuildDefinitions()
        if prodDef.platform:
            self.platform = _PlatformSerialization({}, namespaces,
                prodDef.platform)
        else:
            self.platform = None

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
        self.baseFlavor.characters(prodDef.baseFlavor)

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
                 self.searchPaths, ]
        if len(self.factorySources):
            ret.append(self.factorySources)
        ret.append(self.buildDefinition)
        if self.platform:
            ret.append(self.platform)
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
