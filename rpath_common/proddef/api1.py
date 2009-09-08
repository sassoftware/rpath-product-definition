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
            'ProductDefinitionTroveNotFoundError',
            'ProductDefinitionFileNotFoundError',
            'RepositoryError',
            'PlatformLabelMissingError',
            'ArchitectureNotFoundError',
            'FlavorSetNotFoundError',
            'ContainerTemplateNotFoundError',
            'BuildTemplateNotFoundError',
            'InvalidSchemaVersionError',
            ]

import itertools
import os
import StringIO
import weakref

from conary import changelog
from conary import errors as conaryErrors
from conary import versions as conaryVersions
from conary.conaryclient import filetypes, cmdline
from conary.deps import deps as conaryDeps
from conary.repository import errors as repositoryErrors

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
    "Raised when no such stage exists."

class ArchitectureNotFoundError(ProductDefinitionError):
    "Raised when no such architecture exists."

class FlavorSetNotFoundError(ProductDefinitionError):
    "Raised when no such flavor set exists."

class ContainerTemplateNotFoundError(ProductDefinitionError):
    "Raised when no such container template exists."

class BuildTemplateNotFoundError(ProductDefinitionError):
    "Raised when no such build template exists."

class ProductDefinitionTroveNotFoundError(ProductDefinitionError):
    """
    Raised when the trove containing the product definition file could not
    be found in the repository
    """

class ProductDefinitionFileNotFoundError(ProductDefinitionError):
    "Raised when the product definition file was not found in the repository"

class RepositoryError(ProductDefinitionError):
    "Generic error raised when a repository error was caught"

class PlatformLabelMissingError(ProductDefinitionError):
    "Raised when the platform label is missing, and a rebase was requested"

class InvalidSchemaVersionError(ProductDefinitionError):
    "Raised when the schema version in a product definition file is not recognized."

#}

class BaseDefinition(object):
    version = '2.0'
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

    def getResolveTroves(self):
        """
        @return: the search paths from this product definition, filtering
                 any results that have the isResolveTrove attribute set to 
                 False. This is a subset of the results from getSearchPaths
        @rtype: C{list} of C{_SearchPath} objects
        """
        return [x for x in self.searchPaths 
                if x.isResolveTrove or x.isResolveTrove is None]

    def getGroupSearchPaths(self):
        """
        @return: the search paths from this product definition, filtering
                 any results that do not have isGroupSearchPathTrove attribute
                 set to False. This is a subset of the results 
                 from getSearchPaths
        @rtype: C{list} of C{_SearchPath} objects
        """
        return  [x for x in self.searchPaths 
                 if x.isGroupSearchPathTrove 
                    or x.isGroupSearchPathTrove is None]

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

    def addSearchPath(self, troveName = None, label = None, version = None,
                      isResolveTrove = True, isGroupSearchPathTrove = True):
        """
        Add an search path.
        @param troveName: the trove name for the search path.
        @type troveName: C{str} or C{None}
        @param label: Label for the search path
        @type label: C{str} or C{None}
        @param version: Version for the search path
        @param version: C{str} or C{None}
        @param isResolveTrove: set to False if this element should be not
               be returned for getResolveTroves()  (defaults to True)
        @param isGroupSearchPathTrove: set to False if this element should be 
               not be returned for getGroupSearchPaths() (defaults to True)
        """
        assert(isResolveTrove or isGroupSearchPathTrove)
        self._addSource(troveName, label, version, _SearchPath,
                self.searchPaths, isResolveTrove = isResolveTrove,
                isGroupSearchPathTrove = isGroupSearchPathTrove)

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

    def getArchitectures(self):
        """
        @return: all defined architectures for both proddef and platform
        @rtype: C{list}
        """
        return self.architectures

    def hasArchitecture(self, name):
        """
        @param name: architecture name
        @type name: C{str}
        @rtype: C{bool}
        """
        return name in [ x.name for x in self.getArchitectures() ]

    def getArchitecture(self, name, default = -1):
        """
        @param name: architecture name
        @type name: C{str}
        @param default: if an architecture with this name is not found, return
        this value. If not specified, C{ArchitectureNotFoundError} is raised.
        @rtype: Architecture object
        @raises C{ArchitectureNotFoundError}: if architecture is not found, and
        no default was specified.
        """
        arches = self.getArchitectures()
        for arch in arches:
            if arch.name == name:
                return arch
        if default != -1:
            return default
        raise ArchitectureNotFoundError(name)

    def addArchitecture(self, name, displayName, flavor):
        """
        Add an architecture.
        @param name: name of architecture to add
        @type name: C{str}
        @param displayName: human readable name of the architecture
        @type displayName: C{str}
        @param flavor: flavor of architecture to add
        @type flavor: C{str}
        """
        for obj in self.architectures[:]:
            if obj.name == name:
                self.architectures.remove(obj)
        obj = _Architecture(name = name, displayName = displayName,
                flavor = flavor)
        self.architectures.append(obj)

    def clearArchitectures(self):
        """
        Reset architectures.
        """
        self.architectures = _Architectures()

    def getFlavorSets(self):
        """
        @return: all defined flavor sets
        @rtype: C{list} of FlavorSet objects
        """
        return self.flavorSets

    def getFlavorSet(self, name, default = -1):
        """
        @param name: flavor set name
        @type name: C{str}
        @param default: if an flavor set with this name is not found,
            return this value. If not specified, C{FlavorSetNotFoundError}
            is raised.
        @rtype: FlavorSet object
        @raises C{FlavorSetNotFoundError}: if flavor set is not found, and
        no default was specified.
        """
        flavorSets = self.getFlavorSets()
        for fs in flavorSets:
            if fs.name == name:
                return fs
        if default != -1:
            return default
        raise FlavorSetNotFoundError(name)

    def addFlavorSet(self, name, displayName, flavor):
        """
        add a flavor set.
        @param name: name of flavor set to add
        @type name: C{str}
        @param displayName: human readable name of the architecture
        @type displayName: C{str}
        @param flavor: flavor of flavor set to add
        @type flavor: C{str}
        """
        for obj in self.flavorSets[:]:
            if obj.name == name:
                self.flavorSets.remove(obj)
        obj = _FlavorSet(name = name, displayName = displayName,
                flavor = flavor)
        self.flavorSets.append(obj)

    def clearFlavorSets(self):
        """
        Reset flavor sets.
        """
        self.flavorSets = _FlavorSets()

    def getContainerTemplates(self):
        """
        @return: all defined container templates
        @rtype: C{list} of ContainerTemplate objects
        """
        return self.containerTemplates

    def getContainerTemplate(self, containerFormat, default = -1):
        """
        @param containerFormat: container template containerFormat
        @type containerFormat: C{str}
        @param default: if a container template with this containerFormat is not found,
            return this value. If not specified, C{ContainerTemplateNotFoundError}
            is raised.
        @rtype: ContainerTemplate object
        @raises C{ContainerTemplateNotFoundError}: if container template is not found, and
        no default was specified.
        """
        containerTemplates = self.getContainerTemplates()
        for tmpl in containerTemplates:
            if tmpl.containerFormat == containerFormat:
                return tmpl
        if default != -1:
            return default
        raise ContainerTemplateNotFoundError(containerFormat)

    def addContainerTemplate(self, image):
        """
        add a container template.
        @param image: Image
        @type image: C{imageTypes.Image}
        """
        self.containerTemplates.append(image)

    def clearContainerTemplates(self):
        """
        Reset container templates.
        """
        self.containerTemplates = _ContainerTemplates()

    def getBuildTemplates(self):
        """
        @return: all defined build templates
        @rtype: C{list} of BuildTemplate objects
        """
        return self.buildTemplates

    def getBuildTemplate(self, name, default = -1):
        """
        @param name: build template name
        @type name: C{str}
        @param default: if a build template with this name is not found,
            return this value. If not specified, C{BuildTemplateNotFoundError}
            is raised.
        @rtype: BuildTemplate object
        @raises C{BuildTemplateNotFoundError}: if build template is not found, and
        no default was specified.
        """
        buildTemplates = self.getBuildTemplates()
        for tmpl in buildTemplates:
            if tmpl.name == name:
                return tmpl
        if default != -1:
            return default
        raise BuildTemplateNotFoundError(name)

    def addBuildTemplate(self, name, displayName, architectureRef,
            containerTemplateRef, flavorSetRef = None):
        """
        add a build template.
        @param name: name of the build template
        @type name: C{str}
        @param displayName: human readable name of the build template
        @type displayName: C{str}
        @param architectureRef: reference to architecture
        @type architectureRef: C{str}
        @param containerTemplateRef: reference to container template
        @type containerTemplateRef: C{str}
        @pararm flavorSetRef: reference to flavorSet
        @type flavorSetRef: C{str}
        """
        tmpl = _BuildTemplate(name, displayName, architectureRef,
                containerTemplateRef, flavorSetRef = flavorSetRef)
        self.buildTemplates.append(tmpl)

    def clearBuildTemplates(self):
        """
        Reset build templates.
        """
        self.buildTemplates = _BuildTemplates()

    def _addSource(self, troveName, label, version, cls, intList, **kwargs):
        "Internal function for adding a Source"
        if label is not None:
            if isinstance(label, conaryVersions.Label):
                label = str(label)
        obj = cls(troveName = troveName, label = label, version = version,
                **kwargs)
        intList.append(obj)

    def _saveToRepository(self, conaryClient, label, message = None):
        if message is None:
            message = "Automatic checkin\n"

        recipe = self._recipe.replace('@NAME@', self._troveName)
        recipe = recipe.replace('@VERSION@', self.__class__.version)

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
        cs = conaryClient.createSourceTrove(troveName, str(label),
            self.__class__.version, pathDict, cLog)

        repos = conaryClient.getRepos()
        repos.commitChangeSet(cs)

    def _getStreamFromRepository(self, conaryClient, label):
        repos = conaryClient.getRepos()
        troveName = '%s:source' % self._troveName
        troveSpec = (troveName, label, None)
        try:
            troves = repos.findTroves(None, [ troveSpec ])
        except conaryErrors.TroveNotFound:
            raise ProductDefinitionTroveNotFoundError("%s=%s" % (troveName, label))
        except conaryErrors.RepositoryError, e:
            raise RepositoryError(str(e))
        # At this point, troveSpec is in troves and its value should not be
        # the empty list.
        nvfs = troves[troveSpec]
        #if not nvfs:
        #    raise ProductDefinitionTroveNotFoundError("%s=%s" % (troveName, label))
        nvfs = troves[troveSpec]
        n,v,f = nvfs[0]
        if hasattr(repos, 'getFileContentsFromTrove'):
            try:
                contents = repos.getFileContentsFromTrove(n,v,f,
                                              [self._troveFileName])[0]
            except repositoryErrors.PathsNotFound:
                raise ProductDefinitionFileNotFoundError()
            return contents.get(), (n,v,f)
        trvCsSpec = (n, (None, None), (v, f), True)
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
        raise ProductDefinitionFileNotFoundError("%s=%s" % (troveName, label))

    def _initFields(self):
        self.baseFlavor = None
        self.searchPaths = _SearchPaths()
        self.factorySources = _FactorySources()
        self.architectures = _Architectures()
        self.flavorSets = _FlavorSets()
        self.containerTemplates = _ContainerTemplates()
        self.buildTemplates = _BuildTemplates()

    @classmethod
    def _newNode(self, name, value):
        node = xmllib.StringNode(name = name).characters(value)
        return node

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
        self.sourceGroup = getattr(xmlObj, 'sourceGroup', None)
        self.imageGroup = getattr(xmlObj, 'imageGroup', None)
        self.baseLabel = getattr(xmlObj, 'baseLabel', None)
        self.baseFlavor = getattr(xmlObj, 'baseFlavor', None)
        self.stages.extend(getattr(xmlObj, 'stages', []))
        self.searchPaths.extend(getattr(xmlObj, 'searchPaths', []))
        self.factorySources.extend(getattr(xmlObj, 'factorySources', []))
        self.architectures.extend(getattr(xmlObj, 'architectures', []))
        self.flavorSets.extend(getattr(xmlObj, 'flavorSets', []))
        self.containerTemplates.extend(getattr(xmlObj, 'containerTemplates', []))
        self.buildTemplates.extend(getattr(xmlObj, 'buildTemplates', []))
        self.buildDefinition.extend(getattr(xmlObj, 'buildDefinition', []))
        # Add (weak) reference to the product definition
        for bd in self.buildDefinition:
            bd.setProductDefinition(self)
        self.platform = getattr(xmlObj, 'platform', None)

        self.secondaryLabels = getattr(xmlObj, 'secondaryLabels', None)

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
        @raises C{ProductDefinitionTroveNotFoundError}:
        @raises C{ProductDefinitionFileNotFoundError}:
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

    def getSourceGroup(self):
        """
        @return: the source group, if none is set, default to the image group
        @rtype: C{str}
        """
        if self.sourceGroup:
            return self.sourceGroup
        else:
            return None

    def setSourceGroup(self, sourceGroup):
        """
        Set the source group name
        @param sourceGroup: the image group name
        @type sourceGroup: C{str}
        """
        self.sourceGroup = sourceGroup

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
        platFlv = self.getPlatformBaseFlavor()
        if platFlv is not None:
            nflv = conaryDeps.parseFlavor(platFlv)
            flv = conaryDeps.overrideFlavor(flv, nflv)
        if self.baseFlavor is not None:
            nflv = conaryDeps.parseFlavor(self.baseFlavor)
            flv = conaryDeps.overrideFlavor(flv, nflv)
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
        raise StageNotFoundError(stageName)

    def addStage(self, name = None, labelSuffix = None, promoteMaps = None):
        """
        Add a stage.
        @param name: the stage's name
        @type name: C{str} or C{None}
        @param labelSuffix: Label suffix (e.g. '-devel') for the stage
        @type labelSuffix: C{str} or C{None}
        @param promoteMaps: list of promote maps for the stage
        @type promoteMaps: C{list} of C{(mapName, mapLabel)} tuples
        """
        obj = _Stage(name = name, labelSuffix = labelSuffix,
            promoteMaps = promoteMaps)
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

    def getSecondaryLabelsForStage(self, stageName):
        """
        @param stageName: A stage name
        @type stageName: C{str}
        @return: all secondary labels for the specified stage.
        @rtype: C{list} of (name, value) tuples
        """
        stageObj = self.getStage(stageName)
        if self.secondaryLabels is None:
            return []
        prefix = self.getProductDefinitionLabel()
        labelSuffix = stageObj.labelSuffix or '' # this can be blank

        ret = []
        for sl in self.secondaryLabels:
            name = sl.getName()
            label = sl.getLabel()
            fullLabel = self._getSecondaryLabel(label, labelSuffix)
            ret.append((name, fullLabel))
        return ret

    def getPromoteMapsForStages(self, fromStage, toStage, flattenLabels=()):
        """
        Construct a promote map from C{fromStage} to C{toStage}.

        This will include the "simple" label, all secondary labels, and
        all promote maps to C{toStage}. All implicit promotes (primary
        label, secondary labels, and flattened labels) are re-rooted at
        the new label rather than preserving any shadows.

        @param fromStage: Name of stage to promote I{from}
        @type  fromStage: C{str}
        @param toStage: Name of stage to promote I{to}
        @type  toStage: C{str}
        @param flattenLabels: Extra labels to "flatten" by promoting to the
                              target label.
        @type  flattenLabels: C{sequence or set}
        @return: dictionary mapping labels on C{fromStage} to labels
            on C{toStage}
        @rtype: C{dict}
        """
        fromStageObj = self.getStage(fromStage)
        toStageObj = self.getStage(toStage)
        toStageBranch = '/' + self._getLabelForStage(toStageObj)

        # Flattened labels - these come first so proddef-supplied maps 
        # will override them.
        fromTo = dict.fromkeys(flattenLabels, toStageBranch)

        # Primary label
        fromTo[self._getLabelForStage(fromStageObj)] = toStageBranch

        # Secondary labels
        if self.secondaryLabels is not None:
            fromSuffix = fromStageObj.labelSuffix
            toSuffix = toStageObj.labelSuffix
            for secondaryLabel in self.secondaryLabels:
                label = secondaryLabel.getLabel()
                fromLabel = self._getSecondaryLabel(label, fromSuffix)
                toLabel = self._getSecondaryLabel(label, toSuffix)
                fromTo[fromLabel] = '/' + toLabel

        # Promote maps
        promoteMapsDest = dict((x.getMapName(), x.getMapLabel())
            for x in toStageObj.getPromoteMaps())
        for pm in fromStageObj.getPromoteMaps():
            mapName = pm.getMapName()
            if mapName not in promoteMapsDest:
                continue
            fromTo[pm.getMapLabel()] = promoteMapsDest[mapName]

        return fromTo

    def getSearchPaths(self):
        """
        @return: the search paths from this product definition
        @rtype: C{list} of C{_SearchPath} objects
        """
        if self.searchPaths:
            return self.searchPaths
        return self.getPlatformSearchPaths()

    def getResolveTroves(self):
        """
        @return: the search paths from this product definition, filtering
                 any results that have isResolveTrove set to false. This
                 is a subset of the results from getSearchPaths
        @rtype: C{list} of C{_SearchPath} objects
        """
        if self.searchPaths:
            searchPaths = self.searchPaths
        else:
            searchPaths = self.getPlatformSearchPaths()
        if searchPaths:
            searchPaths = [x for x in searchPaths 
                           if x.isResolveTrove or x.isResolveTrove is None]
        return searchPaths

    def getGroupSearchPaths(self):
        """
        @return: the search paths from this product definition, filtering
                 any results that have the isGroupSearchPathTrove attribute
                 set to False. This is a subset of the results from 
                 getSearchPaths
        @rtype: C{list} of C{_SearchPath} objects
        """
        if self.searchPaths:
            searchPaths = self.searchPaths
        else:
            searchPaths = self.getPlatformSearchPaths()
        if searchPaths:
            searchPaths = [x for x in searchPaths 
                           if x.isGroupSearchPathTrove 
                              or x.isGroupSearchPathTrove is None]
        return searchPaths

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

    def addBuildDefinition(self, name = None, image = None, stages = None,
                           imageGroup = None, sourceGroup = None, 
                           architectureRef = None,
                           containerTemplateRef = None, buildTemplateRef = None,
                           flavorSetRef = None, flavor = None):
        """
        Add a build definition.
        Image types are specified by calling C{ProductDefinition.imageType}.
        Note that the usage of baseFlavor is deprecated in favor of using
        references to architectures and image templates.
        @param name: the name for the build definition
        @type name: C{str} or C{None}
        @param image: an image type, as returned by
        C{ProductDefinition.imageType}.
        @type image: an instance of an C{imageTypes.ImageType_Base}
        @param stages: Stages for which to build this image type
        @type stages: C{list} of C{str} referring to a C{_Stage} object's name
        @param imageGroup: An optional image group that will override the
        product definition's image group
        @type imageGroup: C{str}
        @param sourceGroup: An optional source group that will override the
        product definition's source group
        @type sourceGroup: C{str}
        @param architectureRef: the name of an architecture to inherit flavors
        from.
        @type architectureRef: C{str}
        @param containerTemplateRef: the name of the containerTemplate for
        this image. This value overrides the value implied by the
        buildTemplateRef, if supplied.
        @type containerTemplateRef: C{str}
        @param buildTemplateRef: the name of the buildTemplate to derive values
        for containerTemplateRef and architectureRef.
        @type: buildTemplateRef: C{str}
        @param flavorSetRef: the name of the flavorSet to use for this image
        @type: flavorSetRef: C{str}
        @param flavor: additional flavors
        @type flavor: C{str}
        """
        if architectureRef:
            # Make sure we have the architecture
            arch = self.getArchitecture(architectureRef, None)
            if not arch:
                self.getPlatformArchitecture(architectureRef)
        if containerTemplateRef:
            # make sure we have the containerTemplate
            tmpl = self.getContainerTemplate(containerTemplateRef, None)
            if not tmpl:
                self.getPlatformContainerTemplate(containerTemplateRef)
        if flavorSetRef:
            # make sure we have the flavorSet
            fs = self.getFlavorSet(flavorSetRef, None)
            if not fs:
                self.getPlatformFlavorSet(flavorSetRef)

        obj = Build(name = name, image = image, stages = stages,
                imageGroup = imageGroup,
                sourceGroup = sourceGroup,
                parentImageGroup = self.imageGroup,
                parentSourceGroup = self.sourceGroup,
                architectureRef = architectureRef,
                containerTemplateRef = containerTemplateRef,
                flavorSetRef = flavorSetRef,
                buildTemplateRef = buildTemplateRef,
                proddef = self, flavor = flavor)
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
                              version = None, isResolveTrove = True,
                              isGroupSearchPathTrove = True):
        """
        Add an search path.
        @param troveName: the trove name for the search path.
        @type troveName: C{str} or C{None}
        @param label: Label for the search path
        @type label: C{str} or C{None}
        @param version: Version for the search path
        @param version: C{str} or C{None}
        @param isResolveTrove: set to False if this element should be not
               be returned for getResolveTroves()  (defaults to True)
        @param isGroupSearchPathTrove: set to False if this element should be 
               not be returned for getGroupSearchPath() (defaults to True)
        """
        if self.platform is None:
            self.platform = PlatformDefinition()
        self._addSource(troveName, label, version, _SearchPath,
                        self.platform.searchPaths,
                        isResolveTrove = isResolveTrove,
                        isGroupSearchPathTrove = isGroupSearchPathTrove)

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

    def getPlatformName(self):
        """
        @return: The platform name.
        @rtype: C{str}
        """
        if self.platform is None:
            return None
        return self.platform.getPlatformName()

    def setPlatformName(self, platformName):
        """
        Set the platform name.
        @param platformName: The platform name.
        @type platformName: C{str}
        """
        self._ensurePlatformExists()
        self.platform.setPlatformName(platformName)

    def getPlatformVersionTrove(self):
        """
        @return: the platform version trove.
        @rtype: C{str}
        """
        if self.platform is None:
            return None
        return self.platform.getPlatformVersionTrove()

    def setPlatformVersionTrove(self, troveSpec):
        """
        Set the platform version trove.
        @param troveSpec: The platfrm version trove
        @type platformName: C{str}
        """
        self._ensurePlatformExists()
        self.platform.setPlatformVersionTrove(troveSpec)

    def getPlatformAutoLoadRecipes(self):
        """
        @return: auto load recipes.
        @rtype: C{list} of C{AutoLoadRecipe}
        """
        if self.platform is None:
            return []
        return self.platform.getAutoLoadRecipes()

    def addPlatformAutoLoadRecipe(self, troveName, label):
        """
        Add an auto load recipe
        @param troveName: Trove name
        @type troveName: C{str}
        @param label: Label for the trove
        @type label: C{str}
        """
        self._ensurePlatformExists()
        self.platform.addAutoLoadRecipe(troveName, label)

    def clearPlatformAutoLoadRecipes(self):
        """
        Clear the list of auto load recipes for the platform
        """
        if self.platform is None:
            return
        self.platform.clearAutoLoadRecipes()
        return self

    def getPlatformBaseFlavor(self):
        """
        @return: the platform's base flavor
        @rtype: C{str}
        """

        if self.platform is None:
            return None
        return self.platform.baseFlavor

    def setPlatformBaseFlavor(self, baseFlavor):
        """
        Set the platform's base flavor.
        @param baseFlavor: A flavor for the platform.
        @type baseFlavor: C{str}
        """
        self._ensurePlatformExists()
        self.platform.baseFlavor = baseFlavor

    def getPlatformSourceTrove(self):
        """
        @return: the source trove the for platform
        @rtype: C{str}
        """
        if self.platform is None:
            return None
        return self.platform.sourceTrove

    def setPlatformSourceTrove(self, sourceTrove):
        """
        Set the platform's source trove.
        @param sourceTrove: the source trove name for the platform
        @type sourceTrove: C{str}
        """
        self._ensurePlatformExists()
        self.platform.sourceTrove = sourceTrove

    def getPlatformUseLatest(self):
        """
        @return: the platform's useLatest flag.
        @rtype: C{bool} or None
        """
        if self.platform is None:
            return None
        return self.platform.useLatest

    def setPlatformUseLatest(self, useLatest):
        """
        Set the platform's useLatest flag.
        @param useLatest: value for useLatest flag
        @type useLatest: C{bool}
        """
        self._ensurePlatformExists()
        self.platform.useLatest = useLatest

    def getPlatformArchitecture(self, name, default = -1):
        """
        Retrieve the architecture with the specified name from the platform.
        @param name: architecture name
        @type name: C{str}
        @param default: if an architecture with this name is not found, return
        this value. If not specified, C{ArchitectureNotFoundError} is raised.
        @rtype: Architecture object
        @raises C{ArchitectureNotFoundError}: if architecture is not found, and
        no default was specified.
        """
        pa = None
        if self.platform:
            pa = self.platform.getArchitecture(name, None)
        if pa is not None or default != -1:
            return pa
        raise ArchitectureNotFoundError(name)

    def getPlatformFlavorSet(self, name, default = -1):
        """
        Retrieve the flavorSet with the specified name from the platform.
        @param name: flavorSet name
        @type name: C{str}
        @param default: if a flavorSet with this name is not found, return
        this value. If not specified, C{FlavorSetNotFoundError} is raised.
        @rtype: FlavorSet object
        @raises C{FlavorSetNotFoundError}: if flavorSet is not found, and
        no default was specified.
        """
        pa = None
        if self.platform:
            pa = self.platform.getFlavorSet(name, None)
        if pa is not None or default != -1:
            return pa
        raise FlavorSetNotFoundError(name)

    def getPlatformContainerTemplate(self, containerFormat, default = -1):
        """
        Retrieve the containerTemplate with the specified containerFormat from the platform.
        @param containerFormat: containerTemplate containerFormat
        @type containerFormat: C{str}
        @param default: if a containerTemplate with this containerFormat is not found, return
        this value. If not specified, C{ContainerTemplateNotFoundError} is raised.
        @rtype: ContainerTemplate object
        @raises C{ContainerTemplateNotFoundError}: if containerTemplate is not found, and
        no default was specified.
        """
        pa = None
        if self.platform:
            pa = self.platform.getContainerTemplate(containerFormat, None)
        if pa is not None or default != -1:
            return pa
        raise ContainerTemplateNotFoundError(containerFormat)

    def getPlatformBuildTemplate(self, name, default = -1):
        """
        Retrieve the buildTemplate with the specified name from the platform.
        @param name: buildTemplate name
        @type name: C{str}
        @param default: if a buildTemplate with this name is not found, return
        this value. If not specified, C{BuildTemplateNotFoundError} is raised.
        @rtype: BuildTemplate object
        @raises C{BuildTemplateNotFoundError}: if buildTemplate is not found, and
        no default was specified.
        """
        pa = None
        if self.platform:
            pa = self.platform.getBuildTemplate(name, None)
        if pa is not None or default != -1:
            return pa
        raise BuildTemplateNotFoundError(name)

    def addSecondaryLabel(self, name, label):
        """
        Add a secondary label to the product definition.
        @param name: Name for the secondary label
        @type name: C{str}
        @param label: Label for the secondary label
        @type label: C{str}
        """
        if self.secondaryLabels is None:
            self.secondaryLabels = _SecondaryLabels()
        self.secondaryLabels.append(SecondaryLabel(name, label))
        return self

    def getSecondaryLabels(self):
        """
        @return: the seconary labels for this product definition.
        @rtype: C{list}
        """
        if self.secondaryLabels is None:
            return []
        return self.secondaryLabels

    def clearSecondaryLabels(self):
        """
        Reset secondary label list.
        """
        self.secondaryLabels = None

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
        """
        fields = fields or {}
        if name is not None:
            fields.setdefault('containerFormat', name)
        return imageTypes.Image(fields)

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

    def setBaseLabel(self, label):
        """
        Set the base label for this product definition.
        @param label: Value for the base label.
        @type label: C{str}
        """
        self.baseLabel = label

    def getBaseLabel(self):
        """
        @return: the base label for this product definition.
        @rtype: C{str}
        """
        return self.baseLabel

    def getProductDefinitionLabel(self):
        """
        Method that returns the product definition's label
        @return: a Conary label string
        @rtype: C{str}
        @raises MissingInformationError: if there isn't enough information
            in the product definition to generate the label
        """
        if self.baseLabel is not None:
            return self.baseLabel

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
            key = (build.imageGroup, label, tuple())
            if key not in sPathsSet:
                sPathsList.append(key)
                sPathsSet.add(key)
        # Append the global image group
        key = (self.getImageGroup(), label, tuple())
        if key not in sPathsSet:
            sPathsList.append(key)
            sPathsSet.add(key)
        # Now append the search paths from this object, if available, or from
        # the upstream platform, if available

        # We are purposely dropping the versions from the platform definition
        # on creation.

        sPaths = self.getSearchPaths()
        for sp in sPaths or []:
            attrs = []
            for key in ('isResolveTrove', 'isGroupSearchPathTrove'):
                val = sp.__getattribute__(key)
                if val is not None:
                    attrs.append((key, val))
            key = (sp.troveName, sp.label, tuple(attrs))
            if key not in sPathsSet:
                sPathsList.append(key)
                sPathsSet.add(key)

        for troveName, label, attrs in sPathsList:
            nplat.addSearchPath(troveName=troveName, label=label, **dict(attrs))

        for arch in self.getArchitectures():
            nplat.addArchitecture(name = arch.name,
                    displayName = arch.displayName, flavor = arch.flavor)

        for flvSet in self.getFlavorSets():
            nplat.addFlavorSet(name = flvSet.name,
                    displayName = flvSet.displayName, flavor = flvSet.flavor)

        for ctmpl in self.getContainerTemplates():
            nplat.addContainerTemplate(ctmpl)

        for btmpl in self.getBuildTemplates():
            nplat.addBuildTemplate(name = btmpl.name,
                    displayName = btmpl.displayName,
                    architectureRef = btmpl.architectureRef,
                    containerTemplateRef = btmpl.containerTemplateRef,
                    flavorSetRef = btmpl.flavorSetRef,)

        nplat.setPlatformName(self.getPlatformName())
        nplat.setPlatformVersionTrove(self.getPlatformVersionTrove())

        for alr in self.getPlatformAutoLoadRecipes():
            nplat.addAutoLoadRecipe(alr.getTroveName(), alr.getLabel())

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
                if not tv.startswith('/'):
                    tv = "/" + tv
                label = str(conaryVersions.VersionFromString(tv).trailingLabel())
            else:
                label = None
        if label is None:
            raise PlatformLabelMissingError()
        nplat = self.toPlatformDefinition()
        nplat.loadFromRepository(client, label)
        nplat.snapshotVersions(client)
        self._rebase(label, nplat, useLatest = useLatest)

    def _rebase(self, label, nplat, useLatest = None):
        # Create a new platform definition
        self.platform = PlatformDefinition()
        # Fill it in with fields from the upstream one
        self.setPlatformBaseFlavor(nplat.getBaseFlavor())
        self.setPlatformSourceTrove(nplat.sourceTrove)
        self.setPlatformUseLatest(useLatest)
        self.platform.setPlatformName(nplat.getPlatformName())
        self.platform.setPlatformVersionTrove(nplat.getPlatformVersionTrove())
        for alr in nplat.getAutoLoadRecipes():
            self.addPlatformAutoLoadRecipe(troveName = alr.getTroveName(),
                    label = alr.getLabel())
        for sp in nplat.getSearchPaths():
            self.addPlatformSearchPath(troveName=sp.troveName,
                               label=sp.label,
                               version=sp.version,
                               isResolveTrove=sp.isResolveTrove,
                               isGroupSearchPathTrove=sp.isGroupSearchPathTrove)
        for fs in nplat.getFactorySources():
            self.addPlatformFactorySource(troveName=fs.troveName,
                                          label=fs.label,
                                          version=fs.version)
        for item in nplat.getArchitectures():
            self.platform.addArchitecture(name = item.name,
                                          displayName = item.displayName,
                                          flavor = item.flavor)
        for flvSet in nplat.getFlavorSets():
            self.platform.addFlavorSet(name = flvSet.name,
                    displayName = flvSet.displayName, flavor = flvSet.flavor)

        for image in nplat.getContainerTemplates():
            self.platform.addContainerTemplate(image)

        for btmpl in nplat.getBuildTemplates():
            self.platform.addBuildTemplate(name = btmpl.name,
                    displayName = btmpl.displayName,
                    architectureRef = btmpl.architectureRef,
                    containerTemplateRef = btmpl.containerTemplateRef,
                    flavorSetRef = btmpl.flavorSetRef)

    def _getSecondaryLabel(self, label, suffix):
        """
        Given a label from C{secondaryStages} and a C{suffix},
        construct a complete "secondary" label.

        @param label: Base label from C{secondaryStages} to use as
            a prefix
        @type  label: C{str}
        @param suffix: Suffix to append to base label
        @type  suffix: C{str}
        @return: constructed secondary label
        @rtype: C{str}
        """
        if '@' in label:
            # Just append the stage suffix
            return str(label + suffix)
        else:
            # Use the entire product label
            prefix = self.getProductDefinitionLabel()
            return str(prefix + label + suffix)

    def _initFields(self):
        BaseDefinition._initFields(self)
        self.stages = _Stages()
        self.productName = None
        self.productShortname = None
        self.productDescription = None
        self.productVersion = None
        self.productVersionDescription = None
        self.conaryRepositoryHostname = None
        self.conaryNamespace = None
        self.imageGroup = None
        self.sourceGroup = None
        self.baseLabel = None
        self.buildDefinition = _BuildDefinition()
        self.platform = None
        self.secondaryLabels = None

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
        BaseDefinition._initFields(self)
        self.useLatest = None
        self.sourceTrove = None
        self.platformName = None
        self.platformVersionTrove = None
        self.autoLoadRecipes = None

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
        self.architectures = getattr(xmlObj.platform, 'architectures', None)
        self.flavorSets = getattr(xmlObj.platform, 'flavorSets', None)
        self.containerTemplates = getattr(xmlObj.platform, 'containerTemplates', None)
        self.buildTemplates = getattr(xmlObj.platform, 'buildTemplates', None)
        self.platformName = getattr(xmlObj.platform, 'platformName', None)
        self.platformVersionTrove = getattr(xmlObj.platform, 'platformVersionTrove', None)
        self.autoLoadRecipes = getattr(xmlObj.platform, 'autoLoadRecipes', None)

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
        @raises C{ProductDefinitionTroveNotFoundError}:
        @raises C{ProductDefinitionFileNotFoundError}:
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
            troveSpecs.add(sp.getTroveTup(template=True))
        troveSpecs = sorted(troveSpecs)
        try:
            troves = repos.findTroves(None, troveSpecs, allowMissing = True)
        except conaryErrors.RepositoryError, e:
            raise RepositoryError(str(e))

        for sp in itertools.chain(self.getSearchPaths(),
                                  self.getFactorySources()):
            key = sp.getTroveTup(template=True)
            if key not in troves:
                raise ProductDefinitionTroveNotFoundError("%s=%s" % key[:2])
            # Use the latest version, if for some reason there is more
            # than one in the result set.
            nvf = max(troves[key])
            sp.version = str(nvf[1].trailingRevision())

    def getPlatformName(self):
        """
        @return: The platform name.
        @rtype: C{str}
        """
        if self.platformName is None:
            return None
        return self.platformName.getText()

    def setPlatformName(self, platformName):
        """
        Set the platform name.
        @param platformName: The platform name.
        @type platformName: C{str}
        """
        if platformName is None:
            self.platformName = None
        else:
            self.platformName = self._newNode('platformName', platformName)

    def getPlatformVersionTrove(self):
        """
        @return: the platform version trove.
        @rtype: C{str}
        """
        if self.platformVersionTrove is None:
            return None
        return self.platformVersionTrove.getText()

    def setPlatformVersionTrove(self, troveSpec):
        """
        Set the platform version trove.
        @param troveSpec: The platfrm version trove
        @type platformName: C{str}
        """
        if troveSpec is None:
            self.platformVersionTrove = None
        else:
            self.platformVersionTrove = self._newNode('platformVersionTrove',
            troveSpec)

    def clearAutoLoadRecipes(self):
        """
        Clear the list of auto load recipes for the platform
        """
        self.autoLoadRecipes = None

    def addAutoLoadRecipe(self, troveName = None, label = None):
        """
        Add an auto load recipe
        @param troveName: Trove name
        @type troveName: C{str}
        @param label: Label for the trove
        @type label: C{str}
        """
        if self.autoLoadRecipes is None:
            self.autoLoadRecipes = _AutoLoadRecipes()
        self.autoLoadRecipes.append(_AutoLoadRecipe(troveName, label))
        return self

    def getAutoLoadRecipes(self):
        """
        @return: auto load recipes.
        @rtype: C{list} of C{AutoLoadRecipe}
        """
        if self.autoLoadRecipes is None:
            return []
        return [ AutoLoadRecipe(x) for x in self.autoLoadRecipes ]

#{ Objects for the representation of ProductDefinition fields

class _Stages(xmllib.SerializableList):
    tag = "stages"

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _SearchPaths(xmllib.SerializableList):
    tag = "searchPaths"

class _SimpleElement(xmllib.SerializableObject):
    _xmlTagName = None
    def __init__(self, value, attributes = None):
        self.value = value
        self._attributes = attributes or {}
    def _getName(self):
        return self._xmlTagName
    def _getLocalNamespaces(self):
        return {}
    def _iterAttributes(self):
        return self._attributes.iteritems()
    def _iterChildren(self):
        return []

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _AutoLoadRecipes(xmllib.SerializableList):
    tag = "autoLoadRecipes"

class _AutoLoadRecipe(_SimpleElement):
    _xmlTagName = 'autoLoadRecipe'
    def __init__(self, troveName, label):
        _SimpleElement.__init__(self, None,
            dict(troveName = troveName, label = label))

    def getTroveName(self):
        return self._attributes.get('troveName')

    def getLabel(self):
        return self._attributes.get('label')

class AutoLoadRecipe(object):
    __slots__ = [ '_troveName', '_label' ]
    def __init__(self, node):
        self._troveName = node.getTroveName()
        self._label = node.getLabel()

    def getTroveName(self):
        """
        @return: the trove name for the auto load recipe
        @rtype: C{str}
        """
        return self._troveName

    def getLabel(self):
        """
        @return: the label for the auto load recipe
        @rtype: C{str}
        """
        return self._label

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _FactorySources(xmllib.SerializableList):
    tag = "factorySources"

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _Architectures(xmllib.SerializableList):
    tag = "architectures"

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _FlavorSets(xmllib.SerializableList):
    tag = "flavorSets"

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _ContainerTemplates(xmllib.SerializableList):
    tag = "containerTemplates"

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _BuildTemplates(xmllib.SerializableList):
    tag = "buildTemplates"

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _BuildDefinition(xmllib.SerializableList):
    tag = "buildDefinition"

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _SecondaryLabels(xmllib.SerializableList):
    tag = "secondaryLabels"

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _PromoteMaps(xmllib.SerializableList):
    tag = "promoteMaps"

# pylint: disable-msg=R0903
# Too few public methods (1/2): this is an interface
class _Stage(xmllib.SlotBasedSerializableObject):
    __slots__ = [ 'name', 'labelSuffix', 'promoteMaps' ]
    tag = "stage"

    def __init__(self, name = None, labelSuffix = None, promoteMaps = None):
        xmllib.SlotBasedSerializableObject.__init__(self)
        self.name = name
        self.labelSuffix = labelSuffix
        if not promoteMaps:
            self.promoteMaps = None
            return
        self.promoteMaps = _PromoteMaps()
        for ent in promoteMaps:
            mapName, mapLabel = ent[:2]
            self.promoteMaps.append(PromoteMap(mapName, mapLabel))

    def getPromoteMaps(self):
        if self.promoteMaps is None:
            return []
        return list(self.promoteMaps)

class _TroveSpec(xmllib.SlotBasedSerializableObject):
    __slots__ = ['troveName', 'label', 'version']

    def __init__(self, troveName = None, label = None, version = None):
        self.troveName = troveName
        self.label = label
        self.version = version

    def getTroveTup(self, template=False):
        """
        Get a trovespec tuple for the search path or its template.

        @param template: If C{True}, use the template path; otherwise
            return the "pinned" path.
        @type  template: C{bool}
        @return: (name, version, flavor)
        """
        if template:
            return (self.troveName, self.label, None)
        else:
            version = self.label
            if self.version:
                version += '/' + self.version
            return (self.troveName, version, None)


class _SearchPath(_TroveSpec):
    __slots__ = ['troveName', 'label', 'version', 'isResolveTrove',
                 'isGroupSearchPathTrove']
    tag = "searchPath"

    def __init__(self, troveName = None, label = None, version = None,
                 isResolveTrove = True, isGroupSearchPathTrove = True):
        _TroveSpec.__init__(self, troveName=troveName, label=label,
                            version=version)
        self.isResolveTrove = isResolveTrove
        self.isGroupSearchPathTrove = isGroupSearchPathTrove

class _FactorySource(_TroveSpec):
    tag = "factorySource"

class _Architecture(xmllib.SlotBasedSerializableObject):
    __slots__ = [ 'name', 'displayName', 'flavor' ]
    tag = "architecture"

    def __init__(self, name, displayName, flavor):
        xmllib.SlotBasedSerializableObject.__init__(self)
        self.name = name
        self.displayName = displayName
        self.flavor = flavor

class _FlavorSet(xmllib.SlotBasedSerializableObject):
    __slots__ = [ 'name', 'displayName', 'flavor' ]
    tag = "flavorSet"

    def __init__(self, name, displayName, flavor):
        self.name = name
        self.displayName = displayName
        self.flavor = flavor

class _BuildTemplate(xmllib.SlotBasedSerializableObject):
    __slots__ = [ 'name', 'displayName', 'architectureRef',
            'containerTemplateRef', 'flavorSetRef']
    tag = "buildTemplate"

    def __init__(self, name, displayName, architectureRef,
            containerTemplateRef, flavorSetRef = None):
        self.name = name
        self.displayName = displayName
        self.architectureRef = architectureRef
        self.containerTemplateRef = containerTemplateRef
        self.flavorSetRef = flavorSetRef

class Build(xmllib.SerializableObject):
    __slots__ = [ 'name', 'image', 'stages', 'imageGroup', 'sourceGroup',
                  'parentImageGroup', 'parentSourceGroup',
                  'architectureRef', 'flavorSetRef', 'containerTemplateRef',
                  'buildTemplateRef', 'flavor', '_proddef']
    tag = "build"

    def __init__(self, name = None, image = None, stages = None,
                 imageGroup = None, sourceGroup = None, 
                 parentImageGroup = None, parentSourceGroup = None,
                 architectureRef = None, flavorSetRef = None,
                 containerTemplateRef = None,
                 buildTemplateRef = None, flavor = None,
                 proddef = None, baseLabel = None):
        xmllib.SlotBasedSerializableObject.__init__(self)
        self.name = name
        self.image = image
        self.stages = stages or []
        self.imageGroup = imageGroup
        self.sourceGroup = sourceGroup
        self.parentImageGroup = parentImageGroup
        self.parentSourceGroup = parentSourceGroup
        self.architectureRef = architectureRef
        self.containerTemplateRef = containerTemplateRef
        self.flavorSetRef = flavorSetRef
        self._proddef = None
        self.setProductDefinition(proddef)
        self.flavor = flavor
        self.buildTemplateRef = buildTemplateRef

    def __eq__(self, build):
        for key in self.__slots__:
            if key == '_proddef':
                # Ignore the weak ref
                continue
            if self.__getattribute__(key) != build.__getattribute__(key):
                return False
        return True

    def __ne__(self, build):
        return not self.__eq__(build)

    def getBuildImageGroup(self):
        if self.imageGroup is None:
            return self.parentImageGroup
        return self.imageGroup

    def getBuildSourceGroup(self):
        if self.sourceGroup:
            return self.sourceGroup
        elif self.parentSourceGroup:
            return self.parentSourceGroup
        else:
            return None

    def getBuildImage(self):
        fields = {}
        if self._proddef:
            proddef = self._proddef()
            tmpl = proddef.getContainerTemplate(self.containerTemplateRef, None)
            if not tmpl and proddef.platform:
                tmpl = proddef.getPlatformContainerTemplate( \
                        self.containerTemplateRef)
            if tmpl:
                fields.update(tmpl.fields)
                fields['containerFormat'] = tmpl.containerFormat

        if self.image:
            fields.update(self.image.fields)
        return imageTypes.Image(fields)

    def getBuildStages(self):
        return list(self.stages)

    def getBuildName(self):
        return self.name

    def getBuildBaseFlavor(self):
        # Grab flavor from the referenced components
        if self._proddef is None:
            return ''
        pd = self._proddef
        if pd is not None:
            pd = pd()
        if pd is None:
            return ''

        # Grab base flavor from platform + product
        flv = conaryDeps.parseFlavor(pd.getBaseFlavor())

        # Dereference the flavorSetRef and architectureRef from
        # buildTemplateRef if needed
        flavorSetRef = self.flavorSetRef
        architectureRef = self.architectureRef
        buildTemplateRef = self.buildTemplateRef
        if buildTemplateRef:
            buildTemplate = pd.getBuildTemplate(buildTemplateRef, None)
            if not buildTemplate:
                buildTemplate = pd.getPlatformBuildTemplate(buildTemplateRef)
            if not architectureRef:
                architectureRef = buildTemplate.architectureRef
            if not flavorSetRef:
                flavorSetRef = buildTemplate.flavorSetRef
        try:
            if flavorSetRef:
                methods = [ pd.getPlatformFlavorSet, pd.getFlavorSet ]
                for meth in methods:
                    obj = meth(flavorSetRef, None)
                    if obj is None:
                        continue
                    nflv = conaryDeps.parseFlavor(obj.flavor)
                    flv = conaryDeps.overrideFlavor(flv, nflv)
            if architectureRef:
                methods = [ pd.getPlatformArchitecture, pd.getArchitecture ]
                for meth in methods:
                    obj = meth(architectureRef, None)
                    if obj is None:
                        continue
                    nflv = conaryDeps.parseFlavor(obj.flavor)
                    flv = conaryDeps.overrideFlavor(flv, nflv)
            if self.flavor:
                nflv = conaryDeps.parseFlavor(self.flavor)
                flv = conaryDeps.overrideFlavor(flv, nflv)
        except RuntimeError, e:
            raise ProductDefinitionError(str(e))
        return str(flv)

    def setProductDefinition(self, proddef):
        self._proddef = None
        if proddef:
            self._proddef = weakref.ref(proddef)

    def _getName(self):
        return self.tag

    def _getLocalNamespaces(self):
        return {}

    def _iterChildren(self):
        if self.image is not None:
            attrs = self.image._iterAttributes()
            yield xmllib.NullNode(dict(attrs), name = 'image')
        for stage in self.stages:
            yield xmllib.NullNode(dict(ref=stage), name = 'stage')
        if self.imageGroup is not None:
            yield xmllib.StringNode(name = 'imageGroup').characters(
                self.imageGroup)
        if self.sourceGroup:
            yield xmllib.StringNode(name = 'sourceGroup').characters(
                self.sourceGroup)

    def _iterAttributes(self):
        for f in ['name', 'architectureRef', 'containerTemplateRef',
                'flavorSetRef', 'flavor']:
            attrVal = getattr(self, f)
            if attrVal is not None:
                yield (f, attrVal)
#}

class _BaseSerializableObject(xmllib.SerializableObject):
    def _getName(self):
        return self.tag

    def _getLocalNamespaces(self):
        return {}

    def _iterAttributes(self):
        for attr in self._attributes:
            value = getattr(self, attr)
            if value is not None:
                yield (attr, value)

class SecondaryLabel(_BaseSerializableObject):
    __slots__ = [ 'name', 'label' ]
    _attributes = [ 'name' ]

    tag = 'secondaryLabel'

    def __init__(self, name, label):
        self.name = name
        self.label = label

    def getName(self):
        return self.name

    def getLabel(self):
        return self.label

    def _iterChildren(self):
        return [ self.label ]

class PromoteMap(_BaseSerializableObject):
    __slots__ = [ 'name', 'label' ]
    _attributes = __slots__

    tag = 'promoteMap'

    def __init__(self, mapName, mapLabel):
        self.name = mapName
        self.label = mapLabel

    def getMapLabel(self):
        return self.label

    def getMapName(self):
        return self.name

    def _iterChildren(self):
        return []

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
            isResolveTrove = node.getAttribute('isResolveTrove')
            if isResolveTrove is not None:
                isResolveTrove = xmllib.BooleanNode.fromString(isResolveTrove)
            isGroupSearchPathTrove = node.getAttribute('isGroupSearchPathTrove')
            if isGroupSearchPathTrove is not None:
                isGroupSearchPathTrove = xmllib.BooleanNode.fromString(
                                                    isGroupSearchPathTrove)
            pyObj = _SearchPath(
                troveName = node.getAttribute('troveName'),
                label = node.getAttribute('label'),
                version = node.getAttribute('version'),
                isResolveTrove = isResolveTrove,
                isGroupSearchPathTrove = isGroupSearchPathTrove)
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

    def _processArchitectures(self, architectures):
        return self._processNFCollection(architectures,
            _Architectures, _Architecture)

    def _processFlavorSets(self, flavorSets):
        return self._processNFCollection(flavorSets, _FlavorSets, _FlavorSet)

    def _processContainerTemplates(self, images):
        containerTemplates = _ContainerTemplates()
        for node in images:
            pyObj = imageTypes.Image(node)
            containerTemplates.append(pyObj)
        return containerTemplates

    def _processBuildTemplates(self, buildTemplates):
        builds = _BuildTemplates()
        for node in buildTemplates:
            pyObj = _BuildTemplate(name = node.getAttribute('name'),
                    displayName = node.getAttribute('displayName'),
                    architectureRef = node.getAttribute('architectureRef'),
                    containerTemplateRef = node.getAttribute('containerTemplateRef'),
                    flavorSetRef = node.getAttribute('flavorSetRef'))
            builds.append(pyObj)
        return builds

    def _processNFCollection(self, collection, ListClass, ItemClass):
        collObj = ListClass()
        for node in collection:
            pyObj = ItemClass(
                name = node.getAttribute('name'),
                displayName = node.getAttribute('displayName'),
                flavor = node.getAttribute('flavor'))
            collObj.append(pyObj)
        seen = set()
        # purge duplicate entries. last one wins (it was added most recently)
        for node in reversed(collObj):
            name = node.name
            if name in seen:
                collObj.remove(node)
            seen.add(name)
        return collObj

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
        listNode = node.getChildren('architectures')
        if listNode:
            self.platform.architectures = self._processArchitectures(
                listNode[0].getChildren('architecture'))
        flavorSets = node.getChildren('flavorSets')
        if flavorSets:
            self.platform.flavorSets = self._processFlavorSets(
                    flavorSets[0].getChildren('flavorSet'))
        containerTemplates = node.getChildren('containerTemplates')
        if containerTemplates:
            self.platform.containerTemplates = self._processContainerTemplates(\
                    containerTemplates[0].getChildren('image'))
        buildTemplates = node.getChildren('buildTemplates')
        if buildTemplates:
            self.platform.buildTemplates = self._processBuildTemplates(
                    buildTemplates[0].getChildren('buildTemplate'))
        baseFlavorChildren = node.getChildren('baseFlavor')
        if baseFlavorChildren:
            self.platform.baseFlavor = baseFlavorChildren[0].getText()
        chList = node.getChildren('platformName')
        if chList:
            self.platform.platformName = chList[0]
        chList = node.getChildren('platformVersionTrove')
        if chList:
            self.platform.platformVersionTrove = chList[0]
        chList = node.getChildren('autoLoadRecipes')
        if chList:
            chList = chList[0].getChildren('autoLoadRecipe')
            for child in chList:
                troveName = child.getAttribute('troveName')
                label = child.getAttribute('label')
                self.platform.addAutoLoadRecipe(troveName, label)

    def _getSchemaVersion(self):
        nsName = self.getAttributeByNamespace('schemaLocation',
                xmllib.DataBinder.xmlSchemaNamespace)
        if not nsName:
            return None
        try:
            nsName = os.path.basename(nsName).split()[-1]
            prefix, nsName = nsName.split('-', 1)
            if (prefix != 'rpd'):
                raise InvalidSchemaVersionError(
                    'Invalid schema prefix %s, expected rpd', prefix)
            nsName, suffix = nsName.rsplit('.', 1)
            if (suffix != 'xsd'):
                raise InvalidSchemaVersionError(
                    'Invalid schema suffix %s, expected xsd', suffix)
            return nsName
        except:
            raise InvalidSchemaVersionError('Failed to parse schema version %s',
                                       nsName)

def _addPlatformDefaults(platform):
    platform.setBaseFlavor('~X, ~!alternatives, !bootstrap, ~builddocs, ~buildtests, !cross, ~desktop, ~!dom0, ~!domU, ~emacs, ~!gcj, ~gnome, ~gtk, ~ipv6, ~krb, ~ldap, ~nptl, pam, ~pcre, ~perl, ~!pie, ~python, ~readline, ~!sasl, ~!selinux, ~ssl, ~tcl, ~tk, ~!vmware, ~!xen, ~!xfce')

    platform.addFlavorSet('ami', 'AMI',
            '~!dom0,~domU,~xen,~!vmware')
    platform.addFlavorSet('generic', 'Generic',
            '~!dom0,~!domU,~!xen,~!vmware')
    platform.addFlavorSet('hyper_v', 'Hyper-V',
            '!vmware, ~!xen, !dom0')
    platform.addFlavorSet('virtual_iron', 'Virtual Iron',
            '!xen,!vmware')
    platform.addFlavorSet('vmware', 'VMware',
            '~!dom0,!domU,~!xen,~vmware')
    platform.addFlavorSet('xen', 'Xen',
            '~!dom0,~domU,~xen,~!vmware')

    platform.addArchitecture('x86', 'x86 (32-bit)',
            'is: x86(~i486,~i586,~i686,~cmov,~mmx,~sse,~sse2)')
    platform.addArchitecture('x86_64', 'x86 (64-bit)',
            'is: x86(~i486,~i586,~i686,~cmov,~mmx,~sse,~sse2) x86_64')

    platform.addContainerTemplate(imageTypes.Image( \
            {"containerFormat": "amiImage",
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "amiHugeDiskMountPoint": False,
             "freespace": 1024,
             "swapSize": 1024}))
    platform.addContainerTemplate(imageTypes.Image( \
            {"containerFormat": "applianceIsoImage",
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "anacondaCustomTrove": "",
             "anacondaTemplatesTrove": "conary.rpath.com@rpl:2",
             "betaNag": False,
             "bugsUrl": "",
             "maxIsoSize": None,
             "mediaTemplateTrove": "",
             "showMediaCheck": False}))
    platform.addContainerTemplate(imageTypes.Image( \
            {"containerFormat": "installableIsoImage",
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "anacondaCustomTrove": "",
             "anacondaTemplatesTrove": "conary.rpath.com@rpl:2",
             "betaNag": False,
             "bugsUrl": "",
             "maxIsoSize": None,
             "mediaTemplateTrove": "",
             "showMediaCheck": False}))
    platform.addContainerTemplate(imageTypes.Image( \
            {"containerFormat": "netBootImage",
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": ""}))
    platform.addContainerTemplate(imageTypes.Image( \
            {"containerFormat": "rawFsImage",
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "freespace": 1024,
             "swapSize": 512}))
    platform.addContainerTemplate(imageTypes.Image( \
            {"containerFormat": "rawHdImage",
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "freespace": 1024,
             "swapSize": 512}))
    platform.addContainerTemplate(imageTypes.Image( \
            {"containerFormat": "tarballImage",
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "swapSize": "0"}))
    platform.addContainerTemplate(imageTypes.Image( \
            {"containerFormat": "updateIsoImage",
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "anacondaCustomTrove": "",
             "anacondaTemplatesTrove": "conary.rpath.com@rpl:2",
             "betaNag": False,
             "bugsUrl": "",
             "maxIsoSize": None,
             "mediaTemplateTrove": "",
             "showMediaCheck": False}))
    platform.addContainerTemplate(imageTypes.Image( \
            {"containerFormat": "vhdImage",
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "freespace": 1024,
             "swapSize": 512,
             "vhdDisktype": "dynamic"}))
    platform.addContainerTemplate(imageTypes.Image( \
            {"containerFormat": "virtualIronImage",
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "freespace": 1024,
             "swapSize": 512,
             "vhdDisktype": "dynamic"}))
    platform.addContainerTemplate(imageTypes.Image( \
            {"containerFormat": "vmwareImage",
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "diskAdapter": "lsilogic",
             "freespace": 1024,
             "natNetworking": True,
             "swapSize": 512,
             "vmMemory": 256,
             "vmSnapshots": False}))
    platform.addContainerTemplate(imageTypes.Image( \
            {"containerFormat": "vmwareEsxImage",
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "freespace": 1024,
             "natNetworking": True,
             "swapSize": 512,
             "vmMemory": 256}))
    platform.addContainerTemplate(imageTypes.Image( \
            {"containerFormat": "xenOvaImage",
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "freespace": 1024,
             "swapSize": 512,
             "vmMemory": 256}))

    platform.addBuildTemplate(name="ami_large",
            displayName="EC2 AMI Large/Huge", architectureRef="x86_64",
            containerTemplateRef="amiImage", flavorSetRef="ami")
    platform.addBuildTemplate(name="ec2_small",
            displayName="EC2 AMI Small", architectureRef="x86",
            containerTemplateRef="amiImage", flavorSetRef="ami")
    platform.addBuildTemplate(name="iso", displayName="ISO",
            architectureRef="x86",
            containerTemplateRef="applianceIsoImage")
    platform.addBuildTemplate(name="iso", displayName="ISO",
            architectureRef="x86",
            containerTemplateRef="installableIsoImage")
    platform.addBuildTemplate(name="iso", displayName="ISO",
            architectureRef="x86",
            containerTemplateRef="updateIsoImage")
    platform.addBuildTemplate(name="iso", displayName="ISO",
            architectureRef="x86_64",
            containerTemplateRef="applianceIsoImage")
    platform.addBuildTemplate(name="iso", displayName="ISO",
            architectureRef="x86_64",
            containerTemplateRef="installableIsoImage")
    platform.addBuildTemplate(name="iso", displayName="ISO",
            architectureRef="x86_64",
            containerTemplateRef="updateIsoImage")
    platform.addBuildTemplate(name="hyper_v",
            displayName="MS Hyper-V", architectureRef="x86",
            containerTemplateRef="vhdImage", flavorSetRef="generic")
    platform.addBuildTemplate(name="hyper_v",
            displayName="MS Hyper-V", architectureRef="x86_64",
            containerTemplateRef="vhdImage", flavorSetRef="generic")
    platform.addBuildTemplate(name="raw_fs",
            displayName="Raw Filesystem", architectureRef="x86",
            containerTemplateRef="rawFsImage")
    platform.addBuildTemplate(name="raw_fs",
            displayName="Raw Filesystem", architectureRef="x86_64",
            containerTemplateRef="rawFsImage")
    platform.addBuildTemplate(name="raw_hd",
            displayName="Raw Hard Disk", architectureRef="x86",
            containerTemplateRef="rawHdImage")
    platform.addBuildTemplate(name="raw_hd",
            displayName="Raw Hard Disk", architectureRef="x86_64",
            containerTemplateRef="rawHdImage")
    platform.addBuildTemplate(name="tar",
            displayName="Tar Image", architectureRef="x86",
            containerTemplateRef="tarballImage")
    platform.addBuildTemplate(name="tar",
            displayName="Tar Image", architectureRef="x86_64",
            containerTemplateRef="tarballImage")
    platform.addBuildTemplate(name="vmware", displayName="VMware",
            architectureRef="x86", containerTemplateRef="vmwareImage",
            flavorSetRef="vmware")
    platform.addBuildTemplate(name="vmware", displayName="VMware",
            architectureRef="x86",
            containerTemplateRef="vmwareEsxImage",
            flavorSetRef="vmware")
    platform.addBuildTemplate(name="vmware", displayName="VMware",
            architectureRef="x86_64",
            containerTemplateRef="vmwareImage",
            flavorSetRef="vmware")
    platform.addBuildTemplate(name="vmware", displayName="VMware",
            architectureRef="x86_64",
            containerTemplateRef="vmwareEsxImage",
            flavorSetRef="vmware")
    platform.addBuildTemplate(name="virtual_iron",
            displayName="Virtual Iron", architectureRef="x86",
            containerTemplateRef="virtualIronImage",
            flavorSetRef="virtual_iron")
    platform.addBuildTemplate(name="virtual_iron",
            displayName="Virtual Iron", architectureRef="x86_64",
            containerTemplateRef="virtualIronImage",
            flavorSetRef="virtual_iron")
    platform.addBuildTemplate(name="xen_ova",
            displayName="Xen OVA",
            architectureRef="x86", containerTemplateRef="xenOvaImage",
            flavorSetRef="xen")
    platform.addBuildTemplate(name="xen_ova",
            displayName="Xen OVA",
            architectureRef="x86_64",
            containerTemplateRef="xenOvaImage",
            flavorSetRef="xen")

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

        if chName == self._makeAbsoluteName('sourceGroup'):
            self.sourceGroup = childNode.getText()
            return

        if chName == self._makeAbsoluteName('baseLabel'):
            self.baseLabel = childNode.getText()
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

        if chName == self._makeAbsoluteName('architectures'):
            children = childNode.getChildren('architecture')
            self._addArchitectures(children)
            return

        if chName == self._makeAbsoluteName('flavorSets'):
            children = childNode.getChildren('flavorSet')
            self._addFlavorSets(children)
            return

        if chName == self._makeAbsoluteName('containerTemplates'):
            children = childNode.getChildren('image')
            self._addContainerTemplates(children)
            return

        if chName == self._makeAbsoluteName('buildTemplates'):
            children = childNode.getChildren('buildTemplate')
            self._addBuildTemplates(children)
            return

        if chName == self._makeAbsoluteName('buildDefinition'):
            children = childNode.getChildren('build')
            self._addBuildDefinition(children)
            return

        if chName == self._makeAbsoluteName('platform'):
            self._addPlatform(childNode)
            return

        if chName == self._makeAbsoluteName('secondaryLabels'):
            self._addSecondaryLabels(childNode)
            return

    def _addStages(self, stagesNodes):
        stages = self.stages = _Stages()
        for node in stagesNodes:
            # XXX getAttribute should be getAbsoluteAttribute
            pyObj = _Stage(name = node.getAttribute('name'),
                           labelSuffix = node.getAttribute('labelSuffix'))
            stages.append(pyObj)
            self._addPromoteMaps(pyObj, node)

    def _addPromoteMaps(self, stage, node):
        """
        Add the promote maps from the node to this stage
        """
        stage.promoteMaps = None
        promoteMaps = _PromoteMaps()
        nodeList = node.getChildren('promoteMaps')
        if not nodeList:
            return
        for pmNode in nodeList[0].getChildren('promoteMap'):
            mapName = pmNode.getAttribute('name')
            mapLabel = pmNode.getAttribute('label')
            promoteMaps.append(PromoteMap(mapName, mapLabel))
        stage.promoteMaps = promoteMaps


    def _addSearchPaths(self, searchPaths):
        self.searchPaths = self._processSearchPaths(searchPaths)

    def _addFactorySources(self, factorySources):
        self.factorySources = self._processFactorySources(factorySources)

    def _addArchitectures(self, architectures):
        self.architectures = self._processArchitectures(architectures)

    def _addFlavorSets(self, flavorSets):
        self.flavorSets = self._processFlavorSets(flavorSets)

    def _addContainerTemplates(self, containerTemplates):
        self.containerTemplates = \
                self._processContainerTemplates(containerTemplates)

    def _addBuildTemplates(self, buildTemplates):
        self.buildTemplates = self._processBuildTemplates(buildTemplates)

    def _addBuildDefinition_1_x(self, buildNodes):
        dispatcher = xmllib.NodeDispatcher(self._nsMap)
        dispatcher.registerClasses(imageTypes, imageTypes.Image)

        builds = self.buildDefinition = _BuildDefinition()
        for node in buildNodes:
            imgType = None
            subNode = None
            legacyImageTypes = ["amiImage", "applianceIsoImage",
            "installableIsoImage", "liveIsoImage", "netbootImage",
            "rawFsImage", "rawHdImage", "tarballImage", "updateIsoImage",
            "vhdImage", "virtualIronImage", "vmwareImage",
            "vmwareEsxImage", "xenOvaImage", ]

            containerTemplateRef = None
            for legacyImageType in legacyImageTypes:
                imgTypes = node.getChildren(legacyImageType)
                if imgTypes:
                    # don't assign the containerFormat to the image, it's an
                    # attribute of the buildDefinition
                    imgType = imageTypes.Image(imgTypes[0])
                    containerTemplateRef = legacyImageType
                    break

            for subNode in node.iterChildren():
                if not isinstance(subNode, xmllib.BaseNode):
                    continue
            if subNode is None:
                # Build node had no children
                continue
            imageGroup = node.getChildren('imageGroup')
            if imageGroup:
                imageGroup = imageGroup[0].getText()
            else:
                imageGroup = None
            baseFlavor = node.getAttribute('baseFlavor')
            flavor = node.getAttribute('flavor')

            flavor = baseFlavor or flavor
            if flavor is not None:
                flavor = str(flavor)

            pyobj = Build(
                name = node.getAttribute('name'),
                image = imgType,
                stages = [ x.getAttribute('ref')
                           for x in node.getChildren('stage') ],
                imageGroup = imageGroup,
                parentImageGroup = self.imageGroup,
                architectureRef = node.getAttribute('architectureRef'),
                containerTemplateRef = containerTemplateRef,
                flavor = flavor,
                )
            builds.append(pyobj)

    def _addBuildDefinition(self, buildNodes):
        # support pre-2.0 schemas
        schemaVersion = self._getSchemaVersion()
        if schemaVersion in ('1.0', '1.1', '1.2', '1.3'):
            return self._addBuildDefinition_1_x(buildNodes)

        dispatcher = xmllib.NodeDispatcher(self._nsMap)
        dispatcher.registerClasses(imageTypes, imageTypes.Image)

        builds = self.buildDefinition = _BuildDefinition()
        for node in buildNodes:
            image = node.getChildren('image')
            image = image and imageTypes.Image(image[0]) or None
            imageGroup = node.getChildren('imageGroup')
            if imageGroup:
                imageGroup = imageGroup[0].getText()
            else:
                imageGroup = None
            sourceGroup = node.getChildren('sourceGroup')
            if sourceGroup:
                sourceGroup = sourceGroup[0].getText()
            else:
                sourceGroup = None
            if hasattr(self, 'sourceGroup'):
                parentSourceGroup = self.sourceGroup
            else:
                parentSourceGroup = None
            pyobj = Build(
                name = node.getAttribute('name'),
                image = image,
                stages = [ x.getAttribute('ref')
                           for x in node.getChildren('stage') ],
                imageGroup = imageGroup,
                parentImageGroup = self.imageGroup,
                sourceGroup = sourceGroup,
                parentSourceGroup = parentSourceGroup, 
                architectureRef = node.getAttribute('architectureRef'),
                flavorSetRef = node.getAttribute('flavorSetRef'),
                containerTemplateRef = \
                        node.getAttribute('containerTemplateRef'),
                flavor = node.getAttribute('flavor'),
                buildTemplateRef = node.getAttribute('buildTemplateRef')
                )
            builds.append(pyobj)

    def _addSecondaryLabels(self, childNode):
        self.secondaryLabels = _SecondaryLabels()
        for node in childNode.getChildren('secondaryLabel'):
            name = node.getAttribute('name')
            label = node.getText()
            self.secondaryLabels.append(SecondaryLabel(name, label))
        return self

    def finalize(self):
        if self._getSchemaVersion() in ('1.0', '1.1', '1.2', '1.3'):
            if not hasattr(self, 'platform'):
                # we're going to need a platform to store references to the
                # containerTemplates, architectures and flavorSets
                self._addPlatform(_PlatformDefinition())

        if hasattr(self, 'platform'):
            # if the XML didn't have one of the 4 attributes here, then
            # it simply won't be present, hence the usage of hasattr
            found = False
            for attr in ('containerTemplates', 'architectures',
                    'buildTemplates', 'flavorSets'):
                if hasattr(self, attr) and getattr(self, attr):
                    found = True
                    break
            if not found and \
                    not self.platform.containerTemplates and \
                    not self.platform.architectures and \
                    not self.platform.buildTemplates and \
                    not self.platform.flavorSets:
                        self.baseFlavor = None
                        _addPlatformDefaults(self.platform)

        if self._getSchemaVersion() in ('1.0', '1.1', '1.2', '1.3'):
            for build in self.buildDefinition:
                if not build.flavor:
                    continue
                flavor = conaryDeps.parseFlavor(build.flavor)

                # we need to use all available information to get our
                # inferences as right as we can. limit our arch and flavorSet
                # guesses to those that are valid in the platform
                matchingTemplates = [x for x in self.platform.buildTemplates \
                        if x.containerTemplateRef == build.containerTemplateRef]
                arches = dict([(x.name, conaryDeps.parseFlavor(x.flavor)) \
                        for x in self.platform.architectures if x.name in \
                        [y.architectureRef for y in matchingTemplates]])
                flavorSets = dict([(x.name, conaryDeps.parseFlavor(x.flavor)) \
                        for x in self.platform.flavorSets if x.name in \
                        [y.flavorSetRef for y in matchingTemplates]])
                if not flavorSets:
                    flavorSets = dict([(x.name, conaryDeps.parseFlavor(x.flavor)) \
                            for x in self.platform.flavorSets])

                def getMajorArch(flv):
                    from conary.deps import arch
                    if flv.members and conaryDeps.DEP_CLASS_IS in flv.members:
                        depClass = flv.members[conaryDeps.DEP_CLASS_IS]
                        return arch.getMajorArch(depClass.getDeps()).name
                    return None

                architectureRef = flavorSetRef = None
                matchingArches = [x for x in arches.iteritems() \
                        if x[1].satisfies(flavor) and \
                        getMajorArch(x[1]) == getMajorArch(flavor)]
                if matchingArches:
                    architectureRef = max([(x[1].score(flavor), x[0]) \
                            for x in matchingArches])[1]
                else:
                    # do what we can to infer the proper arch. this will likely
                    # work for arches currently in the wild
                    depName = getMajorArch(flavor)
                    if depName in arches:
                        architectureRef = depName

                matchingFlavorSets = [x for x in flavorSets.iteritems() \
                        if flavor.satisfies(x[1])]
                if matchingFlavorSets:
                    # strong Flavors is really not optimal, but historical
                    # proddefs used flavors that were too strong,
                    # leading to weird flavors matching over more logical ones
                    # if we just score
                    maxScore = max([flavor.toStrongFlavor().score( \
                            x[1].toStrongFlavor()) for x in matchingFlavorSets])
                    bestFlavors = [x for x in matchingFlavorSets if \
                        flavor.toStrongFlavor().score(x[1].toStrongFlavor()) \
                            == maxScore]
                    if 'generic' in [x[0] for x in bestFlavors]:
                        # if generic made the list, it's very likely the right
                        # flavor to use
                        flavorSetRef = 'generic'
                    else:
                        flavorNames = [x[0] for x in bestFlavors]
                        # Xen and AMI are identical on rPL 2, but only AMI will
                        # be present if it is an amiImage; thus xen is more
                        # dominant.
                        if 'ami' in flavorNames and 'xen' in flavorNames:
                            flavorSetRef = 'xen'
                        else:
                            flavorSetRef = bestFlavors[0][0]

                # RBL-3886 do not preserve flavor during migration. it does
                # more harm than good
                build.flavor = None
                build.architectureRef = architectureRef
                build.flavorSetRef = flavorSetRef

        return self

class _PlatformDefinition(BaseXmlNode):
    def finalize(self):
        self._addPlatform(self)
        if not self.platform.containerTemplates and \
                not self.platform.architectures and \
                not self.platform.buildTemplates and \
                not self.platform.flavorSets:
                    _addPlatformDefaults(self.platform)
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
        self.architectures = platform.architectures

        self.flavorSets = platform.flavorSets
        self.containerTemplates = platform.containerTemplates
        self.buildTemplates = platform.buildTemplates
        self.baseFlavor = xmllib.StringNode(name = 'baseFlavor').characters(platform.baseFlavor)
        self.platformName = platform.platformName
        self.platformVersionTrove = platform.platformVersionTrove
        self.autoLoadRecipes = platform.autoLoadRecipes
        xmllib.BaseNode.__init__(self, attrs, namespaces, name=name)

    def iterChildren(self):
        ret = []
        if self.platformName is not None:
            ret.append(self.platformName)
        if self.platformVersionTrove is not None:
            ret.append(self.platformVersionTrove)
        ret.append(self.baseFlavor)
        if self.searchPaths:
            ret.append(self.searchPaths)
        if self.factorySources:
            ret.append(self.factorySources)
        if self.autoLoadRecipes:
            ret.append(self.autoLoadRecipes)
        if self.architectures:
            ret.append(self.architectures)
        if self.flavorSets:
            ret.append(self.flavorSets)
        if self.containerTemplates:
            ret.append(self.containerTemplates)
        if self.buildTemplates:
            ret.append(self.buildTemplates)
        return ret

class _ProductDefinitionSerialization(xmllib.BaseNode):
    def __init__(self, name, attrs, namespaces, prodDef):
        xmllib.BaseNode.__init__(self, attrs, namespaces, name = name)
        self.stages = prodDef.getStages()
        self.searchPaths = prodDef.searchPaths
        self.factorySources = prodDef.factorySources
        self.architectures = prodDef.architectures
        self.flavorSets = prodDef.flavorSets
        self.containerTemplates = prodDef.containerTemplates
        self.buildTemplates = prodDef.buildTemplates
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

        self.sourceGroup = None
        sourceGroup = prodDef.getSourceGroup()
        if sourceGroup:
            self.sourceGroup = xmllib.StringNode(name = 'sourceGroup')
            self.sourceGroup.characters(sourceGroup)

        self.baseLabel = None
        baseLabel = prodDef.getBaseLabel()
        if baseLabel:
            self.baseLabel = xmllib.StringNode(name = 'baseLabel')
            self.baseLabel.characters(baseLabel)

        self.baseFlavor = xmllib.StringNode(name = 'baseFlavor')
        self.baseFlavor.characters(prodDef.baseFlavor)

        self.secondaryLabels = prodDef.getSecondaryLabels() or None

    def iterChildren(self):
        ret =  [ self.productName,
                 self.productShortname,
                 self.productDescription,
                 self.productVersion,
                 self.productVersionDescription,
                 self.conaryRepositoryHostname,
                 self.conaryNamespace,
                 self.imageGroup,
                 self.sourceGroup,
                 self.baseLabel,
                 self.baseFlavor,
                 self.stages, ]
        if self.searchPaths:
            ret.append(self.searchPaths)
        if len(self.factorySources):
            ret.append(self.factorySources)
        if self.secondaryLabels:
            ret.append(self.secondaryLabels)
        if self.architectures:
            ret.append(self.architectures)
        if self.flavorSets:
            ret.append(self.flavorSets)
        if self.containerTemplates:
            ret.append(self.containerTemplates)
        if self.buildTemplates:
            ret.append(self.buildTemplates)
        ret.append(self.buildDefinition)
        if self.platform:
            ret.append(self.platform)
        return ret
