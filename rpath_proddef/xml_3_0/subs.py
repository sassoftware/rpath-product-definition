#!/usr/bin/env python

#
# Generated  by generateDS.py.
#

import sys
from string import lower as str_lower
from xml.dom import minidom
from xml.sax import handler, make_parser

import supers as supermod

#
# Globals
#

ExternalEncoding = 'utf-8'

#
# Data representation classes
#

class stageTypeSub(supermod.stageType):
    def __init__(self, labelSuffix=None, name=None, promoteMaps=None):
        supermod.stageType.__init__(self, labelSuffix, name, promoteMaps)
supermod.stageType.subclass = stageTypeSub
# end class stageTypeSub


class stageListTypeSub(supermod.stageListType):
    def __init__(self, stage=None):
        supermod.stageListType.__init__(self, stage)
supermod.stageListType.subclass = stageListTypeSub
# end class stageListTypeSub


class nameLabelTypeSub(supermod.nameLabelType):
    def __init__(self, troveName=None, label=None, valueOf_=''):
        supermod.nameLabelType.__init__(self, troveName, label, valueOf_)
supermod.nameLabelType.subclass = nameLabelTypeSub
# end class nameLabelTypeSub


class searchPathTypeSub(supermod.searchPathType):
    def __init__(self, isGroupSearchPathTrove=None, troveName=None, version=None, isResolveTrove=None, label=None, valueOf_=''):
        supermod.searchPathType.__init__(self, isGroupSearchPathTrove, troveName, version, isResolveTrove, label, valueOf_)
supermod.searchPathType.subclass = searchPathTypeSub
# end class searchPathTypeSub


class searchPathListTypeSub(supermod.searchPathListType):
    def __init__(self, searchPath=None):
        supermod.searchPathListType.__init__(self, searchPath)
supermod.searchPathListType.subclass = searchPathListTypeSub
# end class searchPathListTypeSub


class factorySourceListTypeSub(supermod.factorySourceListType):
    def __init__(self, factorySource=None):
        supermod.factorySourceListType.__init__(self, factorySource)
supermod.factorySourceListType.subclass = factorySourceListTypeSub
# end class factorySourceListTypeSub


class autoLoadRecipesTypeSub(supermod.autoLoadRecipesType):
    def __init__(self, autoLoadRecipe=None):
        supermod.autoLoadRecipesType.__init__(self, autoLoadRecipe)
supermod.autoLoadRecipesType.subclass = autoLoadRecipesTypeSub
# end class autoLoadRecipesTypeSub


class buildDefinitionTypeSub(supermod.buildDefinitionType):
    def __init__(self, build_=None):
        supermod.buildDefinitionType.__init__(self, build_)
supermod.buildDefinitionType.subclass = buildDefinitionTypeSub
# end class buildDefinitionTypeSub


class imageTypeSub(supermod.imageType):
    def __init__(self, autoResolve=None, maxIsoSize=None, bugsUrl=None, natNetworking=None, vhdDiskType=None, anacondaCustomTrove=None, mediaTemplateTrove=None, baseFileName=None, vmSnapshots=None, swapSize=None, betaNag=None, anacondaTemplatesTrove=None, vmMemory=None, installLabelPath=None, unionfs=None, containerFormat=None, freespace=None, name=None, zisofs=None, diskAdapter=None, amiHugeDiskMountpoint=None, showMediaCheck=None, valueOf_=''):
        supermod.imageType.__init__(self, autoResolve, maxIsoSize, bugsUrl, natNetworking, vhdDiskType, anacondaCustomTrove, mediaTemplateTrove, baseFileName, vmSnapshots, swapSize, betaNag, anacondaTemplatesTrove, vmMemory, installLabelPath, unionfs, containerFormat, freespace, name, zisofs, diskAdapter, amiHugeDiskMountpoint, showMediaCheck, valueOf_)
supermod.imageType.subclass = imageTypeSub
# end class imageTypeSub


class buildTypeSub(supermod.buildType):
    def __init__(self, containerTemplateRef=None, architectureRef=None, name=None, flavorSetRef=None, image=None, stage=None, imageGroup=None, sourceGroup=None):
        supermod.buildType.__init__(self, containerTemplateRef, architectureRef, name, flavorSetRef, image, stage, imageGroup, sourceGroup)
supermod.buildType.subclass = buildTypeSub
# end class buildTypeSub


class stageSub(supermod.stage):
    def __init__(self, ref=None, valueOf_=''):
        supermod.stage.__init__(self, ref, valueOf_)
supermod.stage.subclass = stageSub
# end class stageSub


class secondaryLabelsTypeSub(supermod.secondaryLabelsType):
    def __init__(self, secondaryLabel=None):
        supermod.secondaryLabelsType.__init__(self, secondaryLabel)
supermod.secondaryLabelsType.subclass = secondaryLabelsTypeSub
# end class secondaryLabelsTypeSub


class secondaryLabelSub(supermod.secondaryLabel):
    def __init__(self, name=None, valueOf_=''):
        supermod.secondaryLabel.__init__(self, name, valueOf_)
supermod.secondaryLabel.subclass = secondaryLabelSub
# end class secondaryLabelSub


class promoteMapsTypeSub(supermod.promoteMapsType):
    def __init__(self, promoteMap=None):
        supermod.promoteMapsType.__init__(self, promoteMap)
supermod.promoteMapsType.subclass = promoteMapsTypeSub
# end class promoteMapsTypeSub


class promoteMapTypeSub(supermod.promoteMapType):
    def __init__(self, name=None, label=None, valueOf_=''):
        supermod.promoteMapType.__init__(self, name, label, valueOf_)
supermod.promoteMapType.subclass = promoteMapTypeSub
# end class promoteMapTypeSub


class platformDefinitionTypeSub(supermod.platformDefinitionType):
    def __init__(self, version=None, platformName=None, platformVersionTrove=None, baseFlavor=None, searchPaths=None, factorySources=None, autoLoadRecipes=None, secondaryLabels=None, architectures=None, flavorSets=None, containerTemplates=None, buildTemplates=None):
        supermod.platformDefinitionType.__init__(self, version, platformName, platformVersionTrove, baseFlavor, searchPaths, factorySources, autoLoadRecipes, secondaryLabels, architectures, flavorSets, containerTemplates, buildTemplates)
supermod.platformDefinitionType.subclass = platformDefinitionTypeSub
# end class platformDefinitionTypeSub


class platformTypeSub(supermod.platformType):
    def __init__(self, sourceTrove=None, useLatest=None, platformName=None, platformVersionTrove=None, baseFlavor=None, searchPaths=None, factorySources=None, autoLoadRecipes=None, secondaryLabels=None, architectures=None, flavorSets=None, containerTemplates=None, buildTemplates=None):
        supermod.platformType.__init__(self, sourceTrove, useLatest, platformName, platformVersionTrove, baseFlavor, searchPaths, factorySources, autoLoadRecipes, secondaryLabels, architectures, flavorSets, containerTemplates, buildTemplates)
supermod.platformType.subclass = platformTypeSub
# end class platformTypeSub


class nameFlavorTypeSub(supermod.nameFlavorType):
    def __init__(self, flavor=None, displayName=None, name=None, valueOf_=''):
        supermod.nameFlavorType.__init__(self, flavor, displayName, name, valueOf_)
supermod.nameFlavorType.subclass = nameFlavorTypeSub
# end class nameFlavorTypeSub


class architecturesTypeSub(supermod.architecturesType):
    def __init__(self, architecture=None):
        supermod.architecturesType.__init__(self, architecture)
supermod.architecturesType.subclass = architecturesTypeSub
# end class architecturesTypeSub


class flavorSetsTypeSub(supermod.flavorSetsType):
    def __init__(self, flavorSet=None):
        supermod.flavorSetsType.__init__(self, flavorSet)
supermod.flavorSetsType.subclass = flavorSetsTypeSub
# end class flavorSetsTypeSub


class containerTemplatesTypeSub(supermod.containerTemplatesType):
    def __init__(self, image=None):
        supermod.containerTemplatesType.__init__(self, image)
supermod.containerTemplatesType.subclass = containerTemplatesTypeSub
# end class containerTemplatesTypeSub


class buildTemplateTypeSub(supermod.buildTemplateType):
    def __init__(self, containerTemplateRef=None, architectureRef=None, displayName=None, name=None, flavorSetRef=None, valueOf_=''):
        supermod.buildTemplateType.__init__(self, containerTemplateRef, architectureRef, displayName, name, flavorSetRef, valueOf_)
supermod.buildTemplateType.subclass = buildTemplateTypeSub
# end class buildTemplateTypeSub


class buildTemplatesTypeSub(supermod.buildTemplatesType):
    def __init__(self, buildTemplate=None):
        supermod.buildTemplatesType.__init__(self, buildTemplate)
supermod.buildTemplatesType.subclass = buildTemplatesTypeSub
# end class buildTemplatesTypeSub


class productDefinitionSub(supermod.productDefinition):
    def __init__(self, version=None, productName=None, productShortname=None, productDescription=None, productVersion=None, productVersionDescription=None, conaryRepositoryHostname=None, conaryNamespace=None, imageGroup=None, sourceGroup=None, baseLabel=None, baseFlavor=None, stages=None, searchPaths=None, factorySources=None, autoLoadRecipes=None, secondaryLabels=None, architectures=None, flavorSets=None, containerTemplates=None, buildTemplates=None, buildDefinition=None, platform=None):
        supermod.productDefinition.__init__(self, version, productName, productShortname, productDescription, productVersion, productVersionDescription, conaryRepositoryHostname, conaryNamespace, imageGroup, sourceGroup, baseLabel, baseFlavor, stages, searchPaths, factorySources, autoLoadRecipes, secondaryLabels, architectures, flavorSets, containerTemplates, buildTemplates, buildDefinition, platform)
supermod.productDefinition.subclass = productDefinitionSub
# end class productDefinitionSub



#
# SAX handler used to determine the top level element.
#
class SaxSelectorHandler(handler.ContentHandler):
    def __init__(self):
        self.topElementName = None
    def getTopElementName(self):
        return self.topElementName
    def startElement(self, name, attrs):
        self.topElementName = name
        raise StopIteration


def parseSelect(inFileName):
    infile = file(inFileName, 'r')
    topElementName = None
    parser = make_parser()
    documentHandler = SaxSelectorHandler()
    parser.setContentHandler(documentHandler)
    try:
        try:
            parser.parse(infile)
        except StopIteration:
            topElementName = documentHandler.getTopElementName()
        if topElementName is None:
            raise RuntimeError, 'no top level element'
        topElementName = topElementName.replace('-', '_').replace(':', '_')
        if topElementName not in supermod.__dict__:
            raise RuntimeError, 'no class for top element: %s' % topElementName
        topElement = supermod.__dict__[topElementName]
        infile.seek(0)
        doc = minidom.parse(infile)
    finally:
        infile.close()
    rootNode = doc.childNodes[0]
    rootObj = topElement.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
##     sys.stdout.write('<?xml version="1.0" ?>\n')
##     rootObj.export(sys.stdout, 0)
    return rootObj


def saxParse(inFileName):
    parser = make_parser()
    documentHandler = supermod.Sax_stageTypeHandler()
    parser.setDocumentHandler(documentHandler)
    parser.parse('file:%s' % inFileName)
    rootObj = documentHandler.getRoot()
    #sys.stdout.write('<?xml version="1.0" ?>\n')
    #rootObj.export(sys.stdout, 0)
    return rootObj


def saxParseString(inString):
    parser = make_parser()
    documentHandler = supermod.SaxContentHandler()
    parser.setDocumentHandler(documentHandler)
    parser.feed(inString)
    parser.close()
    rootObj = documentHandler.getRoot()
    #sys.stdout.write('<?xml version="1.0" ?>\n')
    #rootObj.export(sys.stdout, 0)
    return rootObj


def parse(inFilename):
    doc = minidom.parse(inFilename)
    rootNode = doc.documentElement
    rootObj = supermod.stageType.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
##     sys.stdout.write('<?xml version="1.0" ?>\n')
##     rootObj.export(sys.stdout, 0, name_="stageType",
##         namespacedef_='')
    doc = None
    return rootObj


def parseString(inString):
    doc = minidom.parseString(inString)
    rootNode = doc.documentElement
    rootObj = supermod.stageType.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
##     sys.stdout.write('<?xml version="1.0" ?>\n')
##     rootObj.export(sys.stdout, 0, name_="stageType",
##         namespacedef_='')
    return rootObj


def parseLiteral(inFilename):
    doc = minidom.parse(inFilename)
    rootNode = doc.documentElement
    rootObj = supermod.stageType.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
##     sys.stdout.write('from supers import *\n\n')
##     sys.stdout.write('rootObj = stageType(\n')
##     rootObj.exportLiteral(sys.stdout, 0, name_="stageType")
##     sys.stdout.write(')\n')
    return rootObj


USAGE_TEXT = """
Usage: python ???.py <infilename>
"""

def usage():
    print USAGE_TEXT
    sys.exit(1)


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        usage()
    infilename = args[0]
    root = parse(infilename)


if __name__ == '__main__':
    main()
    #import pdb
    #pdb.run('main()')


