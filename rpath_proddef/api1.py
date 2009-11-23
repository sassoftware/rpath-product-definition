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
            'SchemaValidationError',
            ]

import itertools
import os
import StringIO
from lxml import etree

from conary import changelog
from conary import errors as conaryErrors
from conary import versions as conaryVersions
from conary.conaryclient import filetypes, cmdline
from conary.deps import deps as conaryDeps
from conary.lib import util
from conary.repository import errors as repositoryErrors

from rpath_proddef import _xmlConstants

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

class SchemaValidationError(ProductDefinitionError):
    "XML document does not validate against the XML schema"

#}

class BaseDefinition(object):
    version = _xmlConstants.version
    Versioned = True
    defaultNamespace = _xmlConstants.defaultNamespaceList[0]
    xmlSchemaLocation = _xmlConstants.xmlSchemaLocation

    schemaDir = "/usr/share/rpath_proddef"

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
        self._validate = validate
        if schemaDir:
            self.schemaDir = schemaDir


        if fromStream:
            self.parseStream(fromStream, validate = validate,
                             schemaDir = schemaDir)

    def parseStream(self, fromStream, validate = False, schemaDir = None):
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

        from xml.dom import minidom
        if isinstance(fromStream, (str, unicode)):
            func = minidom.parseString
        else:
            func = minidom.parse
        doc = func(fromStream)
        rootNode = doc.documentElement
        if rootNode.attributes.has_key('version'):
            version = rootNode.attributes['version'].value.encode('ascii')
        else:
            # XXX default to the current version, hope for the best
            version = self.version
        xmlns = rootNode.attributes.get('xmlns')

        module = self.loadModule(version)

        rootObj = getattr(module, self.ClassFactoryName).factory()
        rootObj.build(rootNode)
        doc.unlink()
        if version != self.version:
            migr = MigrationManager(version)
            rootObj = migr.migrate(rootObj)
        self._rootObj = rootObj
        self._postinit()

    @classmethod
    def loadModule(cls, version):
        moduleName = "xml_%s.subs" % version.replace('.', '_')
        try:
            module = __import__(moduleName, globals(), None, [moduleName])
        except ImportError:
            raise InvalidSchemaVersionError(version)
        return module

    @classmethod
    def getSchemaFile(cls, schemaDir, version):
        schemaFile = os.path.join(schemaDir, "rpd-%s.xsd" % version)
        try:
            file(schemaFile)
        except OSError:
            raise SchemaValidationError("Unable to load schema file %s" % schemaFile)
        return schemaFile

    @classmethod
    def validate(cls, stream, schemaDir, version):
        schemaFile = cls.getSchemaFile(schemaDir, version)
        schema = etree.XMLSchema(file = schemaFile)
        tree = etree.parse(stream)
        if not schema.validate(tree):
            raise SchemaValidationError(str(schema.error_log))
        return tree

    def serialize(self, stream, validate = True):
        """
        Serialize the current object as an XML stream.
        @param stream: stream to write the serialized object
        @type stream: C{file}
        """
        attrs = [
            ('xmlns', self.defaultNamespace),
            ('xmlns:xsi', _xmlConstants.xmlSchemaNamespace),
            ("xsi:schemaLocation", self.xmlSchemaLocation),
        ]
        namespacedef = ' '.join('%s="%s"' % a for a in attrs)

        # Write to a temporary file. We are paranoid and want to verify that
        # the output we produce doesn't break lxml
        bsio = util.BoundedStringIO()
        self._rootObj.export(bsio, 0, namespace_ = '', name_ = self.RootNode,
            namespacedef_ = namespacedef)
        bsio.seek(0)
        if validate and os.path.exists(self.schemaDir):
            tree = self.validate(bsio, self.schemaDir,
                self._rootObj.get_version())
        elif validate:
            import sys
            sys.stderr.write("Warning: unable to validate schema: directory %s missing"
                % self.schemaDir)
            tree = etree.parse(bsio)
        else:
            tree = etree.parse(bsio)
        tree.write(stream, encoding = 'UTF-8', pretty_print = True,
            xml_declaration = True)

    def getBaseFlavor(self):
        """
        @return: the base flavor
        @rtype: C{str}
        """
        return self._rootObj.get_baseFlavor()

    def setBaseFlavor(self, baseFlavor):
        """
        Set the base flavor.
        @param baseFlavor: the base flavor
        @type baseFlavor: C{str}
        """
        self._rootObj.set_baseFlavor(baseFlavor)

    baseFlavor = property(getBaseFlavor, setBaseFlavor)

    def getSearchPaths(self):
        """
        @return: the search paths from this product definition
        @rtype: C{list} of C{_SearchPath} objects
        """

        sp = self._rootObj.get_searchPaths()
        if sp is None:
            return []
        return sp.get_searchPath()

    searchPaths = property(getSearchPaths)

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
        self._rootObj.set_searchPaths(None)

    def getFactorySources(self):
        """
        @return: the factory sources from this product definition
        @rtype: C{list} of C{_FactorySource} objects
        """
        fs = self._rootObj.get_factorySources()
        if fs is None:
            return []
        return fs.get_factorySource()

    factorySources = property(getFactorySources)

    def clearFactorySources(self):
        """
        Delete all factorySources.
        @return: None
        @rtype None
        """
        self._rootObj.set_factorySources(None)

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
        xmlsubs = self.xmlFactory()
        sp = self._rootObj.get_searchPaths()
        if sp is None:
            sp = xmlsubs.searchPathListTypeSub.factory()
            self._rootObj.set_searchPaths(sp)
        self._addSource(troveName, label, version,
                xmlsubs.searchPathTypeSub.factory, sp.add_searchPath,
                isResolveTrove = isResolveTrove,
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
        sp = self._rootObj.get_factorySources()
        xmlsubs = self.xmlFactory()
        if sp is None:
            sp = xmlsubs.factorySourceListTypeSub.factory()
            self._rootObj.set_factorySources(sp)
        self._addSource(troveName, label, version,
            xmlsubs.searchPathTypeSub.factory, sp.add_factorySource)

    def getArchitectures(self):
        """
        @return: all defined architectures for both proddef and platform
        @rtype: C{list}
        """
        vals = self._rootObj.get_architectures()
        if vals is None:
            return []
        return vals.get_architecture()

    architectures = property(getArchitectures)

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
        xmlsubs = self.xmlFactory()
        # Replace architecture with the same name
        arches = self._rootObj.get_architectures()
        if arches is None:
            arches = []
        else:
            arches = arches.get_architecture()
        narches = xmlsubs.architecturesTypeSub.factory()
        for arch in (arches or []):
            if arch.get_name() == name:
                continue
            narches.add_architecture(arch)
        newVal = xmlsubs.nameFlavorTypeSub.factory(name = name,
            displayName = displayName, flavor = flavor)
        narches.add_architecture(newVal)
        self._rootObj.set_architectures(narches)

    def clearArchitectures(self):
        """
        Reset architectures.
        """
        self._rootObj.set_architectures(None)

    def getFlavorSets(self):
        """
        @return: all defined flavor sets
        @rtype: C{list} of FlavorSet objects
        """
        fsets = self._rootObj.get_flavorSets()
        if fsets is None:
            return []
        return fsets.get_flavorSet()

    flavorSets = property(getFlavorSets)

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
        xmlsubs = self.xmlFactory()
        # Replace flavor sets with the same name
        fsets = self._rootObj.get_flavorSets()
        nfsets = xmlsubs.flavorSetsTypeSub.factory()
        for fset in ((fsets and fsets.get_flavorSet()) or []):
            if fset.get_name() == name:
                continue
            nfsets.add_flavorSet(fset)
        newVal = xmlsubs.nameFlavorTypeSub.factory(name = name,
            displayName = displayName, flavor = flavor)
        nfsets.add_flavorSet(newVal)
        self._rootObj.set_flavorSets(nfsets)

    def clearFlavorSets(self):
        """
        Reset flavor sets.
        """
        self._rootObj.set_flavorSets(None)

    def getContainerTemplates(self):
        """
        @return: all defined container templates
        @rtype: C{list} of ContainerTemplate objects
        """
        vals = self._rootObj.get_containerTemplates()
        if vals is None:
            return []
        return vals.get_image()

    containerTemplates = property(getContainerTemplates)

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
        dd a container template.
        @param image: Image
        @type image: C{imageTypes.Image}
        """
        xmlsubs = self.xmlFactory()
        vals = self._rootObj.get_containerTemplates()
        if vals is None:
            vals = xmlsubs.containerTemplatesTypeSub.factory()
            self._rootObj.set_containerTemplates(vals)
        vals.add_image(image)

    def clearContainerTemplates(self):
        """
        Reset container templates.
        """
        self._rootObj.set_containerTemplates(None)

    def getBuildTemplates(self):
        """
        @return: all defined build templates
        @rtype: C{list} of BuildTemplate objects
        """
        vals = self._rootObj.get_buildTemplates()
        if vals is None:
            return []
        return vals.get_buildTemplate()

    buildTemplates = property(getBuildTemplates)

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
        xmlsubs = self.xmlFactory()
        # Replace architecture with the same name
        values = self._rootObj.get_buildTemplates()
        if values is not None:
            values = values.get_buildTemplate()
        nvalues = xmlsubs.buildTemplatesTypeSub.factory()
        for val in (values or []):
            # XXX
            # Don't remove already existing templates, we did not enforce
            # name uniqueness before
            #if arch.get_name() == name:
            #    continue
            nvalues.add_buildTemplate(val)
        newVal = xmlsubs.buildTemplateTypeSub.factory(name = name,
            displayName = displayName, architectureRef = architectureRef,
            containerTemplateRef = containerTemplateRef,
            flavorSetRef = flavorSetRef)
        nvalues.add_buildTemplate(newVal)
        self._rootObj.set_buildTemplates(nvalues)

    def clearBuildTemplates(self):
        """
        Reset build templates.
        """
        self._rootObj.set_buildTemplates(None)

    def imageType(self, name, fields = None):
        """
        Image type factory. Given an image type name, it will instantiate an
        object of the proper type.
        @param name: The name of the image type.
        @type name: C{str}
        @param fields: Fields to initialize the image type object
        @type fields: C{dict}
        """
        xmlsubs = self.xmlFactory()
        fields = fields or {}
        if name is not None:
            fields.setdefault('containerFormat', name)
        # vhdDiskType is special for some reason - mint keeps trying to set it
        # to the empty string
        if fields.get('vhdDiskType') == '':
            del fields['vhdDiskType']
        return xmlsubs.imageTypeSub.factory(**fields)

    @classmethod
    def parseFlavor(cls, flv):
        try:
            return conaryDeps.parseFlavor(flv)
        except RuntimeError, e:
            raise ProductDefinitionError(str(e))

    def _addSource(self, troveName, label, version, factory, addMethod, **kwargs):
        "Internal function for adding a Source"
        if label is not None:
            if isinstance(label, conaryVersions.Label):
                label = str(label)
        obj = factory(troveName = troveName, label = label, version = version,
                **kwargs)
        addMethod(obj)

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

    def xmlFactory(self):
        return self.loadModule(self.version)

    def _initFields(self):
        xmlsubs = self.xmlFactory()
        self._rootObj = getattr(xmlsubs, self.ClassFactoryName)()
        if self.Versioned:
            self._rootObj.set_version(self.version)

    def _postinit(self):
        pass

    def _setDefault(self, field, factory):
        getter = getattr(self._rootObj, 'get_%s' % field)
        vals = getter()
        if vals is not None:
            return vals
        vals = factory.factory()
        setter = getattr(self._rootObj, 'set_%s' % field)
        setter(vals)
        return vals

class ProductDefinition(BaseDefinition):
    """
    Represents the definition of a product.
    @cvar version:
    @type version: C{str}
    @cvar defaultNamespace:
    @type defaultNamespace: C{str}
    @cvar xmlSchemaLocation:
    @type xmlSchemaLocation: C{str}
    @cvar schemaDir: Directory where schema definitions are stored
    @type schemaDir: C{str}
    """
    ClassFactoryName = 'productDefinitionSub'
    RootNode = 'productDefinition'

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
        if not hasattr(obj, '_rootObj'):
            return False
        return self._rootObj.__eq__(obj._rootObj)

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def copy(self):
        outStr = StringIO.StringIO()
        self.serialize(outStr)
        inStr = StringIO.StringIO(outStr.getvalue())
        return ProductDefinition(inStr, schemaDir = self.schemaDir,
            validate = self._validate)

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
        return self._rootObj.get_productName()

    def setProductName(self, productName):
        """
        Set the product name
        @param productName: the product name
        @type productName: C{str}
        """
        self._rootObj.set_productName(productName)

    def getProductDescription(self):
        """
        @return: the product description
        @rtype: C{str}
        """
        return self._rootObj.get_productDescription()

    def setProductDescription(self, productDescription):
        """
        Set the product description
        @param productDescription: the product description
        @type productDescription: C{str}
        """
        self._rootObj.set_productDescription(productDescription)

    def getProductShortname(self):
        """
        @return: the product shortname
        @rtype: C{str}
        """
        return self._rootObj.get_productShortname()

    def setProductShortname(self, productShortname):
        """
        @param productShortname: the product's shortname
        @type productShortname: C{str}
        """
        self._rootObj.set_productShortname(productShortname)

    def getProductVersion(self):
        """
        @return: the product version
        @rtype: C{str}
        """
        return self._rootObj.get_productVersion()

    def setProductVersion(self, productVersion):
        """
        Set the product version
        @param productVersion: the product version
        @type productVersion: C{str}
        """
        self._rootObj.set_productVersion(productVersion)

    def getProductVersionDescription(self):
        """
        @return: the product version description
        @rtype: C{str}
        """
        return self._rootObj.get_productVersionDescription()

    def setProductVersionDescription(self, productVersionDescription):
        """
        Set the product version description
        @param productVersionDescription: the product version description
        @type productVersionDescription: C{str}
        """
        self._rootObj.set_productVersionDescription(productVersionDescription)

    def getConaryRepositoryHostname(self):
        """
        @return: the Conary repository's hostname (e.g. conary.example.com)
        @rtype: C{str}
        """
        return self._rootObj.get_conaryRepositoryHostname()

    def setConaryRepositoryHostname(self, conaryRepositoryHostname):
        """
        Set the Conary repository hostname
        @param conaryRepositoryHostname: the fully-qualified hostname for
           the repository
        @type conaryRepositoryHostname: C{str}
        """
        self._rootObj.set_conaryRepositoryHostname(conaryRepositoryHostname)

    def getConaryNamespace(self):
        """
        @return: the Conary namespace to use for this product
        @rtype: C{str}
        """
        return self._rootObj.get_conaryNamespace()

    def setConaryNamespace(self, conaryNamespace):
        """
        Set the Conary namespace
        @param conaryNamespace: the Conary namespace
        @type conaryNamespace: C{str}
        """
        self._rootObj.set_conaryNamespace(conaryNamespace)

    def getSourceGroup(self):
        """
        @return: the source group, if none is set, default to the image group
        @rtype: C{str}
        """
        return self._rootObj.get_sourceGroup()

    def setSourceGroup(self, sourceGroup):
        """
        Set the source group name
        @param sourceGroup: the image group name
        @type sourceGroup: C{str}
        """
        self._rootObj.set_sourceGroup(sourceGroup)

    def getImageGroup(self):
        """
        @return: the image group
        @rtype: C{str}
        """
        # XXX Old code relied on the image group being None, not empty string
        return self._rootObj.get_imageGroup() or None

    def setImageGroup(self, imageGroup):
        """
        Set the image group name
        @param imageGroup: the image group name
        @type imageGroup: C{str}
        """
        self._rootObj.set_imageGroup(imageGroup)

    def getBaseFlavor(self):
        """
        @return: the base flavor
        @rtype: C{str}
        """
        flv = conaryDeps.parseFlavor('')
        platFlv = self.getPlatformBaseFlavor()
        if platFlv is not None:
            nflv = self.parseFlavor(platFlv)
            flv = conaryDeps.overrideFlavor(flv, nflv)
        bf = BaseDefinition.getBaseFlavor(self)
        if bf is not None:
            nflv = self.parseFlavor(bf)
            flv = conaryDeps.overrideFlavor(flv, nflv)
        return str(flv)

    # self.baseFlavor will refer to the flavor of the product, as defined, not
    # the one inherited from the platform.
    # This line is commented out because we inherit the base flavor from the
    # parent object.
    #baseFlavor = property(BaseDefinition.getBaseFlavor, BaseDefinition.setBaseFlavor)

    def getStages(self):
        """
        @return: the stages from this product definition
        @rtype: C{list} of C{_Stage} objects
        """
        stages = self._rootObj.get_stages()
        if stages is None:
            return []
        return stages.get_stage()

    stages = property(getStages)

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
        xmlsubs = self.xmlFactory()
        stages = self._setDefault('stages', xmlsubs.stageListTypeSub)
        if promoteMaps is None:
            nvals = None
        else:
            nvals = xmlsubs.promoteMapsTypeSub.factory()
            for pm in promoteMaps:
                if isinstance(pm, tuple):
                    pm = xmlsubs.promoteMapTypeSub.factory(name = pm[0],
                        label = pm[1])
                nvals.add_promoteMap(pm)
        stages.add_stage(xmlsubs.stageTypeSub.factory(
            name = name, labelSuffix = labelSuffix,
            promoteMaps = nvals))

    def clearStages(self):
        """
        Delete all stages.
        @return: None
        @rtype None
        """
        self._rootObj.set_stages(None)

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
        secondaryLabels = self.getSecondaryLabels()
        if not secondaryLabels:
            return []
        prefix = self.getProductDefinitionLabel()
        labelSuffix = stageObj.labelSuffix or '' # this can be blank

        ret = []
        for sl in secondaryLabels:
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
        secondaryLabels = self.getSecondaryLabels()
        if secondaryLabels:
            fromSuffix = fromStageObj.labelSuffix
            toSuffix = toStageObj.labelSuffix
            for secondaryLabel in secondaryLabels:
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
        sp = BaseDefinition.getSearchPaths(self)
        if sp:
            return sp
        return self.getPlatformSearchPaths()

    def getResolveTroves(self):
        """
        @return: the search paths from this product definition, filtering
                 any results that have isResolveTrove set to false. This
                 is a subset of the results from getSearchPaths
        @rtype: C{list} of C{_SearchPath} objects
        """
        searchPaths = self.getSearchPaths()
        if not searchPaths:
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
        searchPaths = BaseDefinition.getGroupSearchPaths(self)
        if not searchPaths and self.platform:
            searchPaths = self.platform.getGroupSearchPaths()
        searchPaths = [x for x in (searchPaths or [])
                       if x.isGroupSearchPathTrove
                          or x.isGroupSearchPathTrove is None]
        return searchPaths

    def getFactorySources(self):
        """
        @return: the factory sources from this product definition
        @rtype: C{list} of C{_FactorySource} objects
        """
        fs = BaseDefinition.getFactorySources(self)
        if fs:
            return fs
        return self.getPlatformFactorySources()

    def getBuildDefinitions(self):
        """
        @return: The build definitions from this product definition
        @rtype: C{list} of C{Build} objects
        """
        bd = self._rootObj.get_buildDefinition()
        if bd is None:
            return []
        return bd.get_build()

    buildDefinition = property(getBuildDefinitions)

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
        xmlsubs = self.xmlFactory()
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

        obj = xmlsubs.buildTypeSub.factory(name = name, image = image,
                imageGroup = imageGroup,
                sourceGroup = sourceGroup,
                architectureRef = architectureRef,
                containerTemplateRef = containerTemplateRef,
                flavorSetRef = flavorSetRef)
        obj.parentImageGroup = self.getImageGroup()
        obj.parentSourceGroup = self.getSourceGroup()
        obj.buildFlavor = self._getFlavorByRefs(flavorSetRef,
            architectureRef, buildTemplateRef, flavor)
        obj.containerTemplateFields = self._getBuildContainerTemplateFields(
            containerTemplateRef)
        for stage in (stages or []):
            obj.add_stage(xmlsubs.stageSub.factory(ref = stage))
        bdef = self._setDefault('buildDefinition', xmlsubs.buildDefinitionTypeSub)
        bdef.add_build(obj)

    def clearBuildDefinition(self):
        """
        Delete all buildDefinition.
        @return: None
        @rtype None
        """
        self._rootObj.set_buildDefinition(None)

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
        self.platform.clearSearchPaths()

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
        self._ensurePlatformExists()
        self.platform.addSearchPath(troveName = troveName, label = label,
            version = version, isResolveTrove = isResolveTrove,
            isGroupSearchPathTrove = isGroupSearchPathTrove)

    def getPlatformFactorySources(self):
        """
        @return: the factory sources from this product definition
        @rtype: C{list} of C{_FactorySource} objects
        """
        if self.platform is None:
            return []
        return self.platform.getFactorySources()

    def clearPlatformFactorySources(self):
        """
        Delete all factorySources.
        @return: None
        @rtype None
        """
        if self.platform is None:
            return
        self.platform.clearFactorySources()

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
        self._ensurePlatformExists()
        self.platform.addFactorySource(troveName = troveName, label = label,
            version = version)

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
        return self.platform.getBaseFlavor()

    def setPlatformBaseFlavor(self, baseFlavor):
        """
        Set the platform's base flavor.
        @param baseFlavor: A flavor for the platform.
        @type baseFlavor: C{str}
        """
        self._ensurePlatformExists()
        self.platform.setBaseFlavor(baseFlavor)

    def getPlatformSourceTrove(self):
        """
        @return: the source trove the for platform
        @rtype: C{str}
        """
        if self.platform is None:
            return None
        return self.platform.getPlatformSourceTrove()

    def setPlatformSourceTrove(self, sourceTrove):
        """
        Set the platform's source trove.
        @param sourceTrove: the source trove name for the platform
        @type sourceTrove: C{str}
        """
        self._ensurePlatformExists()
        self.platform.setPlatformSourceTrove(sourceTrove)

    def getPlatformUseLatest(self):
        """
        @return: the platform's useLatest flag.
        @rtype: C{bool} or None
        """
        if self.platform is None:
            return None
        return self.platform.getPlatformUseLatest()

    def setPlatformUseLatest(self, useLatest):
        """
        Set the platform's useLatest flag.
        @param useLatest: value for useLatest flag
        @type useLatest: C{bool}
        """
        self._ensurePlatformExists()
        self.platform.setPlatformUseLatest(useLatest)

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

    def getPlatformBuildTemplates(self):
        if self.platform is None:
            return []
        return self.platform.getBuildTemplates()

    def iterAllBuildTemplates(self):
        return itertools.chain(self.getBuildTemplates(),
                               self.getPlatformBuildTemplates())

    def addSecondaryLabel(self, name, label):
        """
        Add a secondary label to the product definition.
        @param name: Name for the secondary label
        @type name: C{str}
        @param label: Label for the secondary label
        @type label: C{str}
        """
        xmlsubs = self.xmlFactory()
        labels = self._setDefault('secondaryLabels',
            xmlsubs.secondaryLabelsTypeSub)
        labels.add_secondaryLabel(xmlsubs.secondaryLabelSub(
            name = name, valueOf_ = label))
        return self

    def getSecondaryLabels(self):
        """
        @return: the seconary labels for this product definition.
        @rtype: C{list}
        """
        vals = self._rootObj.get_secondaryLabels()
        if vals is None:
            return []
        return vals.get_secondaryLabel()

    def clearSecondaryLabels(self):
        """
        Reset secondary label list.
        """
        self._rootObj.set_secondaryLabels(None)

    def _ensurePlatformExists(self):
        if self.platform is None:
            self.platform = Platform()
            self._rootObj.set_platform(self.platform._rootObj)

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
            if stageName in build.getBuildStages():
                ret.append(build)
        return ret

    def setBaseLabel(self, label):
        """
        Set the base label for this product definition.
        @param label: Value for the base label.
        @type label: C{str}
        """
        self._rootObj.set_baseLabel(label)

    def getBaseLabel(self):
        """
        @return: the base label for this product definition.
        @rtype: C{str}
        """
        return self._rootObj.get_baseLabel()

    def getProductDefinitionLabel(self):
        """
        Method that returns the product definition's label
        @return: a Conary label string
        @rtype: C{str}
        @raises MissingInformationError: if there isn't enough information
            in the product definition to generate the label
        """
        baseLabel = self.getBaseLabel()
        if baseLabel:
            return baseLabel

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
        # Create a new platform
        xmlsubs = self.xmlFactory()
        self.platform = Platform()
        uroot = nplat._rootObj
        platobj = xmlsubs.platformTypeSub.factory(
            platformName = uroot.get_platformName(),
            platformVersionTrove = uroot.get_platformVersionTrove(),
            sourceTrove = nplat.getPlatformSourceTrove(),
            useLatest = useLatest,
            baseFlavor = uroot.get_baseFlavor(),
            searchPaths = uroot.get_searchPaths(),
            factorySources = uroot.get_factorySources(),
            autoLoadRecipes = uroot.get_autoLoadRecipes(),
            architectures = uroot.get_architectures(),
            flavorSets = uroot.get_flavorSets(),
            containerTemplates = uroot.get_containerTemplates(),
            buildTemplates = uroot.get_buildTemplates(),
            )
        self._rootObj.set_platform(platobj)
        self.platform._rootObj = platobj
        self._postinit()

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

    def _getFlavorByRefs(self, flavorSetRef, architectureRef,
            buildTemplateRef, extraFlavor):
        # Grab base flavor from platform + product
        flv = self.parseFlavor(self.getBaseFlavor())

        if buildTemplateRef:
            buildTemplate = self.getBuildTemplate(buildTemplateRef, None)
            if not buildTemplate:
                buildTemplate = self.getPlatformBuildTemplate(buildTemplateRef)
            if not architectureRef:
                architectureRef = buildTemplate.architectureRef
            if not flavorSetRef:
                flavorSetRef = buildTemplate.flavorSetRef
        if flavorSetRef:
            methods = [ self.getPlatformFlavorSet, self.getFlavorSet ]
            for meth in methods:
                obj = meth(flavorSetRef, None)
                if obj is None:
                    continue
                nflv = self.parseFlavor(obj.flavor)
                flv = conaryDeps.overrideFlavor(flv, nflv)
        if architectureRef:
            methods = [ self.getPlatformArchitecture, self.getArchitecture ]
            for meth in methods:
                obj = meth(architectureRef, None)
                if obj is None:
                    continue
                nflv = self.parseFlavor(obj.flavor)
                flv = conaryDeps.overrideFlavor(flv, nflv)
        if extraFlavor:
            nflv = self.parseFlavor(extraFlavor)
            flv = conaryDeps.overrideFlavor(flv, nflv)
        return str(flv)

    def _getBuildContainerTemplateFields(self, containerTemplateRef):
        tmpl = self.getContainerTemplate(containerTemplateRef, None)
        if not tmpl:
            tmpl = self.getPlatformContainerTemplate(containerTemplateRef,
                None)
        # if we didn't find the container, the previous function would raise
        # an exeption
        fields = {}
        if tmpl:
            fields['containerFormat'] = tmpl.containerFormat
            fields.update(tmpl.getFields())

        return fields

    def _initFields(self):
        BaseDefinition._initFields(self)
        self.platform = None

    def _postinit(self):
        platform = self._rootObj.get_platform()
        if platform is None:
            self.platform = None
        else:
            self.platform = Platform()
            self.platform._rootObj = platform
        # Pass some parent information into the build objects
        for build in self.getBuildDefinitions():
            build.parentImageGroup = self.getImageGroup()
            build.parentSourceGroup = self.getSourceGroup()
            build.buildFlavor = self._getFlavorByRefs(build.flavorSetRef,
                build.architectureRef, None, None)
            build.containerTemplateFields = self._getBuildContainerTemplateFields(build.containerTemplateRef)

        # Adding the platform was part of the migration from 1.3 to 2.0
        if self.platform:
            self._addPlatformDefaults()

    def _addPlatformDefaults(self):
        fields = ['containerTemplates', 'architectures',
                  'buildTemplates', 'flavorSets']
        for field in fields:
            if getattr(self, field) or getattr(self.platform, field):
                return
        # the fields were not set in the platform or product
        _addPlatformDefaults(self.platform)

    #}

class BasePlatform(BaseDefinition):
    """
    Base platform node. This corresponds to the common data between
    platformType and platformDefinitionType
    """
    def getPlatformName(self):
        """
        @return: The platform name.
        @rtype: C{str}
        """
        return self._rootObj.get_platformName()

    def setPlatformName(self, platformName):
        """
        Set the platform name.
        @param platformName: The platform name.
        @type platformName: C{str}
        """
        return self._rootObj.set_platformName(platformName)

    def getPlatformVersionTrove(self):
        """
        @return: the platform version trove.
        @rtype: C{str}
        """
        return self._rootObj.get_platformVersionTrove()

    def setPlatformVersionTrove(self, troveSpec):
        """
        Set the platform version trove.
        @param troveSpec: The platform version trove
        @type platformName: C{str}
        """
        self._rootObj.set_platformVersionTrove(troveSpec)

    def clearAutoLoadRecipes(self):
        """
        Clear the list of auto load recipes for the platform
        """
        self._rootObj.set_autoLoadRecipes(None)

    def addAutoLoadRecipe(self, troveName = None, label = None):
        """
        Add an auto load recipe
        @param troveName: Trove name
        @type troveName: C{str}
        @param label: Label for the trove
        @type label: C{str}
        """
        xmlsubs = self.xmlFactory()
        vals = self._setDefault('autoLoadRecipes', xmlsubs.autoLoadRecipesTypeSub)
        vals.add_autoLoadRecipe(xmlsubs.nameLabelTypeSub.factory(
            troveName = troveName, label = label))

    def getAutoLoadRecipes(self):
        """
        @return: auto load recipes.
        @rtype: C{list} of C{AutoLoadRecipe}
        """
        vals = self._rootObj.get_autoLoadRecipes()
        if vals is None:
            return []
        return vals.get_autoLoadRecipe()

class Platform(BasePlatform):
    ClassFactoryName = 'platformTypeSub'
    RootNode = 'platform'
    Versioned = False

    _troveName = None

    def getPlatformUseLatest(self):
        """
        @return: the platform version trove.
        @rtype: C{bool}
        """
        return self._rootObj.get_useLatest()

    def setPlatformUseLatest(self, useLatest):
        """
        @return: the platform version trove.
        @rtype: C{bool}
        """
        return self._rootObj.set_useLatest(useLatest)

    def getPlatformSourceTrove(self):
        """
        @return: the platform source trove.
        @rtype: C{str}
        """
        return self._rootObj.get_sourceTrove()

    def setPlatformSourceTrove(self, troveSpec):
        """
        Set the platform source trove.
        @param troveSpec: The platform source trove
        @type platformName: C{str}
        """
        self._rootObj.set_sourceTrove(troveSpec)

    sourceTrove = property(getPlatformSourceTrove, setPlatformSourceTrove)

class PlatformDefinition(BasePlatform):
    ClassFactoryName = 'platformDefinitionTypeSub'
    RootNode = 'platformDefinition'

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
        self._sourceTrove = "%s=%s" % (self._troveName, nvf[1])

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

    # sourceTrove is set when we load the trove from the repository. It is not
    # part of the XML stream, so we set it separately in this object.
    # It will, however, become part of the XML stream for Platform objects.

    def getPlatformSourceTrove(self):
        return self._sourceTrove

    def setPlatformSourceTrove(self, sourceTrove):
        self._sourceTrove = sourceTrove

    sourceTrove = property(getPlatformSourceTrove, setPlatformSourceTrove)

    def _initFields(self):
        BasePlatform._initFields(self)
        self._sourceTrove = None

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

    platform.addContainerTemplate(platform.imageType("amiImage",
            {
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "amiHugeDiskMountpoint": False,
             "freespace": 1024,
             "swapSize": 1024}))
    platform.addContainerTemplate(platform.imageType("applianceIsoImage",
            {
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
    platform.addContainerTemplate(platform.imageType("installableIsoImage",
            {
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
    platform.addContainerTemplate(platform.imageType("netbootImage",
            {
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": ""}))
    platform.addContainerTemplate(platform.imageType("rawFsImage",
            {
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "freespace": 1024,
             "swapSize": 512}))
    platform.addContainerTemplate(platform.imageType("rawHdImage",
            {
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "freespace": 1024,
             "swapSize": 512}))
    platform.addContainerTemplate(platform.imageType("tarballImage",
            {
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "swapSize": "0"}))
    platform.addContainerTemplate(platform.imageType("updateIsoImage",
            {
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
    platform.addContainerTemplate(platform.imageType("vhdImage",
            {
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "freespace": 1024,
             "swapSize": 512,
             "vhdDiskType": "dynamic"}))
    platform.addContainerTemplate(platform.imageType("virtualIronImage",
            {
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "freespace": 1024,
             "swapSize": 512,
             "vhdDiskType": "dynamic"}))
    platform.addContainerTemplate(platform.imageType("vmwareImage",
            {
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "diskAdapter": "lsilogic",
             "freespace": 1024,
             "natNetworking": True,
             "swapSize": 512,
             "vmMemory": 256,
             "vmSnapshots": False}))
    platform.addContainerTemplate(platform.imageType("vmwareEsxImage",
            {
             "autoResolve": False,
             "baseFileName": "",
             "installLabelPath": "",
             "freespace": 1024,
             "natNetworking": True,
             "swapSize": 512,
             "vmMemory": 256}))
    platform.addContainerTemplate(platform.imageType("xenOvaImage",
            {
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

def getMajorArch(flv):
    from conary.deps import arch
    if flv.members and conaryDeps.DEP_CLASS_IS in flv.members:
        depClass = flv.members[conaryDeps.DEP_CLASS_IS]
        return arch.getMajorArch(depClass.getDeps()).name
    return None

def _convertBuildTemplate(fromObj, proddef, build):
    # we need to use all available information to get our
    # inferences as right as we can. limit our arch and flavorSet
    # guesses to those that are valid in the platform
    legacyImageTypes = [ x.name for x in build.member_data_items_
        if x.name.endswith('Image') ]
    vals = [ x for x in legacyImageTypes if getattr(build, x, None) ]
    if vals:
        containerTemplateRef = vals[0]
    else:
        containerTemplateRef = None

    matchingTemplates = [x for x in proddef.platform.buildTemplates
            if x.containerTemplateRef == containerTemplateRef ]

    flavor = build.baseFlavor or build.flavor
    if not flavor:
        return (build.architectureRef, None, containerTemplateRef)

    flavor = BaseDefinition.parseFlavor(flavor)
    matchingArchRefs = set(x.architectureRef for x in matchingTemplates)
    matchingFlavorSetRefs = set(x.flavorSetRef for x in matchingTemplates
        if x.flavorSetRef)
    arches = dict((x.name, BaseDefinition.parseFlavor(x.flavor))
            for x in proddef.platform.architectures
            if x.name in matchingArchRefs)
    allFlavorSets = [ (x.name, BaseDefinition.parseFlavor(x.flavor))
                for x in proddef.platform.flavorSets ]
    flavorSets = dict((name, flv)
            for (name, flv) in allFlavorSets
            if name in matchingFlavorSetRefs)
    if not flavorSets:
        flavorSets = dict(allFlavorSets)

    architectureRef = flavorSetRef = None
    matchingArches = [ x for x in arches.iteritems()
            if x[1].satisfies(flavor) and 
                getMajorArch(x[1]) == getMajorArch(flavor) ]
    if matchingArches:
        architectureRef = max((x[1].score(flavor), x[0])
                for x in matchingArches)[1]
    else:
        # do what we can to infer the proper arch. this will likely
        # work for arches currently in the wild
        depName = getMajorArch(flavor)
        if depName in arches:
            architectureRef = depName

    matchingFlavorSets = [x for x in flavorSets.iteritems()
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
        bestFlavorNames = set(x[0] for x in bestFlavors)
        if 'generic' in bestFlavorNames:
            # if generic made the list, it's very likely the right
            # flavor to use
            flavorSetRef = 'generic'
        else:
            flavorNames = bestFlavorNames
            # Xen and AMI are identical on rPL 2, but only AMI will
            # be present if it is an amiImage; thus xen is more
            # dominant.
            if 'ami' in flavorNames and 'xen' in flavorNames:
                flavorSetRef = 'xen'
            else:
                flavorSetRef = bestFlavors[0][0]

    # RBL-3886 do not preserve flavor during migration. it does
    # more harm than good
    return (architectureRef, flavorSetRef, containerTemplateRef)

def _convertBuildTemplates(fromObj, proddef, newModule):
    bdef = fromObj.get_buildDefinition()
    if bdef is None:
        return
    bdef = bdef.get_build()
    nbdef = proddef.getBuildDefinitions()

    for build, nbuild in zip(bdef, nbdef):
        ret = _convertBuildTemplate(fromObj, proddef, build)
        architectureRef, flavorSetRef, containerTemplateRef = ret
        nbuild.architectureRef = architectureRef
        nbuild.flavorSetRef = flavorSetRef
        nbuild.containerTemplateRef = containerTemplateRef

class MigrationManager(object):
    __slots__ = [ '_version', '_path' ]
    _transitions = {}
    CurrentVersion = BaseDefinition.version

    @classmethod
    def register(cls, klass):
        vals = cls._transitions.setdefault(klass.fromVersion, {})
        vals = vals.setdefault(klass.toVersion, [])
        vals.append(klass)

    def __init__(self, version):
        """Migration from the specified version"""
        # Look for a way to get to the latest version
        v = version
        path = [ v ]
        while v != self.CurrentVersion:
            if v not in self._transitions:
                raise RuntimeError("Unable to migrate")
            v = self._transitions[v].keys()[0]
            path.append(v)
        self._version = version
        self._path = path

    def migrate(self, rootObj):
        if self._version == self.CurrentVersion:
            return rootObj
        v = self._path.pop(0)
        className = rootObj.__class__.__name__
        while self._path:
            nv = self._path.pop(0)
            transitions = self._transitions[v][nv]
            for MigrateClass in transitions:
                module = BaseDefinition.loadModule(nv)
                rootObj = MigrateClass().migrate(rootObj, module)
                rootObj.version = nv
            v = nv
        return rootObj


class BaseMigration(object):
    fromVersion = None
    toVersion = None

    skipFields = set()
    reinitFields = set()

    def migrate(self, fromObj, newModule):
        toObj = self.copyFrom(fromObj, newModule)
        if fromObj.__class__.__name__ == 'platformDefinitionTypeSub':
            method = self.migratePlatform
        else:
            method = self.migrateProduct
        self.migrateCommon(fromObj, toObj, newModule)
        method(fromObj, toObj, newModule)
        return toObj

    def migrateCommon(self, fromObj, toObj, newModule):
        pass

    def migratePlatform(self, fromObj, toObj, newModule):
        pass

    def migrateProduct(self, fromObj, toObj, newModule):
        pass

    @classmethod
    def copyFrom(cls, fromObj, newModule):
        objName = fromObj.__class__.__name__
        if not hasattr(newModule, objName):
            return None

        toObj = getattr(newModule, fromObj.__class__.__name__)()
        newMemberItems = set(x.name for x in toObj.member_data_items_)
        for field in fromObj.member_data_items_:
            fieldName = field.name
            if fieldName not in newMemberItems:
                # This field does not exist in the destination module, we'll
                # have to handle it in a special way
                continue
            if fieldName in cls.skipFields:
                continue
            val = getattr(fromObj, fieldName)
            if fieldName in cls.reinitFields:
                if val is None:
                    continue
                val = getattr(newModule, val.__class__.__name__)()
            elif isinstance(val, list):
                if not val:
                    # Empty list
                    continue
                # Lists should be homogenous at this point
                if hasattr(val[0], 'member_data_items_'):
                    nval = [ cls.copyFrom(x, newModule) for x in val ]
                    val = [ x for x in nval if x is not None ]
            elif hasattr(val, 'member_data_items_'):
                val = cls.copyFrom(val, newModule)
                if val is None:
                    # This field does not exist in the new schema
                    continue
            # Add the new object
            setattr(toObj, fieldName, val)
        return toObj


class Migrate_10_11(BaseMigration):
    fromVersion = '1.0'
    toVersion = '1.1'

    def migrateCommon(self, fromObj, toObj, newModule):
        self._migrateSearchPaths(fromObj, toObj, newModule)

    def _migrateSearchPaths(self, fromObj, toObj, newModule):
        searchPaths = fromObj.get_upstreamSources()
        if not searchPaths:
            return
        searchPaths = searchPaths.get_upstreamSource()
        if not searchPaths:
            return
        newSearchPaths = newModule.searchPathListTypeSub()
        for sp in searchPaths:
            nsp = newModule.searchPathTypeSub(troveName = sp.troveName,
                label = sp.label)
            newSearchPaths.add_searchPath(nsp)
        toObj.set_searchPaths(newSearchPaths)

MigrationManager.register(Migrate_10_11)


class Migrate_11_12(BaseMigration):
    fromVersion = '1.1'
    toVersion = '1.2'

    def migrateProduct(self, fromObj, toObj, newModule):
        self._migratePlatformSource(fromObj, toObj, newModule)
        self._migrateBuildFlavor(fromObj, toObj, newModule)

    def _migratePlatformSource(self, fromObj, toObj, newModule):
        platform = fromObj.get_platform()
        if not platform:
            return
        sourceTrove = platform.get_source()
        toObj.get_platform().set_sourceTrove(sourceTrove)

    def _migrateBuildFlavor(self, fromObj, toObj, newModule):
        builds = toObj.get_buildDefinition()
        if not builds:
            return
        builds = builds.get_build()
        for build in builds:
            build.flavor = build.baseFlavor
            build.baseFlavor = None

MigrationManager.register(Migrate_11_12)


class Migrate_12_13(BaseMigration):
    fromVersion = '1.2'
    toVersion = '1.3'

MigrationManager.register(Migrate_12_13)


class Migrate_13_20(BaseMigration):
    fromVersion = '1.3'
    toVersion = '2.0'

    def migrateProduct(self, fromObj, toObj, newModule):
        pd = ProductDefinition()
        pd._rootObj = toObj
        plat = pd.platform = Platform()
        # XXX this seems fragile. We need to set the version, so xmlFactory
        # loads the proper module
        plat.version = self.toVersion

        platobj = toObj.get_platform()
        plat._rootObj = platobj
        if platobj is None:
            platobj = newModule.platformTypeSub()
            toObj.set_platform(platobj)
            plat._rootObj = platobj
        pd._addPlatformDefaults()

        _convertBuildTemplates(fromObj, pd, newModule)

MigrationManager.register(Migrate_13_20)


class Migrate_20_30(BaseMigration):
    fromVersion = '2.0'
    toVersion = '3.0'

    def _migrateContainerTemplates(self, fromObj, toObj):
        containerTemplates = fromObj.get_containerTemplates()
        if not containerTemplates:
            return
        cTemplFrom = containerTemplates.get_image()
        cTemplTo = toObj.get_containerTemplates().get_image()
        for oldImg, newImg in zip(cTemplFrom, cTemplTo):
            obsoleteVal = oldImg.amiHugeDiskMountPoint
            if obsoleteVal and not newImg.amiHugeDiskMountpoint:
                newImg.amiHugeDiskMountpoint = obsoleteVal
            obsoleteVal = oldImg.vhdDisktype
            if obsoleteVal and not newImg.vhdDiskType:
                newImg.vhdDiskType = obsoleteVal

    def _migrateBuildDefinitions(self, fromObj, toObj):
        buildDefinitions = toObj.get_buildDefinition()
        if not buildDefinitions:
            return
        buildDefinitions = buildDefinitions.get_build()
        for bd in buildDefinitions:
            if bd.containerTemplateRef == 'netBootImage':
                bd.containerTemplateRef = 'netbootImage'
            if bd.image and bd.image.vhdDiskType == '':
                bd.image.vhdDiskType = None

    def migrateCommon(self, fromObj, toObj, newModule):
        self._migrateContainerTemplates(fromObj, toObj)

    def migrateProduct(self, fromObj, toObj, newModule):
        platobj = fromObj.get_platform()
        if platobj:
            self._migrateContainerTemplates(platobj, toObj.get_platform())
        self._migrateBuildDefinitions(fromObj, toObj)

MigrationManager.register(Migrate_20_30)
