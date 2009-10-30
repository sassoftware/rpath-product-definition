#!/usr/bin/env python
# -*- mode: pymode; coding: latin1; -*-

import sys
import re

#
# You must include the following class definition at the top of
#   your method specification file.
#
class MethodSpec(object):
    def __init__(self, name='', source='', class_names='',
            class_names_compiled=None):
        """MethodSpec -- A specification of a method.
        Member variables:
            name -- The method name
            source -- The source code for the method.  Must be
                indented to fit in a class definition.
            class_names -- A regular expression that must match the
                class names in which the method is to be inserted.
            class_names_compiled -- The compiled class names.
                generateDS.py will do this compile for you.
        """
        self.name = name
        self.source = source
        if class_names is None:
            self.class_names = ('.*', )
        else:
            self.class_names = class_names
        if class_names_compiled is None:
            self.class_names_compiled = re.compile(self.class_names)
        else:
            self.class_names_compiled = class_names_compiled
    def get_name(self):
        return self.name
    def set_name(self, name):
        self.name = name
    def get_source(self):
        return self.source
    def set_source(self, source):
        self.source = source
    def get_class_names(self):
        return self.class_names
    def set_class_names(self, class_names):
        self.class_names = class_names
        self.class_names_compiled = re.compile(class_names)
    def get_class_names_compiled(self):
        return self.class_names_compiled
    def set_class_names_compiled(self, class_names_compiled):
        self.class_names_compiled = class_names_compiled
    def match_name(self, class_name):
        """Match against the name of the class currently being generated.
        If this method returns True, the method will be inserted in
          the generated class.
        """
        if self.class_names_compiled.search(class_name):
            return True
        else:
            return False
    def get_interpolated_source(self, values_dict):
        """Get the method source code, interpolating values from values_dict
        into it.  The source returned by this method is inserted into
        the generated class.
        """
        source = self.source % values_dict
        return source
    def show(self):
        print 'specification:'
        print '    name: %s' % (self.name, )
        print self.source
        print '    class_names: %s' % (self.class_names, )
        print '    names pat  : %s' % (self.class_names_compiled.pattern, )

#
# Provide one or more method specification such as the following.
# Notes:
# - Each generated class contains a class variable member_data_items_.
#   This variable contains a list of instances of class _MemberSpec.
#   See the definition of class _MemberSpec near the top of the
#   generated superclass file and also section "User Methods" in
#   the documentation, as well as the examples below.

#
# Replace the following method specifications with your own.

#
# Sample method specification #1
#
getTroveTup = MethodSpec(name='getTroveTup',
    source='''
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
''',
    class_names = r'^searchPathType$',
    )

imageTypeGetFields = MethodSpec(name='getTroveTup',
    source='''
    def getFields(self):
        fieldNames = [ x.get_name()
            for x in self.member_data_items_ ]
        fields = ((x, getattr(self, x)) for x in fieldNames
            if x not in ('containerFormat', 'valueOf_'))
        fields = dict((x, y) for (x, y) in fields if y is not None)
        return fields

    fields = property(getFields)
''',
    class_names = r'^imageType$',
    )

buildTypeMethods = MethodSpec('buildTypeMethods',
    source = '''
    def getBuildStages(self):
        return [ x.get_ref() for x in self.get_stage() ]

    def getBuildImageGroup(self):
        val = self.get_imageGroup()
        if val is None:
            return self.parentImageGroup
        return val

    def getBuildSourceGroup(self):
        val = self.get_sourceGroup()
        if val is None:
            return self.parentSourceGroup
        return val

    def getBuildBaseFlavor(self):
        return self.buildFlavor

    def getBuildImage(self):
        fields = self.containerTemplateFields.copy()
        if self.image:
            fields.update(self.image.getFields())
        return imageType.subclass.factory(**fields)

    getBuildName = get_name
''',
    class_names = r'^buildType$',
    )

secondaryLabelMethods = MethodSpec('secondaryLabelMethods',
    source = '''
    getName = get_name
    getLabel = getValueOf_
    setLabel = setValueOf_
    label = property(getLabel, setLabel)
''',
    class_names = r'^secondaryLabel$',
    )

stageTypeMethods = MethodSpec('stageTypeMethods',
    source = '''
    def getPromoteMaps(self):
        vals = self.get_promoteMaps()
        if vals is None:
            return []
        return vals.get_promoteMap()
''',
    class_names = r'^stageType$',
    )

promoteMapTypeMethods = MethodSpec('promoteMapTypeMethods',
    source = '''
    getMapName = get_name
    getMapLabel = get_label
''',
    class_names = r'^promoteMapType$',
    )

nameLabelTypeMethods = MethodSpec('nameLabelTypeMethods',
    source = '''
    getTroveName = get_troveName
    getLabel = get_label
''',
    class_names = r'^nameLabelType$',
    )

contentProviderTypeMethods = MethodSpec('contentProviderTypeMethods',
    source = '''
    def _getDataSources(self):
        if self.dataSource is None:
            return []
        return self.dataSource
    dataSources = property(_getDataSources)

    def _getSourceTypes(self):
        if self.sourceType is None:
            return []
        return self.sourceType
    sourceTypes = property(_getSourceTypes)
''',
    class_names = r'contentProviderType$',
    )

METHOD_SPECS = (
    getTroveTup,
    buildTypeMethods,
    imageTypeGetFields,
    secondaryLabelMethods,
    stageTypeMethods,
    promoteMapTypeMethods,
    nameLabelTypeMethods,
    contentProviderTypeMethods,
)

def test():
    for spec in METHOD_SPECS:
        spec.show()

def main():
    test()


if __name__ == '__main__':
    main()


