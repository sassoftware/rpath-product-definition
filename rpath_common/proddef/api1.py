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

from rpath_common.xmllib import api1 as xmllib

class ProductDefinition(object):
    """
    Represents the definition of a product.
    """
    def __init__(self, elementDict={}, xml=None):
        """
        Pass in either a dictionary as constructed in the example below, or an
        xml string to create an instance.
        """
        # Static text that needs to be at the beginning of our xml.
        self.xml_header_tag = '<?xml version="1.0" encoding="UTF-8"?>'

        self.elementDict = elementDict

        self.xmldb = xmllib.DataBinder()
        self.xmldb.registerType('baseFlavor', xmllib.StringNode)

        if xml is None:
            # No xml was passed in, create an empty object that we will build
            # out later to represent the dict.
            XmlObj = type('XmlObj', (object,), {})
            XmlObj.__name__ = 'productDefinition'
            self.xmlobj = XmlObj()
            self._setFromDict()
        else:
            # Create the object from the passed in xml using our DataBinder.
            self.xmlobj = self.xmldb.parseString(xml)

        # A special attribute recognized by xmllib to preserve child order.
        self.xmlobj._childOrder = ['baseFlavor', 'stages', 'upstreamSources',
                                   'buildDefinition']

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
            
    
def cls(**kwargs):
    """
    Return a class instance that has a class attribute set for each key/value
    pair in kwargs.  If one of the values in the kwargs is a dict itself, that
    signifies a child element.  In that case, create an object for that
    element using recursion and add the produced object to our instance's main
    dictionary.
    """

    # Just an empty class on which to set attributes.
    class Cls(object):
        #pylint: disable-msg=R0903
        pass

    # Empty dict to store attrs for our instance.
    attrs = {}

    for k, v in kwargs.items():
        # If v is a dict, create an object for it.
        if type(v) == type({}):
            attrs[k] = [cls(**v)]
        # Else, just set it as a class attribute on Cls
        else:
            setattr(Cls, k, v)

    # Instantiate our modified class and update it's internal dictionary to
    # represent any child elements.
    x = Cls()
    x.__dict__.update(attrs)
    return x
