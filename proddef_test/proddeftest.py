#
# Copyright (c) rPath, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import copy
import os
import sys
import StringIO

from conary import conaryclient, versions
from conary.deps import deps
from conary.lib import util
from conary_test import rephelp
from rpath_proddef import api1 as proddef
from testrunner import testhelp
from proddef_test import resources

VFS = versions.VersionFromString

legacyXML = \
"""<?xml version="1.0" encoding="UTF-8"?>
<productDefinition version="1.3"
xmlns="http://www.rpath.com/permanent/rpd-1.3.xsd"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.rpath.com/permanent/rpd-1.3.xsd">
   <productName>My Awesome Appliance</productName>
   <productShortname>awesome</productShortname>
   <productDescription>
      This here is my awesome appliance.
      Is it not nifty?
      Worship the appliance.
   </productDescription>
   <productVersion>1.0</productVersion>
   <productVersionDescription>
      Version 1.0 features "stability" and "usefulness", which is a
      vast improvement over our pre-release code.
   </productVersionDescription>
   <conaryRepositoryHostname>conary.example.com</conaryRepositoryHostname>
   <conaryNamespace>mycompany</conaryNamespace>
   <imageGroup>group-foo</imageGroup>
   <baseFlavor>\
      ~MySQL-python.threadsafe, ~X, ~!alternatives, !bootstrap,\
      ~builddocs, ~buildtests, !cross, ~desktop, ~!dietlibc, ~!dom0, ~!domU,\
      ~emacs, ~gcj, ~gnome, ~grub.static, ~gtk, ~ipv6, ~kde, ~!kernel.debug,\
      ~kernel.debugdata, ~!kernel.numa, ~kernel.smp, ~krb, ~ldap, ~nptl,\
      ~!openssh.smartcard, ~!openssh.static_libcrypto, pam, ~pcre, ~perl,\
      ~!pie, ~!postfix.mysql, ~python, ~qt, ~readline, ~!sasl, ~!selinux,\
      ~sqlite.threadsafe, ssl, ~tcl, tcpwrappers, ~tk, ~uClibc, !vmware,\
      ~!xen, ~!xfce, ~!xorg-x11.xprint\
   </baseFlavor>
   <stages>
      <stage labelSuffix="-devel" name="devel"/>
      <stage labelSuffix="-qa" name="qa"/>
      <stage labelSuffix="" name="release"/>
   </stages>
   <searchPaths>
      <searchPath label="rap.rpath.com@rpath:linux-1"
troveName="group-rap-standard"/>
      <searchPath label="products.rpath.com@rpath:postgres-8.2"
troveName="group-postgres"/>
   </searchPaths>
  <factorySources>
    <factorySource troveName="group-factories" label="products.rpath.com@rpath:factories-1"/>
  </factorySources>
   <buildDefinition>
      <build baseFlavor="is: x86" name="x86 installableIso">
         <installableIsoImage freespace="1024"/>
         <stage ref="devel"/>
         <stage ref="qa"/>
         <stage ref="release"/>
         <imageGroup>group-os</imageGroup>
      </build>
      <build baseFlavor="is: x86_64" name="x86_64 installableIso">
         <installableIsoImage/>
         <stage ref="release"/>
      </build>
      <build baseFlavor="~xen, ~domU is: x86" name="x86 rawFs">
         <rawFsImage freespace="1234"/>
      </build>
      <build baseFlavor="~xen, ~domU is: x86 x86_64" name="x86_64 rawHd">
         <rawHdImage autoResolve="true" baseFileName="/proc/foo/moo"/>
         <stage ref="devel"/>
         <stage ref="qa"/>
         <stage ref="release"/>
         <imageGroup>group-os</imageGroup>
      </build>
      <build baseFlavor="~vmware is: x86 x86_64" name="x86_64 vmware">
         <vmwareImage autoResolve="true" baseFileName="foobar"/>
         <stage ref="release"/>
         <imageGroup>group-bar</imageGroup>
      </build>
      <build baseFlavor="is: x86 x86_64" name="Virtual Iron Image">
         <virtualIronImage />
         <stage ref="release"/>
         <imageGroup>group-bar</imageGroup>
      </build>
   </buildDefinition>
</productDefinition>
"""

legacyXML2 = \
"""<?xml version="1.0" encoding="UTF-8"?>
<productDefinition version="1.3"
xmlns="http://www.rpath.com/permanent/rpd-1.3.xsd"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.rpath.com/permanent/rpd-1.3.xsd">
   <productName>My Awesome Appliance</productName>
   <productShortname>awesome</productShortname>
   <productDescription>
      This here is my awesome appliance.
      Is it not nifty?
      Worship the appliance.
   </productDescription>
   <productVersion>1.0</productVersion>
   <productVersionDescription>
      Version 1.0 features "stability" and "usefulness", which is a
      vast improvement over our pre-release code.
   </productVersionDescription>
   <conaryRepositoryHostname>conary.example.com</conaryRepositoryHostname>
   <conaryNamespace>mycompany</conaryNamespace>
   <imageGroup>group-foo</imageGroup>
   <baseFlavor>\
      ~MySQL-python.threadsafe, ~X, ~!alternatives, !bootstrap,\
      ~builddocs, ~buildtests, !cross, ~desktop, ~!dietlibc, ~!dom0, ~!domU,\
      ~emacs, ~gcj, ~gnome, ~grub.static, ~gtk, ~ipv6, ~kde, ~!kernel.debug,\
      ~kernel.debugdata, ~!kernel.numa, ~kernel.smp, ~krb, ~ldap, ~nptl,\
      ~!openssh.smartcard, ~!openssh.static_libcrypto, pam, ~pcre, ~perl,\
      ~!pie, ~!postfix.mysql, ~python, ~qt, ~readline, ~!sasl, ~!selinux,\
      ~sqlite.threadsafe, ssl, ~tcl, tcpwrappers, ~tk, ~uClibc, !vmware,\
      ~!xen, ~!xfce, ~!xorg-x11.xprint\
   </baseFlavor>
   <stages>
      <stage labelSuffix="-devel" name="devel"/>
      <stage labelSuffix="-qa" name="qa"/>
      <stage labelSuffix="" name="release"/>
   </stages>
   <searchPaths>
      <searchPath label="rap.rpath.com@rpath:linux-1"
troveName="group-rap-standard"/>
      <searchPath label="products.rpath.com@rpath:postgres-8.2"
troveName="group-postgres"/>
   </searchPaths>
  <factorySources>
    <factorySource troveName="group-factories" label="products.rpath.com@rpath:factories-1"/>
  </factorySources>
  <architectures>
    <architecture name="x86" flavor="is: x86(cmov, i486, i586, i686)"/>
  </architectures>
  <buildDefinition>
    <build flavor="foo is: x86" name="x86 installableIso" architectureRef="x86">
      <installableIsoImage freespace="1024"/>
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
      <imageGroup>group-os</imageGroup>
    </build>
    <build flavor="is: x86" name="x86 rawHd" architectureRef="x86">
      <rawHdImage freespace="1024"/>
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
      <imageGroup>group-os</imageGroup>
    </build>
    <build flavor="foo" name="just something random">
      <rawHdImage freespace="1024"/>
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
      <imageGroup>group-os</imageGroup>
    </build>
    <build flavor="foo" name="random2" architectureRef="missing">
      <rawHdImage freespace="1024"/>
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
      <imageGroup>group-os</imageGroup>
    </build>
    <build name="random2" architectureRef="missing">
      <rawHdImage freespace="1024"/>
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
      <imageGroup>group-os</imageGroup>
    </build>
  </buildDefinition>
</productDefinition>
"""

legacyXML3 = \
"""<?xml version="1.0" encoding="UTF-8"?>
<productDefinition version="1.3"
xmlns="http://www.rpath.com/permanent/rpd-1.3.xsd"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.rpath.com/permanent/rpd-1.3.xsd">
   <productName>My Awesome Appliance</productName>
   <productShortname>awesome</productShortname>
   <productDescription>
      This here is my awesome appliance.
      Is it not nifty?
      Worship the appliance.
   </productDescription>
   <productVersion>1.0</productVersion>
   <productVersionDescription>
      Version 1.0 features "stability" and "usefulness", which is a
      vast improvement over our pre-release code.
   </productVersionDescription>
   <conaryRepositoryHostname>conary.example.com</conaryRepositoryHostname>
   <conaryNamespace>mycompany</conaryNamespace>
   <imageGroup>group-foo</imageGroup>
   <baseFlavor>\
      ~MySQL-python.threadsafe, ~X, ~!alternatives, !bootstrap,\
      ~builddocs, ~buildtests, !cross, ~desktop, ~!dietlibc, ~!dom0, ~!domU,\
      ~emacs, ~gcj, ~gnome, ~grub.static, ~gtk, ~ipv6, ~kde, ~!kernel.debug,\
      ~kernel.debugdata, ~!kernel.numa, ~kernel.smp, ~krb, ~ldap, ~nptl,\
      ~!openssh.smartcard, ~!openssh.static_libcrypto, pam, ~pcre, ~perl,\
      ~!pie, ~!postfix.mysql, ~python, ~qt, ~readline, ~!sasl, ~!selinux,\
      ~sqlite.threadsafe, ssl, ~tcl, tcpwrappers, ~tk, ~uClibc, !vmware,\
      ~!xen, ~!xfce, ~!xorg-x11.xprint\
   </baseFlavor>
   <stages>
      <stage labelSuffix="-devel" name="devel"/>
      <stage labelSuffix="-qa" name="qa"/>
      <stage labelSuffix="" name="release"/>
   </stages>
   <searchPaths>
      <searchPath label="rap.rpath.com@rpath:linux-1"
troveName="group-rap-standard"/>
      <searchPath label="products.rpath.com@rpath:postgres-8.2"
troveName="group-postgres"/>
   </searchPaths>
  <factorySources>
    <factorySource troveName="group-factories" label="products.rpath.com@rpath:factories-1"/>
  </factorySources>
  <buildDefinition>
    <build flavor="foo is: x86" name="x86 installableIso" architectureRef="x86">
      <installableIsoImage freespace="1024"/>
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
      <imageGroup>group-os</imageGroup>
    </build>
    <build flavor="is: x86" name="x86 rawHd" architectureRef="x86">
      <rawHdImage freespace="1024"/>
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
      <imageGroup>group-os</imageGroup>
    </build>
    <build flavor="foo" name="just something random">
      <rawHdImage freespace="1024"/>
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
      <imageGroup>group-os</imageGroup>
    </build>
    <build flavor="foo" name="random2" architectureRef="missing">
      <rawHdImage freespace="1024"/>
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
      <imageGroup>group-os</imageGroup>
    </build>
    <build name="random2" architectureRef="missing">
      <rawHdImage freespace="1024"/>
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
      <imageGroup>group-os</imageGroup>
    </build>
  </buildDefinition>
</productDefinition>
"""

XML = """<?xml version="1.0" encoding="UTF-8"?>
<productDefinition xmlns="http://www.rpath.com/permanent/rpd-%(version)s.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="%(version)s" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-%(version)s.xsd">
  <productName>My Awesome Appliance</productName>
  <productShortname>awesome</productShortname>
  <productDescription>
      This here is my awesome appliance.
      Is it not nifty?
      Worship the appliance.
   </productDescription>
  <productVersion>1.0</productVersion>
  <productVersionDescription>
      Version 1.0 features "stability" and "usefulness", which is a
      vast improvement over our pre-release code.
   </productVersionDescription>
  <conaryRepositoryHostname>conary.example.com</conaryRepositoryHostname>
  <conaryNamespace>mycompany</conaryNamespace>
  <imageGroup>group-foo</imageGroup>
  <sourceGroup>group-source</sourceGroup>
  <baseFlavor>\
      ~MySQL-python.threadsafe, ~X, ~!alternatives, !bootstrap,\
      ~builddocs, ~buildtests, !cross, ~desktop, ~!dietlibc, ~!dom0, ~!domU,\
      ~emacs, ~gcj, ~gnome, ~grub.static, ~gtk, ~ipv6, ~kde, ~!kernel.debug,\
      ~kernel.debugdata, ~!kernel.numa, ~kernel.smp, ~krb, ~ldap, ~nptl,\
      ~!openssh.smartcard, ~!openssh.static_libcrypto, pam, ~pcre, ~perl,\
      ~!pie, ~!postfix.mysql, ~python, ~qt, ~readline, ~!sasl, ~!selinux,\
      ~sqlite.threadsafe, ssl, ~tcl, tcpwrappers, ~tk, ~uClibc, !vmware,\
      ~!xen, ~!xfce, ~!xorg-x11.xprint\
   </baseFlavor>
  <stages>
    <stage labelSuffix="-devel" name="devel"/>
    <stage labelSuffix="-qa" name="qa"/>
    <stage labelSuffix="" name="release"/>
  </stages>
  <searchPaths>
    <searchPath label="rap.rpath.com@rpath:linux-1" troveName="group-rap-standard"/>
    <searchPath label="products.rpath.com@rpath:postgres-8.2" troveName="group-postgres"/>
    <searchPath label="conary.rpath.com@rpl:1" troveName="group-os" isGroupSearchPathTrove="false"/>
    <searchPath label="localhost@linux:1" troveName="foo" isResolveTrove="false" isGroupSearchPathTrove="true"/>
  </searchPaths>
  <factorySources>
    <factorySource troveName="group-factories" label="products.rpath.com@rpath:factories-1"/>
  </factorySources>
  <architectures>
    <architecture name="x86" displayName="32 bit" flavor="grub.static, dietlibc is:x86(i486, i586, cmov, mmx, sse)"/>
    <architecture name="x86_64" displayName="64 bit" flavor="!grub.static, !dietlibc is:x86_64 x86(i486, i586, cmov, mmx, sse)"/>
  </architectures>
  <flavorSets>
    <flavorSet name="AMI" displayName="AMI" flavor="xen, domU, !dom0, !vmware"/>
    <flavorSet name="Hyper-V" displayName="Hyper-V" flavor="!vmware, ~!xen"/>
    <flavorSet name="LiveIso" displayName="LiveIso" flavor="~!vmware, !xen, !dom0, !domU"/>
    <flavorSet name="VMware" displayName="VMware" flavor="~vmware, !xen"/>
    <flavorSet name="VirtualIron" displayName="VirtualIron" flavor="!vmware, !xen"/>
    <flavorSet name="Xen" displayName="Xen" flavor="~xen, ~domU, ~!dom0, ~!vmware"/>
  </flavorSets>
  <containerTemplates>
    <image containerFormat="amiImage" autoResolve="false" baseFileName="" installLabelPath="" amiHugeDiskMountpoint="/mnt/floppy" freespace="1024" swapSize="1024"/>
    <image containerFormat="applianceIsoImage" autoResolve="false" baseFileName="" installLabelPath="" anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" betaNag="false" bugsUrl="" maxIsoSize="681574400" mediaTemplateTrove="" showMediaCheck="false"/>
    <image containerFormat="installableIsoImage" autoResolve="false" baseFileName="" installLabelPath="" anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" betaNag="false" bugsUrl="" maxIsoSize="681574400" mediaTemplateTrove="" showMediaCheck="false"/>
    <image containerFormat="liveIsoImage" autoResolve="false" baseFileName="" installLabelPath="" unionfs="true" zisofs="true"/>
    <image containerFormat="netbootImage" autoResolve="false" baseFileName="" installLabelPath=""/>
    <image containerFormat="rawFsImage" autoResolve="false" baseFileName="" installLabelPath="" freespace="1024" swapSize="128"/>
    <image containerFormat="rawHdImage" autoResolve="false" baseFileName="" installLabelPath="" freespace="1024" swapSize="128"/>
    <image containerFormat="tarballImage" autoResolve="false" baseFileName="" installLabelPath="" swapSize="0"/>
    <image containerFormat="updateIsoImage" autoResolve="false" baseFileName="" installLabelPath="" anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" betaNag="false" bugsUrl="" maxIsoSize="681574400" mediaTemplateTrove="" showMediaCheck="false"/>
    <image containerFormat="vhdImage" autoResolve="false" baseFileName="" installLabelPath="" freespace="1024" swapSize="128" vhdDiskType="dynamic"/>
    <image containerFormat="vmwareImage" autoResolve="false" baseFileName="" installLabelPath="" diskAdapter="lsilogic" freespace="1024" natNetworking="true" swapSize="128" vmMemory="128" vmSnapshots="false"/>
    <image containerFormat="vmwareEsxImage" autoResolve="false" baseFileName="" installLabelPath="" freespace="1024" natNetworking="true" swapSize="128" vmMemory="128"/>
    <image containerFormat="xenOvaImage" autoResolve="false" baseFileName="" installLabelPath="" freespace="1024" swapSize="128" vmMemory="128"/>
  </containerTemplates>
  <buildTemplates>
    <buildTemplate name="Demo CD" architectureRef="x86" containerTemplateRef="liveIso"/>
    <buildTemplate name="EC2 AMI Large/Huge" architectureRef="x86_64" containerTemplateRef="ami" flavorSetRef="AMI"/>
    <buildTemplate name="EC2 AMI Small" architectureRef="x86" containerTemplateRef="ami" flavorSetRef="AMI"/>
    <buildTemplate name="ISO" architectureRef="x86" containerTemplateRef="applianceIso"/>
    <buildTemplate name="ISO" architectureRef="x86" containerTemplateRef="installableIso"/>
    <buildTemplate name="ISO" architectureRef="x86" containerTemplateRef="updateIso"/>
    <buildTemplate name="ISO" architectureRef="x86_64" containerTemplateRef="applianceIso"/>
    <buildTemplate name="ISO" architectureRef="x86_64" containerTemplateRef="installableIso"/>
    <buildTemplate name="ISO" architectureRef="x86_64" containerTemplateRef="updateIso"/>
    <buildTemplate name="MS Hyper-V" architectureRef="x86" containerTemplateRef="vhdImage" flavorSetRef="Hyper-V"/>
    <buildTemplate name="MS Hyper-V" architectureRef="x86_64" containerTemplateRef="vhdImage" flavorSetRef="Hyper-V"/>
    <buildTemplate name="Raw Filesystem" architectureRef="x86" containerTemplateRef="rawFsImage"/>
    <buildTemplate name="Raw Filesystem" architectureRef="x86_64" containerTemplateRef="rawFsImage"/>
    <buildTemplate name="Raw Hard Drive" architectureRef="x86" containerTemplateRef="rawHdImage"/>
    <buildTemplate name="Raw Hard Drive" architectureRef="x86_64" containerTemplateRef="rawHdImage"/>
    <buildTemplate name="Tar Image" architectureRef="x86" containerTemplateRef="tarballImage"/>
    <buildTemplate name="Tar Image" architectureRef="x86_64" containerTemplateRef="tarballImage"/>
    <buildTemplate name="VMware" architectureRef="x86" containerTemplateRef="vmwareImage" flavorSetRef="VMware"/>
    <buildTemplate name="VMware" architectureRef="x86" containerTemplateRef="vmwareEsxImage" flavorSetRef="VMware"/>
    <buildTemplate name="VMware" architectureRef="x86_64" containerTemplateRef="vmwareImage" flavorSetRef="VMware"/>
    <buildTemplate name="VMware" architectureRef="x86_64" containerTemplateRef="vmwareEsxImage" flavorSetRef="VMware"/>
    <buildTemplate name="Virtual Iron" architectureRef="x86" containerTemplateRef="vhdImage" flavorSetRef="VirtualIron"/>
    <buildTemplate name="Virtual Iron" architectureRef="x86_64" containerTemplateRef="vhdImage" flavorSetRef="VirtualIron"/>
    <buildTemplate name="Xen OVA" architectureRef="x86" containerTemplateRef="xenOvaImage" flavorSetRef="Xen"/>
    <buildTemplate name="Xen OVA" architectureRef="x86_64" containerTemplateRef="xenOvaImage" flavorSetRef="Xen"/>
  </buildTemplates>
  <buildDefinition>
    <build containerTemplateRef="installIso" architectureRef="x86" name="x86 installableIso">
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
      <imageGroup>group-os</imageGroup>
      <sourceGroup>group-source</sourceGroup>
    </build>
    <build containerTemplateRef="installIso" architectureRef="x86_64" name="x86_64 installableIso">
      <stage ref="release"/>
    </build>
    <build flavorSetRef="xen" containerTemplateRef="rawFsImage" architectureRef="x86" name="x86 rawFsImage">
      <image freespace="1234"/>
    </build>
    <build flavorSetRef="xen" containerTemplateRef="rawHdImage" architectureRef="x86_64" name="x86_64 rawHdImage">
      <image autoResolve="true" baseFileName="proc-foo-moo"/>
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
      <imageGroup>group-os</imageGroup>
      <sourceGroup>group-source</sourceGroup>
    </build>
    <build flavorSetRef="vmware" containerTemplateRef="vmwareImage" architectureRef="x86_64" name="x86_64 vmware">
      <image autoResolve="true" baseFileName="foobar"/>
      <stage ref="release"/>
      <imageGroup>group-bar</imageGroup>
      <sourceGroup>group-source-bar</sourceGroup>
    </build>
    <build architectureRef="x86_64" containerTemplateRef="vhdImage" name="Virtual Iron Image">
      <stage ref="release"/>
      <imageGroup>group-bar</imageGroup>
      <sourceGroup>group-source-bar</sourceGroup>
    </build>
  </buildDefinition>
</productDefinition>
""" % dict(version = proddef.ProductDefinition.version)

class BaseTest(testhelp.TestCase):
    def getArchiveDir(self):
        return resources.get_archive()

    def setUp(self):
        testhelp.TestCase.setUp(self)
        self.setUpSchemaDir()

    def setUpSchemaDir(self):
        schemaFile = "rpd-%s.xsd" % proddef.ProductDefinition.version
        schemaDir = resources.get_path('xsd')
        if not os.path.exists(os.path.join(schemaDir, schemaFile)):
            # Not running from a checkout
            schemaDir = os.path.join("/usr/share/rpath_proddef")
            assert(os.path.exists(os.path.join(schemaDir, schemaFile)))
        self.schemaDir = schemaDir
        self.mock(proddef.ProductDefinition, 'schemaDir', schemaDir)
        self.mock(proddef.PlatformDefinition, 'schemaDir', schemaDir)
        self.mock(proddef.Platform, 'schemaDir', schemaDir)

    def newProductDefinition(self, **kwargs):
        defaults = dict(
            productName = 'product name',
            productShortname = 'product short name',
            productDescription = 'product description',
            productVersion = '0.1',
            productVersionDescription = 'version 0.1 description',
            conaryRepositoryHostname = 'conary.example.com',
            conaryNamespace = 'lnx',
            imageGroup = 'group-os',
            baseFlavor = '',
        )
        defaults.update(dict((k, v) for (k, v) in kwargs.items() if k in defaults))
        prd = proddef.ProductDefinition()
        for k, v in defaults.items():
            method = getattr(prd, "set%s%s" % (k[0].upper(), k[1:]))
            method(v)
        stages = kwargs.get('stages', [('release', '')])
        for name, labelSuffix in stages:
            prd.addStage(name=name, labelSuffix=labelSuffix)
        return prd

class RepositoryBasedTest(rephelp.RepositoryHelper, BaseTest):
    def setUp(self):
        rephelp.RepositoryHelper.setUp(self)
        BaseTest.setUpSchemaDir(self)

    def test_saveToRepository(self):
        label = str(self.defLabel)

        pd = proddef.ProductDefinition(fromStream = XML)

        # Test the exception code paths first
        # force a bogus port number to prevent collisions with a real repo
        try:
            self.cfg.configLine('repositoryMap localhost http://localhost:999999/conary/')
            client = conaryclient.ConaryClient(self.cfg)
            self.failUnlessRaises(proddef.RepositoryError,
                pd._getStreamFromRepository, client, label)
        finally:
            self.cfg.repositoryMap = conaryclient.conarycfg.RepoMap()

        self.openRepository()
        client = conaryclient.ConaryClient(self.cfg)

        self.failUnlessRaises(proddef.ProductDefinitionTroveNotFoundError,
            pd._getStreamFromRepository, client, label)

        pd._saveToRepository(client, label, message = "Boo!\n")

        sourceTrv = client.getRepos().findTrove(versions.Label(label),
            ('product-definition:source', None, None))[0]

        fileStreams = client.getFilesFromTrove(sourceTrv[0], sourceTrv[1],
            sourceTrv[2])

        recipeStream = fileStreams['product-definition.recipe']
        recipe = recipeStream.read()
        self.failIf("@NAME@" in recipe, recipe)
        self.failIf("@VERSION@" in recipe, recipe)

        stream = pd._getStreamFromRepository(client, label)

        # Test the exception code paths too
        self.failUnlessRaises(proddef.ProductDefinitionTroveNotFoundError,
            pd._getStreamFromRepository, client, label + 'x')

        # Mangle the file name
        pd._troveFileNames[-1] += 'GARBLE'
        self.failUnlessRaises(proddef.ProductDefinitionFileNotFoundError,
            pd._getStreamFromRepository, client, label)

    def testLoadFromRepository(self):
        labelHost = self.defLabel.getHost()
        conaryNamespace = 'exm'

        productDescription = "Some long\nproduct description\n"
        productVersionDescription = "This version\nhas bugs\n"
        baseFlavor = "~!perl"

        prodDef = proddef.ProductDefinition()
        prodDef.setProductName("My Awesome Appliance")
        prodDef.setProductShortname("awesome")
        prodDef.setProductDescription(productDescription)
        prodDef.setProductVersion("1.0")
        prodDef.setProductVersionDescription(productVersionDescription)
        prodDef.setConaryRepositoryHostname(labelHost)
        prodDef.setConaryNamespace(conaryNamespace)
        prodDef.setImageGroup("group-awesome-dist")
        prodDef.setBaseFlavor(baseFlavor)
        prodDef.addStage(name='devel', labelSuffix='-devel')
        prodDef.addStage(name='qa', labelSuffix='-qa')
        prodDef.addStage(name='release', labelSuffix='')

        prodDef.addContainerTemplate(prodDef.imageType('installableIsoImage'))
        prodDef.addContainerTemplate(prodDef.imageType('xenOvaImage'))
        prodDef.addContainerTemplate(prodDef.imageType('rawHdImage'))
        prodDef.addContainerTemplate(prodDef.imageType('vmwareImage'))

        prodDef.addFlavorSet('x86', '32 bit', 'is: x86')
        prodDef.addFlavorSet('x86_64', '64 bit', 'is: x86 x86_64')
        prodDef.addFlavorSet('xen', 'Xen', '~xen,~domU is: x86')
        prodDef.addFlavorSet('vmware x86_64', 'VMware', '~vmware is: x86 x86_64')

        prodDef.addSearchPath(troveName='group-rap-standard',
            label=versions.Label('rap.rpath.com@rpath:linux-1'))

        prodDef.addFactorySource(troveName='group-factories',
            label='products.rpath.com@rpath:factories-1')

        prodDef.addBuildDefinition(name='x86 Installable ISO Build',
            flavorSetRef = 'x86',
            containerTemplateRef = 'installableIsoImage',
            stages = ['devel', 'qa', 'release'])

        prodDef.addBuildDefinition(name='x86-64 Installable ISO Build',
            flavorSetRef = 'x86_64',
            containerTemplateRef = 'installableIsoImage',
            stages = ['devel', 'qa', 'release'])

        prodDef.addBuildDefinition(
            name='x86 Citrix Xenserver Virtual Appliance',
            flavorSetRef = 'xen',
            containerTemplateRef = 'xenOvaImage',
            stages = ['devel', 'qa', 'release'])

        prodDef.addBuildDefinition(
            name='Another Xen Build',
            flavorSetRef = 'xen',
            containerTemplateRef = 'rawHdImage',
            image = prodDef.imageType(None,
                            dict(autoResolve="true",
                            baseFileName="/poo/moo/foo")),
            stages = ['devel', 'qa', 'release'])

        prodDef.addBuildDefinition(name='VMWare build',
            flavorSetRef = 'vmware x86_64',
            containerTemplateRef = 'vmwareImage',
            image = prodDef.imageType(None,
                            dict(autoResolve="true",
                            baseFileName="foobar")),
            stages = ['devel', 'qa'])

        prodDef.addBuildDefinition(
            name='Totally VMware optional build from a different group',
            flavorSetRef = 'vmware x86_64',
            imageGroup='group-foo-dist',
            containerTemplateRef = 'vmwareImage',)

        sio = StringIO.StringIO()

        prodDef.serialize(sio)

        self.openRepository()

        client = conaryclient.ConaryClient(self.cfg)
        prodDef.saveToRepository(client)

        prodDef = proddef.ProductDefinition()
        prodDef.setProductShortname("awesome")
        prodDef.setProductVersion("1.0")
        prodDef.setConaryRepositoryHostname(labelHost)
        prodDef.setConaryNamespace(conaryNamespace)

        prodDef.loadFromRepository(client)
        self.failUnlessEqual(prodDef.preMigrateVersion,
            proddef.ProductDefinition.version)
        sio2 = StringIO.StringIO()
        prodDef.serialize(sio2)

        self.failUnlessEqual(sio.getvalue(), sio2.getvalue())

        # Test the platform's saving to repo
        prodDef.savePlatformToRepository(client)
        # Make sure we can still load the platform
        pld = proddef.PlatformDefinition()
        pld.loadFromRepository(client, "%s@%s:awesome-1.0" % (labelHost,
            conaryNamespace))
        self.failUnlessEqual(pld.sourceTrove,
            "platform-definition=/localhost@exm:awesome-1.0/%s-1" %
                proddef.ProductDefinition.version)

        # Test that if we save as version 2.0, we read back version 2.0
        prodDef.saveToRepository(client, version = '2.0')

        prodDef = proddef.ProductDefinition()
        prodDef.setProductShortname("awesome")
        prodDef.setProductVersion("1.0")
        prodDef.setConaryRepositoryHostname(labelHost)
        prodDef.setConaryNamespace(conaryNamespace)
        prodDef.loadFromRepository(client)
        self.failUnlessEqual(prodDef.preMigrateVersion, '2.0')

        # Now verify that the proddef trove version is 2.0 instead of latest
        label = prodDef.getProductDefinitionLabel()
        stream, nvf = prodDef._getStreamFromRepository(client, label)
        self.failUnlessEqual(nvf[0], 'product-definition:source')
        self.failUnlessEqual(str(nvf[1]), '/localhost@exm:awesome-1.0/2.0-1')

    def testPlatformSaveToRepository(self):
        self.openRepository()
        client = conaryclient.ConaryClient(self.cfg)
        pld = proddef.PlatformDefinition(fromStream = refPlatSerialize1)
        # Make sure rebase works with unicode strings too
        pld.saveToRepository(client, unicode(self.defLabel))

        pld2 = proddef.PlatformDefinition()
        pld2.loadFromRepository(client, unicode(self.defLabel))
        sio = StringIO.StringIO()
        pld2.serialize(sio)

    def testRebase(self):
        self.openRepository()
        client = conaryclient.ConaryClient(self.cfg)

        self.addComponent("foo:runtime")
        self.addCollection("foo", [":runtime"])

        self.addComponent("bar:runtime")
        self.addCollection("bar", [":runtime"])

        pld = proddef.PlatformDefinition(fromStream = refPlatSerialize1)
        pld.clearSearchPaths()
        pld.addSearchPath(troveName = "foo", label = str(self.defLabel))
        pld.clearFactorySources()
        pld.addFactorySource(troveName = "bar", label = str(self.defLabel))
        pld.saveToRepository(client, str(self.defLabel))

        pd = proddef.ProductDefinition(fromStream = refSerialize5)
        pd.rebase(client, str(self.defLabel), useLatest = True)
        self.failUnlessEqual(pd.getPlatformUseLatest(), True)

        self.failUnlessEqual(pd.getPlatformBaseFlavor(),
            'black-coffee,!cream,~sugar is: x86 x86_64')
        self.failUnlessEqual(pd.getPlatformSourceTrove(),
            "%s=/%s/%s-1" % (pld._troveName, self.defLabel,
                proddef.ProductDefinition.version))
        self.failUnlessEqual(
            [x.getTroveTup() for x in pd.getPlatformSearchPaths()],
            [('foo', 'localhost@rpl:linux', None)])
        self.failUnlessEqual(
            [x.getTroveTup() for x in pd.getPlatformFactorySources()],
            [('bar', 'localhost@rpl:linux', None)])

        # Muck with the platform's version, to make sure we are properly
        # snapshotting it
        pd.platform.sourceTrove = "%s=%s/9.99-1-1" % (pld._troveName,
            self.defLabel)

        # Rebase again, no label specified
        pd.rebase(client)
        self.failUnlessEqual(pd.getPlatformSourceTrove(),
            "%s=/%s/%s-1" % (pld._troveName, self.defLabel,
                proddef.ProductDefinition.version))

    def testRebase2(self):
        self.openRepository()
        client = conaryclient.ConaryClient(self.cfg)

        self.addComponent("foo:runtime")
        self.addCollection("foo", [":runtime"])

        self.addComponent("bar:runtime")
        self.addCollection("bar", [":runtime"])

        pld = proddef.PlatformDefinition(fromStream = refPlatSerialize1)
        pld.clearSearchPaths()
        pld.addSearchPath(troveName = "foo", label = str(self.defLabel))
        pld.clearFactorySources()
        pld.addFactorySource(troveName = "bar", label = str(self.defLabel))
        pld.containerTemplates[0].anacondaTemplatesTrove = "custom-value"
        pld.saveToRepository(client, str(self.defLabel))

        pd = proddef.ProductDefinition(fromStream = refSerialize5)
        # Add some stuff to the platform
        pd.addPlatformSearchPath("will-go-away", label = "no@such:label")
        pd.platform.addContainerTemplate(pd.imageType("amiImage"))
        self.failUnlessEqual(
            pd.platform.containerTemplates[0].containerFormat, 'amiImage')

        pd.rebase(client, str(self.defLabel), useLatest = True)

        self.failUnlessEqual(
            pd.platform.containerTemplates[0].containerFormat,
            'installableIsoImage')
        self.failUnlessEqual(
            pd.platform.containerTemplates[0].anacondaTemplatesTrove,
            'custom-value')
        pd.saveToRepository(client)

        pd2 = proddef.ProductDefinition()
        pd2.setProductShortname(pd.getProductShortname())
        pd2.setProductVersion(pd.getProductVersion())
        pd2.setConaryRepositoryHostname(pd.getConaryRepositoryHostname())
        pd2.setConaryNamespace(pd.getConaryNamespace())
        pd2.loadFromRepository(client)

        self.failUnlessEqual(
            pd2.platform.containerTemplates[0].containerFormat,
            'installableIsoImage')
        self.failUnlessEqual(
            pd2.platform.containerTemplates[0].anacondaTemplatesTrove,
            'custom-value')

    def testRebase3(self):
        # Same as testRebase2, but one of the search paths has a version
        self.openRepository()
        client = conaryclient.ConaryClient(self.cfg)

        self.addComponent("foo:runtime")
        self.addCollection("foo", [":runtime"])

        self.addComponent("bar:runtime")
        self.addCollection("bar", [":runtime"])

        pld = proddef.PlatformDefinition(fromStream = refPlatSerialize1)
        pld.clearSearchPaths()
        pld.addSearchPath(troveName = "foo", label = str(self.defLabel))
        pld.addSearchPath(troveName = "group-snapshotted",
            label=str(self.defLabel), version = '0.0.0')
        pld.clearFactorySources()
        pld.addFactorySource(troveName = "bar", label = str(self.defLabel))
        pld.containerTemplates[0].anacondaTemplatesTrove = "custom-value"
        pld.saveToRepository(client, str(self.defLabel))

        pd = proddef.ProductDefinition(fromStream = refSerialize5)
        pd.clearSearchPaths()
        # Add some stuff to the platform
        pd.addPlatformSearchPath("will-go-away", label = "no@such:label")
        pd.platform.addContainerTemplate(pd.imageType("amiImage"))
        self.failUnlessEqual(
            pd.platform.containerTemplates[0].containerFormat, 'amiImage')

        pd.rebase(client, str(self.defLabel))
        self.assertEquals(
            [ (x.troveName, x.version) for x in pd.getSearchPaths() ],
            [('foo', '1.0-1-1'), ('group-snapshotted', '0.0.0')])

    def testPlatformSnapshotVersions(self):
        self.openRepository()
        client = conaryclient.ConaryClient(self.cfg)

        self.addComponent("foo:runtime")
        self.addCollection("foo", [":runtime"])

        self.addComponent("bar:runtime")
        self.addCollection("bar", [":runtime"])

        pld = proddef.PlatformDefinition()
        pld.addSearchPath(troveName = "foo", label = str(self.defLabel))
        pld.addFactorySource(troveName = "bar", label = str(self.defLabel))

        pld.snapshotVersions(client)
        def check(pld):
            for x in pld.getSearchPaths():
                self.failUnlessEqual(x.troveName, 'foo')
                self.failUnlessEqual(x.label, str(self.defLabel))
                self.failUnlessEqual(x.version, '1.0-1-1')
            for x in pld.getFactorySources():
                self.failUnlessEqual(x.troveName, 'bar')
                self.failUnlessEqual(x.label, str(self.defLabel))
                self.failUnlessEqual(x.version, '1.0-1-1')
        check(pld)

        # We should be able to run this again
        pld.snapshotVersions(client)
        check(pld)

        sio = StringIO.StringIO()
        pld.serialize(sio)

        # Add a trove that doesn't exist
        pld.addSearchPath(troveName = "baz", label = str(self.defLabel))
        e = self.failUnlessRaises(proddef.SearchPathTroveNotFoundError,
            pld.snapshotVersions, client)
        self.failUnlessEqual(str(e), "baz=localhost@rpl:linux")

        sio.seek(0)
        pld = proddef.PlatformDefinition(fromStream = sio)

        # Add a trove from a label that doesn't exist
        pld.addSearchPath(troveName = "baz", label = 'foo.localhost@x:1')
        e = self.failUnlessRaises(proddef.RepositoryError,
            pld.snapshotVersions, client)
        self.failUnlessEqual(str(e),
        "Error occurred opening repository https://test:<PASSWD>@foo.localhost/conary/: Name or service not known")

    def test_saveToRepositoryWithSignature(self):
        from conary.lib import openpgpkey, openpgpfile
        # Create an empty secring
        secring = os.path.join(self.workDir, "secring.pgp")
        file(secring, "w")

        # Add our secret key
        sio = util.ExtendedStringIO()
        openpgpfile.parseAsciiArmor(secretKey, sio)
        sio.seek(0)
        msg = openpgpfile.PGP_Message(sio)
        key = msg.iterKeys().next()
        fingerprints = openpgpfile.addKeys([ key ], secring)

        self.failUnlessEqual(fingerprints,
            ['F290AD1A788C8B5A8C0346C2C1AC7699C515A5C1'])

        keyCache = openpgpkey.getKeyCache()
        self.mock(keyCache, 'privatePath', secring)


        # Callback
        class KeyCacheCallback(keyCache.callback.__class__):
            def getKeyPassphrase(slf, keyId, *args, **kwargs):
                return 'rpath'

        label = str(self.defLabel)

        pd = proddef.ProductDefinition(fromStream = XML)

        self.cfg.configLine('signatureKeyMap localhost@rpl:linux C515A5C1')

        self.openRepository()
        client = conaryclient.ConaryClient(self.cfg)

        self.mock(keyCache, 'callback', KeyCacheCallback())

        pd._saveToRepository(client, label, message = "Boo!\n")

        repos = client.getRepos()
        sourceTrvTup = repos.findTrove(versions.Label(label),
            ('product-definition:source', None, None))[0]
        sourceTrv = repos.getTrove(*sourceTrvTup)

        digitalSigs = [ x for x in sourceTrv.troveInfo.sigs.digitalSigs ]
        self.failUnlessEqual([ x[0] for x in digitalSigs ],
            fingerprints)

    def testPreserveExtraFiles(self):
        troveName = "platform-definition"
        # Make sure rebase works with unicode strings too
        troveLabel = unicode(self.defLabel)

        self.openRepository()
        client = conaryclient.ConaryClient(self.cfg)

        pld = proddef.PlatformDefinition(fromStream = refPlatSerialize1)
        self.failUnlessEqual(
            pld._getTroveTupFromRepository(client, troveLabel, allowMissing=True),
            None)

        pld.saveToRepository(client, troveLabel)


        extraFileContents = "somecontent\n"

        # Add a file
        coDir = os.path.join(self.workDir, troveName)
        self.checkout(troveName, troveLabel, dir = coDir)
        origDir = os.getcwd()
        try:
            os.chdir(coDir)
            file("somefile", "w").write(extraFileContents)
            self.addfile("somefile", text = True)
            self.commit()
        finally:
            os.chdir(origDir)

        # Save platform again
        pld.saveToRepository(client, unicode(self.defLabel))

        repos = client.getRepos()
        trvTup = repos.findTrove(None,
            (troveName + ":source", troveLabel, None))[0]
        self.failUnlessEqual(str(trvTup[1]),
            "/%s/%s-3" % (troveLabel, proddef.PlatformDefinition.version))
        self.failUnlessEqual(pld._getTroveTupFromRepository(client, troveLabel),
            trvTup)

        trv = repos.getTrove(*trvTup)
        self.failUnlessEqual(sorted([ x[1] for x in trv.iterFileList() ]),
            [proddef.PlatformDefinition._troveFileNames[0],
            'platform-definition.recipe',
             'somefile'])
        pathId, path, fileId, fileVer = [ x for x in trv.iterFileList()
            if x[1] == 'somefile' ][0]

        # Verify contents
        conts = repos.getFileContents([(fileId, fileVer)])[0]
        self.failUnlessEqual(conts.get().read(), extraFileContents)

class ProductDefinitionTest(BaseTest):

    def setUp(self):
        BaseTest.setUp(self)
        self._logLevel = 10

        self.productName = "My Awesome Appliance"
        self.productShortname = "awesome"
        self.productDescription = """
      This here is my awesome appliance.
      Is it not nifty.
      Worship the appliance.
   """

        self.productVersion = "1.0"
        self.productVersionDescription = """
      Version 1.0 features "stability" and "usefulness", which is a
      vast improvement over our pre-release code.
   """

        self.baseFlavor = """
      ~MySQL-python.threadsafe, ~X, ~!alternatives, !bootstrap,
      ~builddocs, ~buildtests, !cross, ~desktop, ~!dietlibc, ~!dom0, ~!domU,
      ~emacs, ~gcj, ~gnome, ~grub.static, ~gtk, ~ipv6, ~kde, ~!kernel.debug,
      ~kernel.debugdata, ~!kernel.numa, ~kernel.smp, ~krb, ~ldap, ~nptl,
      ~!openssh.smartcard, ~!openssh.static_libcrypto, pam, ~pcre, ~perl,
      ~!pie, ~!postfix.mysql, ~python, ~qt, ~readline, ~!sasl, ~!selinux,
      ~sqlite.threadsafe, ssl, ~tcl, tcpwrappers, ~tk, ~uClibc, !vmware,
      ~!xen, ~!xfce, ~!xorg-x11.xprint
   """.replace('\n', '').replace(' ', '')

        self.conaryRepositoryHostname = "product.example.com"
        self.conaryNamespace = "exm"
        self.imageGroup = "group-awesome-dist"
        self.sourceGroup = "group-source"

        self.stages = [dict(name='devel', labelSuffix='-devel'),
                       dict(name='qa', labelSuffix='-qa'),
                       dict(name='release', labelSuffix='')]

        self.searchPaths = \
                [dict(troveName='group-rap-standard', 
                      label='rap.rpath.com@rpath:linux-1',
                      isResolveTrove=None,
                      isGroupSearchPathTrove=None),
                 dict(troveName='group-postgres', 
                      label='products.rpath.com@rpath:postgres-8.2',
                      isResolveTrove=None,
                      isGroupSearchPathTrove=None),
                 dict(troveName='group-os',
                      label='conary.rpath.com@rpl:1',
                      isResolveTrove=None,
                      isGroupSearchPathTrove=False),
                 dict(troveName='foo',
                      label='localhost@linux:1',
                      isResolveTrove=False,
                      isGroupSearchPathTrove=True)]

        self.factorySources = \
                [dict(troveName='group-factories', 
                      label='products.rpath.com@rpath:factories-1'),
                ]

        self.buildDefinition = \
              [{'name' : 'x86 installableIso',
                'image': None,
                'stages' : ['devel', 'qa', 'release'],
                'imageGroup' : 'group-os',
                'sourceGroup' : 'group-source',
                'realImageGroup' : 'group-os',},
               {'name' : 'x86_64 installableIso',
                'image': None,
                'stages' : ['release'],
                'imageGroup' : 'group-foo',
                'sourceGroup' : 'group-source',
                'realImageGroup' : None},
               {'name' : 'x86 rawFsImage',
                'image': {'freespace' : 1234},
                'stages' : [],
                'imageGroup' : 'group-foo',
                'sourceGroup' : 'group-source',
                'realImageGroup' : None},
               {'name' : 'x86_64 rawHdImage',
                'image': {'autoResolve': True,
                                'baseFileName': 'proc-foo-moo'},
                'stages' : ['devel', 'qa', 'release'],
                'imageGroup' : 'group-os',
                'sourceGroup' : 'group-source',
                'realImageGroup' : 'group-os',
                },
               {'name' : 'x86_64 vmware',
                'image': {'autoResolve': True,
                                 'baseFileName': 'foobar'},
                'stages' : ['release'],
                'imageGroup' : 'group-bar',
                'sourceGroup' : 'group-source-bar',
                'realImageGroup' : 'group-bar',
                },
               {'name' : 'Virtual Iron Image',
                'image': None,
                'stages' : ['release'],
                'imageGroup' : 'group-bar',
                'sourceGroup' : 'group-source-bar',
                'realImageGroup' : 'group-bar',
                },
               ]

        self.pdFromXml = proddef.ProductDefinition(fromStream=XML)

    def testCompatImageTypeFile(self):
        from rpath_proddef import imageTypes
        image = imageTypes.Image({'containerFormat': 'installableIsoImage',
            'swapSize' : 1024})
        self.failUnlessEqual(image.containerFormat, 'installableIsoImage')
        self.failUnlessEqual(image.swapSize, 1024)

        # Check the interface mint uses currently
        self.failUnlessEqual(sorted(imageTypes.Image._attributes.items()),
            [
                ('amiHugeDiskMountpoint', str),
                ('anacondaCustomTrove', str),
                ('anacondaTemplatesTrove', str),
                ('autoResolve', bool),
                ('baseFileName', str),
                ('baseImageTrove', str),
                ('betaNag', bool),
                ('bugsUrl', str),
                ('buildOVF10', bool),
                ('diskAdapter', str),
                ('freespace', int),
                ('installLabelPath', str),
                ('maxIsoSize', int),
                ('mediaTemplateTrove', str),
                ('name', str),
                ('natNetworking', bool),
                ('platformIsoKitTrove', str),
                ('showMediaCheck', bool),
                ('swapSize', int),
                ('unionfs', bool),
                ('vhdDiskType', str),
                ('vmMemory', int),
                ('vmSnapshots', bool),
                ('zisofs', bool),
            ])

    def testValidate(self):
        schemaFiles = [
            resources.get_path(
                'xsd', 'rpd-%s.xsd' % proddef.ProductDefinition.version),
            '/usr/share/rpath_proddef/rpd-%s.xsd' %
                proddef.ProductDefinition.version
        ]
        docs = [ XML, refSerialize1, refSerialize11, refSerialize12]
        for schemaFile in schemaFiles:
            if not os.path.exists(schemaFile):
                continue
            for doc in docs:
                schema = proddef.etree.XMLSchema(file = schemaFile)
                tree = proddef.etree.parse(StringIO.StringIO(doc))
                self.failUnless(schema.validate(tree), str(schema.error_log))
            break
        else: # for
            raise testhelp.SkipTestException("Unable to validate schema - "
                                              "schema file not found")

    def testLoad_MissingVersion(self):
        data = XML.replace('version="%s"' % proddef.ProductDefinition.version,
            '')
        pd = proddef.ProductDefinition(fromStream = data)
        self.failUnlessEqual(pd.getProductName(), 'My Awesome Appliance')

    def testEqualsToOtherType(self):
        pd = proddef.ProductDefinition(XML)
        self.failIf(pd == 1)

    def testLoad_UnknownVersion(self):
        data = XML.replace('version="%s"' % proddef.ProductDefinition.version,
            'version="0.1.nosuchversion"')
        self.failUnlessRaises(proddef.InvalidSchemaVersionError,
            proddef.ProductDefinition, fromStream = data)

    def testBaseFlavor(self):
        """
        Test that baseFlavor got set after parsing
        """
        self.failUnlessEqual(self.pdFromXml.getBaseFlavor(), self.baseFlavor)

    def testSourceGroup(self):
        """
        Test that source group is set.
        """
        self.failUnlessEqual(self.pdFromXml.getSourceGroup(), self.sourceGroup)

    def testXmlEquality(self):
        """
        The same data must provide the same XML reprentation exactly
        both for comparison purposes and to be confident that we
        are processing the data stably.
        """
        stream = StringIO.StringIO()
        self.pdFromXml.serialize(stream)
        stream.seek(0)

        pd = proddef.ProductDefinition(fromStream = stream)
        stream2 = StringIO.StringIO()
        pd.serialize(stream2)
        self.assertEquals(stream.getvalue(), stream2.getvalue())

    def testParseStream(self):
        """
        """
        prd = proddef.ProductDefinition(fromStream = XML,
            validate = True, schemaDir = self.schemaDir)
        self.failUnlessEqual(prd.getBaseFlavor(), self.baseFlavor)

        ref = [ ("devel", "-devel"),
                ("qa", "-qa"),
                ("release", ""), ]
        self.failUnlessEqual(
            [ dict(name = x.name, labelSuffix = x.labelSuffix) for x in prd.getStages() ],
            self.stages)

        ref = [ ("group-rap-standard", "rap.rpath.com@rpath:linux-1"),
                ("group-postgres", "products.rpath.com@rpath:postgres-8.2"),]

        self.failUnlessEqual(
            [ dict(troveName = x.troveName, label = x.label,
                   isResolveTrove=x.isResolveTrove,
                   isGroupSearchPathTrove=x.isGroupSearchPathTrove)
                for x in prd.getSearchPaths() ], self.searchPaths)

        self.failUnlessEqual(
            [ dict(troveName = x.troveName, label = x.label)
                for x in prd.getFactorySources() ], self.factorySources)


        ref = [ ("is: x86", True, ("installableIsoImage", {})),
                ("is: x86_64", True, ("installableIsoImage", {})),
                ("~xen, ~domU is: x86", False, ("rawFsImage", {})),
                ("~xen, ~domU is: x86 x86_64", True, ("rawHdImage",
                    dict(autoResolve=True, baseFileName = "/proc/foo/moo"))),
                ("~vmware is: x86 x86_64", True, ("vmwareImage",
                    dict(autoResolve=True, baseFileName = "foobar"))),
                ("is: x86 x86_64", True, ("virtualIronImage", dict())) ]

        actual = [
            { 'name' : x.getBuildName(),
              'image': x.image and x.image.getFields(),
              'stages' : x.getBuildStages(),
              'imageGroup' : x.getBuildImageGroup(),
              'sourceGroup' : x.getBuildSourceGroup(),
              'realImageGroup' : x.imageGroup, }
                    for x in prd.getBuildDefinitions()
        ]
        self.failUnlessEqual(actual, self.buildDefinition)

        builds =  [ x.name for x in prd.getBuildsForStage('release') ]
        self.failUnlessEqual(builds,
            ['x86 installableIso', 'x86_64 installableIso', 'x86_64 rawHdImage', 'x86_64 vmware', 'Virtual Iron Image'])

        builds =  [ x.name for x in prd.getBuildsForStage('qa') ]
        self.failUnlessEqual(builds,
            ['x86 installableIso', 'x86_64 rawHdImage'])

        builds =  [ x.name for x in prd.getBuildsForStage('devel') ]
        self.failUnlessEqual(builds,
            ['x86 installableIso', 'x86_64 rawHdImage'])

        builds =  [ x.name for x in prd.getBuildsForStage('nosuchstage') ]
        self.failUnlessEqual(builds, [])

    def testSerialize1(self):
        prd = proddef.ProductDefinition()
        prd.setProductName("My Awesome Appliance")
        prd.setProductShortname("awesome")
        prd.setProductDescription("""
      This here is my awesome appliance.
      Is it not nifty?
      Worship the appliance.
  """)
        prd.setProductVersion("1.0")
        productVersionDescription = """
      Version 1.0 features "stability" and "usefulness", which is a
      vast improvement over our pre-release code.
  """
        prd.setProductVersionDescription(productVersionDescription)
        self.failUnlessEqual(prd.getProductVersionDescription(),
            productVersionDescription)

        prd.setConaryRepositoryHostname("product.example.com")
        prd.setConaryNamespace("exm")

        prd.setImageGroup('group-awesome-dist')
        prd.setBaseFlavor('is: x86 x86_64')

        prd.addStage(name = 'devel', labelSuffix = '-devel')
        prd.addStage(name = 'qa', labelSuffix = '-qa')
        prd.addStage(name = 'release', labelSuffix = '')

        prd.addSearchPath(troveName = 'group-foo', label = 'localhost@s:1',
            version = "1-1-1")
        prd.addSearchPath(troveName = 'group-bar', label = 'localhost@s:2',
            version = "1-1-1")

        prd.addContainerTemplate(prd.imageType('installableIsoImage'))
        prd.addArchitecture(name = 'x86_64', displayName = '64 bit',
                flavor = "is: x86 x86_64")
        prd.addFlavorSet(name = 'cheese', displayName = 'cheese',
                flavor = '~cheese')

        prd.addBuildDefinition(architectureRef = 'x86_64',
            imageGroup = 'group-foo',
            name = 'x86_64 build',
            containerTemplateRef = 'installableIsoImage',
            stages = ['qa', 'release'])

        stream = StringIO.StringIO()
        prd.serialize(stream)
        self.assertXMLEquals(stream.getvalue(), refSerialize1)

        prd.setSourceGroup('group-awesome')
        stream = StringIO.StringIO()
        prd.serialize(stream)
        self.assertXMLEquals(stream.getvalue(), refSerialize11)

    def testSerialize2(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        stream = StringIO.StringIO()
        prd.serialize(stream)
        self.assertXMLEquals(stream.getvalue(), refSerialize1)

    def testSerialize3(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize2)
        stream = StringIO.StringIO()
        prd.serialize(stream)
        self.assertXMLEquals(stream.getvalue(), refSerialize1)

        nref = refSerialize1.replace(
            'xmlns="http://www.rpath.com/permanent/rpd-%s.xsd"' %
                proddef.ProductDefinition.version,
            'xmlns="blobbedygoo"')
        prd = proddef.ProductDefinition(fromStream = nref)
        stream = StringIO.StringIO()
        prd.serialize(stream)

        self.failIf(stream.getvalue() == nref,
                "expected namespace to be corrected")

    def testSerialize4(self):
        # No factory source in the product definition, it should not show up
        # in the XML
        prd = proddef.ProductDefinition(fromStream = refSerialize1,
            validate = True, schemaDir = self.schemaDir)
        del prd.factorySources[:]
        stream = StringIO.StringIO()
        prd.serialize(stream)
        # Erase the reference to factorySources from XML too
        ref = refSerialize1.replace("""
  <factorySources>
    <factorySource troveName="group-factories" label="products.rpath.com@rpath:factories-1"/>
  </factorySources>""", "")
        self.assertXMLEquals(stream.getvalue(), ref)

        prd = proddef.ProductDefinition(fromStream = ref,
            validate = True, schemaDir = self.schemaDir)
        del prd.factorySources[:]
        stream = StringIO.StringIO()
        prd.serialize(stream)
        self.assertXMLEquals(stream.getvalue(), ref)

    def testSerialize5(self):
        # Add some architectures and some container templates
        prd = proddef.ProductDefinition(fromStream = refSerialize1,
            validate = True, schemaDir = self.schemaDir)
        prd.addArchitecture(name = "x86",
                displayName = "32 bit",
            flavor="grub.static, dietlibc is:x86(i486, i586, cmov, mmx, sse)")
        prd.addArchitecture(name = "x86_64",
                displayName = "64 bit",
            flavor="!grub.static, !dietlibc is:x86_64 x86(i486, i586, cmov, mmx, sse)")
        prd.addContainerTemplate(prd.imageType('rawFsImage'))
        prd.addFlavorSet(name = "xen domU", displayName = "xen domU",
                flavor = "~xen, ~domU, ~!vmware")
        prd.addFlavorSet(name = "vmware", displayName = "vmware",
                flavor = "~vmware, ~!xen, ~!domU")
        stream = StringIO.StringIO()
        prd.serialize(stream)
        self.assertXMLEquals(stream.getvalue(), refSerialize6)

        stream.seek(0)
        prd2 = proddef.ProductDefinition(fromStream = stream)
        self.failUnlessEqual(
            [ (x.name, x.flavor) for x in prd.getArchitectures() ],
            [ (x.name, x.flavor) for x in prd2.getArchitectures() ])
        self.failUnlessEqual(prd.getSecondaryLabels(), [])

        # Validate too
        stream.seek(0)
        prd3 = proddef.ProductDefinition(fromStream = stream,
            validate = True, schemaDir = self.schemaDir)

    def testSerialize7(self):
        # Test secondary labels
        prd = proddef.ProductDefinition(fromStream = refSerialize8,
            validate = True, schemaDir = self.schemaDir)
        self.failUnlessEqual(
            [ (x.getName(), x.getLabel()) for x in prd.getSecondaryLabels() ],
            [ ('Xen', '-xen'), ('VMware', 'my@label:vmware')])
        # Make sure we expand labels properly
        self.failUnlessEqual(prd.getSecondaryLabelsForStage('devel'),
            [ ('Xen', 'product.example.com@exm:awesome-1.0-xen-devel'),
              ('VMware', 'my@label:vmware-devel')])
        self.failUnlessEqual(prd.getSecondaryLabelsForStage('release'),
            [ ('Xen', 'product.example.com@exm:awesome-1.0-xen'),
              ('VMware', 'my@label:vmware')])

        # Serialize
        sio = StringIO.StringIO()
        prd.serialize(sio)
        self.assertXMLEquals(sio.getvalue(), refSerialize8)

        # Test API for adding secondary labels
        prd.addSecondaryLabel('Floo', '-floo')
        self.failUnlessEqual(prd.getSecondaryLabelsForStage('devel'),
            [ ('Xen', 'product.example.com@exm:awesome-1.0-xen-devel'),
              ('VMware', 'my@label:vmware-devel'),
              ('Floo', 'product.example.com@exm:awesome-1.0-floo-devel'),
              ])
        prd.clearSecondaryLabels()
        self.failUnlessEqual(prd.getSecondaryLabelsForStage('devel'),
            [])

    def testSerialize8(self):
        # Test promote maps
        prd = proddef.ProductDefinition(fromStream = refSerialize9,
            validate = True, schemaDir = self.schemaDir)

        promMaps = [('myblah', 'host@myblah:devel'), ('myblip', 'host@myblip:devel')]

        stage = prd.getStage('devel')
        self.failUnlessEqual(
            [ (x.getMapName(), x.getMapLabel()) for x in stage.getPromoteMaps() ],
            promMaps)
        stage = prd.getStage('qa')
        self.failUnlessEqual(
            [ (x.getMapName(), x.getMapLabel()) for x in stage.getPromoteMaps() ],
            [])

        # Serialize
        sio = StringIO.StringIO()
        prd.serialize(sio)
        self.assertXMLEquals(sio.getvalue(), refSerialize9)

        promMaps2 = promMaps + [('my@label:1', 'your@label:2')]
        # Test API for adding promote maps
        prd.addStage(name = 'hotfix', labelSuffix = "-hotfix",
            promoteMaps = promMaps2)
        stage = prd.getStage('hotfix')
        self.failUnlessEqual(
            [ (x.getMapName(), x.getMapLabel()) for x in stage.getPromoteMaps() ],
            promMaps2)

        prd.addSecondaryLabel('Floo', '-floo')

        sio = StringIO.StringIO()
        prd.serialize(sio)
        sio.seek(0)

        prd = proddef.ProductDefinition(fromStream = sio,
            validate = True, schemaDir = self.schemaDir)

        self.failUnlessEqual(prd.getSecondaryLabelsForStage('devel'),
              [('Floo', 'product.example.com@exm:awesome-1.0-floo-devel'),
              ])

        stage = prd.getStage('hotfix')
        self.failUnlessEqual(
            [ (x.getMapName(), x.getMapLabel()) for x in stage.getPromoteMaps() ],
            promMaps2)

    def testSerializeMissingSchemaDir(self):
        prd = proddef.ProductDefinition(fromStream = XML)
        prd.schemaDir = "/no/such/dir"
        stderr = StringIO.StringIO()
        self.mock(sys, 'stderr', stderr)
        out = StringIO.StringIO()
        prd.serialize(out)
        self.unmock()
        self.failUnlessEqual(stderr.getvalue(),
            "Warning: unable to validate schema: directory /no/such/dir missing")

    def testPlatSerialize6(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize4,
            validate = True, schemaDir = self.schemaDir)
        prd.addArchitecture(name = "x86",
                displayName = "32 bit",
            flavor="grub.static, dietlibc is:x86(i486, i586, cmov, mmx, sse)")
        prd.addArchitecture(name = "x86_64",
                displayName = "64 bit",
            flavor="!grub.static, !dietlibc is:x86_64 x86(i486, i586, cmov, mmx, sse)")
        prd.addContainerTemplate(prd.imageType("amiImage",
                                            dict(freespace = '1024')))
        prd.addFlavorSet(name = "xen domU",
                displayName = "xen",
            flavor = "~xen, ~domU, ~!vmware")
        prd.addFlavorSet(name = "vmware",
                displayName = "vmware",
            flavor = "~vmware, ~!xen, ~!domU")

        # Save it as a platform
        pld = prd.toPlatformDefinition()

        stream = StringIO.StringIO()
        pld.serialize(stream)
        self.assertXMLEquals(stream.getvalue(), refPlatSerialize6)

    def testSerialize6(self):
        # Add build definitions with references to arches
        prd = proddef.ProductDefinition(fromStream = refSerialize6,
            validate = True, schemaDir = self.schemaDir)
        prd.addBuildDefinition(name = "build1", architectureRef = "x86",
            containerTemplateRef = "installableIsoImage",
            stages = ['devel', 'qa', 'release'],
            flavorSetRef = "cheese")
        buildDef = [x for x in prd.getBuildDefinitions() if x.name == "build1"][0]
        self.failUnlessEqual(buildDef.getBuildSourceGroup(), None)
        self.failUnlessEqual(buildDef.architectureRef, "x86")
        self.assertEquals(buildDef.containerTemplateRef, "installableIsoImage")
        self.assertEquals(buildDef.flavorSetRef, "cheese")
        self.failUnlessEqual(buildDef.getBuildBaseFlavor(),
                '~cheese,dietlibc,grub.static is: x86(cmov,i486,i586,mmx,sse)')

        # Missing ref
        e = self.failUnlessRaises(proddef.ArchitectureNotFoundError,
            prd.addBuildDefinition, name = "build2", architectureRef = 'XXX')
        self.failUnlessEqual(str(e), 'XXX')

        e = self.failUnlessRaises(proddef.FlavorSetNotFoundError,
            prd.addBuildDefinition, name = "build2", flavorSetRef = 'XXX')
        self.failUnlessEqual(str(e), 'XXX')

        stream = StringIO.StringIO()
        prd.serialize(stream)
        self.assertXMLEquals(stream.getvalue(), refSerialize7)

        # And parse it too
        stream.seek(0)
        prd = proddef.ProductDefinition(fromStream = stream,
            validate = True, schemaDir = self.schemaDir)
        stream.truncate(0)
        prd.serialize(stream)
        self.assertXMLEquals(stream.getvalue(), refSerialize7)

        # Save platform def
        pld = prd.toPlatformDefinition()
        prd._rebase('some@new:label', pld)
        stream.truncate(0)
        prd.serialize(stream)

        stream.seek(0)
        prd = proddef.ProductDefinition(fromStream = stream,
            validate = True, schemaDir = self.schemaDir)

        self.failUnlessEqual(
            [ (x.name, x.flavor) for x in prd.platform.getArchitectures() ],
            [ (x.name, x.flavor) for x in prd.getArchitectures() ])
        self.failUnlessEqual(
            [ (x.name, x.flavor) for x in prd.platform.getFlavorSets() ],
            [ ('cheese', '~cheese')])
        self.failUnlessEqual(
            [ (x.name, x.flavor) for x in prd.getFlavorSets() ],
            [ ('cheese', '~cheese'), ('xen domU', '~xen, ~domU, ~!vmware'),
              ('vmware', '~vmware, ~!xen, ~!domU')])

    def testBaseLabel(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1,
            validate = True, schemaDir = self.schemaDir)
        stream = StringIO.StringIO()
        prd.serialize(stream)
        assert 'baseLabel' not in stream.getvalue()

        # baseLabel is not the recommended case, but it should work...
        refSerializeBaseLabel = refSerialize1.replace(
'''  <imageGroup>group-awesome-dist</imageGroup>''',
'''  <imageGroup>group-awesome-dist</imageGroup>
  <baseLabel>some@other:label</baseLabel>''')
        prd = proddef.ProductDefinition(fromStream = refSerializeBaseLabel,
            validate = True, schemaDir = self.schemaDir)
        self.failUnlessEqual(prd.getBaseLabel(), 'some@other:label')
        stream = StringIO.StringIO()
        prd.serialize(stream)
        self.assertXMLEquals(stream.getvalue(), refSerializeBaseLabel)

        prd.setBaseLabel(None)
        stream = StringIO.StringIO()
        prd.serialize(stream)
        self.assertXMLEquals(stream.getvalue(), refSerialize1)

        prd.setBaseLabel('yet@another:label')
        stream = StringIO.StringIO()
        prd.serialize(stream)
        self.assertXMLEquals(stream.getvalue(),
            refSerializeBaseLabel.replace('some@other:label',
                                          'yet@another:label'))

        self.failUnlessEqual(prd.getProductDefinitionLabel(),
            'yet@another:label')

        self.failUnlessEqual(prd.getDefaultLabel(),
            'yet@another:label-devel')

        self.failUnlessEqual(prd.getLabelForStage('devel'),
            'yet@another:label-devel')
        self.failUnlessEqual(prd.getLabelForStage('qa'),
            'yet@another:label-qa')
        self.failUnlessEqual(prd.getLabelForStage('release'),
            'yet@another:label')


    def testBuildDefinitionFlavors(self):
        prd = proddef.ProductDefinition()
        labelHost = 'localhost'
        conaryNamespace = 'exm'

        prd.setProductShortname("awesome")
        prd.setProductVersion("1.0")
        prd.setConaryRepositoryHostname(labelHost)
        prd.setConaryNamespace(conaryNamespace)

        prd.setBaseFlavor('platb1,~platb2,~!platb3,!platb4')
        prd.addArchitecture(name = 'a1',
                displayName = 'a1',
            flavor = 'plata1,~plata2,~!plata3,!plata4')
        prd.addContainerTemplate(prd.imageType('xenOvaImage'))
        prd.addFlavorSet(name = 't1',
                displayName = 't1',
            flavor = 'platt1,~platt2,~!platt3,!platt4')
        prd.addBuildTemplate(name = "bt1", displayName = 'bt1',
                architectureRef = "a1", containerTemplateRef = 'liveIso')
        # Add a duplicate build template, the platform should filter it out
        prd.addBuildTemplate(name = "bt1", displayName = 'bt1',
                architectureRef = "a1", containerTemplateRef = 'liveIso')

        # Save platform definition
        pld = prd.toPlatformDefinition()

        # Another product
        prd = proddef.ProductDefinition()
        prd.setBaseFlavor('prodb1,~prodb2,~!prodb3,!prodb4')
        prd.addArchitecture(name = 'a1',
                displayName = 'a1',
            flavor = 'proda1,~proda2,~!proda3,!proda4')
        prd.addContainerTemplate(prd.imageType('xenOvaImage'))
        prd.addFlavorSet(name = 't1',
                displayName = 't1',
            flavor = 'prodt1,~prodt2,~!prodt3,!prodt4')

        prd.addBuildDefinition(name = "b1", architectureRef = "a1",
            flavorSetRef = "t1",
            containerTemplateRef = 'xenOvaImage',
            stages = ['devel', 'qa', 'release'])
        buildDef = [x for x in prd.getBuildDefinitions() if x.name == "b1"][0]
        self.failUnlessEqual(buildDef.getBuildBaseFlavor(), 'proda1,~proda2,~!proda3,!proda4,prodb1,~prodb2,~!prodb3,!prodb4,prodt1,~prodt2,~!prodt3,!prodt4')

        # Add the platform definition
        prd._rebase('some@new:label', pld)
        self.failUnlessEqual(buildDef.getBuildBaseFlavor(), 'plata1,~plata2,~!plata3,!plata4,platb1,~platb2,~!platb3,!platb4,platt1,~platt2,~!platt3,!platt4,proda1,~proda2,~!proda3,!proda4,prodb1,~prodb2,~!prodb3,!prodb4,prodt1,~prodt2,~!prodt3,!prodt4')

        # Catch the runtime error too
        prd.clearBuildDefinition()
        prd.addBuildDefinition(name = "b1", architectureRef = "a1",
            flavorSetRef = "t1",
            image = 'xenOvaImage',
            stages = ['devel', 'qa', 'release'])
        buildDef = [x for x in prd.getBuildDefinitions() if x.name == "b1"][0]

        # Test some more corner cases
        e = self.failUnlessRaises(proddef.ArchitectureNotFoundError,
            prd.getPlatformArchitecture, 'XXX')
        self.failUnlessEqual(prd.getPlatformArchitecture('XXX', None), None)

        e = self.assertRaises(proddef.ContainerTemplateNotFoundError,
                prd.getContainerTemplate, 'XXX')
        self.assertEquals(prd.getContainerTemplate('XXX', None), None)

        e = self.assertRaises(proddef.FlavorSetNotFoundError,
                prd.getFlavorSet, 'XXX')
        self.assertEquals(prd.getFlavorSet('XXX', None), None)

        e = self.assertRaises(proddef.BuildTemplateNotFoundError,
                prd.getBuildTemplate, 'XXX')
        self.assertEquals(prd.getBuildTemplate('XXX', None), None)

    def testStageLabels(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        self.assertEquals(prd.getLabelForStage("devel"),
                "product.example.com@exm:awesome-1.0-devel")
        self.assertEquals(prd.getLabelForStage("qa"),
                "product.example.com@exm:awesome-1.0-qa")
        self.assertEquals(prd.getLabelForStage("release"),
                "product.example.com@exm:awesome-1.0")
        self.assertRaises(proddef.StageNotFoundError,
                prd.getLabelForStage, "nonexistent")

    def testClearStages(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        self.assertNotEquals(prd.stages, [])
        prd.clearStages()
        self.assertEquals(prd.stages, [])

    def testClearFactorySources(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        prd.addFactorySource(troveName = 'group-factories')
        self.assertNotEquals(prd.factorySources, [])
        prd.clearFactorySources()
        self.assertEquals(prd.factorySources, [])

    def testClearBuildDefinition(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        self.assertNotEquals(prd.buildDefinition, [])
        prd.clearBuildDefinition()
        self.assertEquals(prd.buildDefinition, [])

    def testClearSearchPaths(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        self.assertNotEquals(prd.searchPaths, [])
        prd.clearSearchPaths()
        self.assertEquals(prd.searchPaths, [])

    def testClearArchitectures(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize6)
        self.assertNotEquals(prd.architectures, [])
        self.failUnlessEqual(prd.hasArchitecture('x86'), True)
        self.failUnlessEqual(prd.hasArchitecture('XXX'), False)
        self.failUnlessEqual(prd.getArchitecture('XXX', None), None)

        self.failUnlessEqual(prd.getContainerTemplate('XXX', None), None)

        self.assertNotEquals(prd.containerTemplates, [])

        prd.clearArchitectures()
        self.assertEquals(prd.architectures, [])

        prd.addContainerTemplate(prd.imageType('installableIsoImage'))
        prd.clearContainerTemplates()
        self.assertEquals(prd.containerTemplates, [])

    def testPlatform(self):
        platFlv = 'black-coffee,!cream,~sugar'
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        prd.setPlatformBaseFlavor(platFlv)
        prd.setPlatformSourceTrove("foo=bar@baz:1")
        stream = StringIO.StringIO()
        prd.serialize(stream)
        self.assertXMLEquals(stream.getvalue(), refSerialize3)
        self.failUnlessEqual(prd.getBaseFlavor(),
            'black-coffee,!cream,~sugar is: x86 x86_64')

        prd.addPlatformFactorySource(troveName='a', label='b')
        prd.addPlatformSearchPath(troveName='c', label='d')
        prd.setPlatformUseLatest(True)

        stream = StringIO.StringIO()
        prd.serialize(stream)
        self.assertXMLEquals(stream.getvalue(), refSerialize10)

    def testLoadPlatform(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize4)

        self.failUnlessEqual(prd.getPlatformBaseFlavor(),
            "black-coffee,!cream,~sugar")
        self.failUnlessEqual(prd.getPlatformUseLatest(), True)
        self.failUnlessEqual(prd.getPlatformSourceTrove(), 'foo=bar@baz:1')

        self.failUnlessEqual(
            [(x.troveName, x.label) for x in prd.getPlatformSearchPaths()],
            [('c', 'd')])

        self.failUnlessEqual(
            [(x.troveName, x.label) for x in prd.getPlatformFactorySources()],
            [('a', 'b')])

    def testToPlatformDefinition(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize4)
        pld = prd.toPlatformDefinition()

        self.failUnlessEqual(pld.getBaseFlavor(),
            'black-coffee,!cream,~sugar is: x86 x86_64')

        self.failUnlessEqual(
            [ (x.troveName, x.label) for x in pld.getSearchPaths()],
            [('group-foo', 'product.example.com@exm:awesome-1.0'),
             ('group-awesome-dist', 'product.example.com@exm:awesome-1.0'),
             ('group-foo', 'localhost@s:1'),
             ('group-bar', 'localhost@s:2')]
        )
        self.failUnlessEqual(
            [ (x.troveName, x.label) for x in pld.getFactorySources()],
            [ ('a', 'b')]
        )

        # reintroduce a baseFlavor
        pld.setBaseFlavor('black-coffee,!cream,~sugar is: x86 x86_64')
        sio = StringIO.StringIO()
        pld.serialize(sio)
        self.assertXMLEquals(sio.getvalue(), refPlatSerialize2)

    def testToPlatformDefinition1(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize4)
        pld = prd.toPlatformDefinition()

        # migration code wipes baseFlavor if it appears to need to be migrated
        self.failUnlessEqual(pld.getBaseFlavor(), 'black-coffee,!cream,~sugar is: x86 x86_64')

    def testToPlatformDefinition4(self):
        """Override platformInformation in product"""
        prd = proddef.ProductDefinition(fromStream = refToPlat4)
        info = copy.deepcopy(prd.getPlatformInformation())
        info.set_bootstrapTrove(['spam'])
        prd.setPlatformInformation(info)

        pld = prd.toPlatformDefinition()
        self.failUnlessEqual(
                pld.getPlatformInformation().bootstrapTroves,
                [('spam', None, None)])

    def testToPlatformDefinition5(self):
        # RBL-7550
        prd = proddef.ProductDefinition(fromStream = refToPlat4)
        pld = proddef.PlatformDefinition(fromStream = refPlatSerialize1)
        nlabel = 'some@label:1'
        prd._rebase(nlabel, pld)
        # Get rid of this product's platform info, to force reading from the
        # platform
        prd._rootObj.platformInformation = None

        npld = prd.toPlatformDefinition()
        sio = StringIO.StringIO()
        npld.serialize(sio)
        self.failUnlessEqual(npld.getPlatformInformation().originLabel,
            'bar@baz:1')
        self.failUnlessEqual(npld.getPlatformInformation().getOriginLabel(),
            versions.Label('bar@baz:1'))

    def testLoadPlatformDefinition(self):
        pld = proddef.PlatformDefinition(fromStream = refPlatSerialize1)
        sio = StringIO.StringIO()
        pld.serialize(sio)
        self.assertXMLEquals(sio.getvalue(), refPlatSerialize1)

    def testLoadPlatformDefinitionMangledNs(self):
        nref = refPlatSerialize1.replace(
            'xmlns="http://www.rpath.com/permanent/rpd-1.3.xsd"',
            'xmlns="blobbedygoo"')
        pld = proddef.PlatformDefinition(fromStream = nref)
        stream = StringIO.StringIO()
        pld.serialize(stream)

        # We changed the namespace, we should expect no match
        self.assertXMLEquals(stream.getvalue(), nref)

    def testRebaseMissingLabel(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        self.failUnlessRaises(proddef.PlatformLabelMissingError,
            prd.rebase, None)

    def test_rebase(self):
        pd = proddef.ProductDefinition(fromStream = refSerialize4)
        pld = proddef.PlatformDefinition(fromStream = refPlatSerialize1)
        # We need to set this by hand, it normally comes from
        # loadFromRepository
        nlabel = 'some@label:1'
        sourceTrove = "%s=/%s/1.2.3-4" % (pld._troveName, nlabel)
        pld.sourceTrove = sourceTrove

        pld.addArchitecture(name = "x86",
            displayName = '32 bit',
            flavor="grub.static, dietlibc is:x86(i486, i586, cmov, mmx, sse)")
        pld.addArchitecture(name = "x86_64",
            displayName = '64 bit',
            flavor="!grub.static, !dietlibc is:x86_64 x86(i486, i586, cmov, mmx, sse)")
        img = pld.imageType('rawHdImage')
        pld.addContainerTemplate(img)
        pld.addFlavorSet("xen", "Xen", "~xen, ~domU, ~!vmware")
        pld.addBuildTemplate("xen domU", "Xen domU", 'x86', 'rawHdImage')

        pd._rebase(nlabel, pld, useLatest = True)
        self.failUnlessEqual(pd.getPlatformSourceTrove(), sourceTrove)
        self.failUnlessEqual(pd.getPlatformBaseFlavor(),
            'black-coffee,!cream,~sugar is: x86 x86_64')
        self.failUnlessEqual(pd.getPlatformUseLatest(), True)
        self.failUnlessEqual(
            [ (x.troveName, x.label) for x in pd.getPlatformSearchPaths() ],
            [('group-foo', 'product.example.com@exm:awesome-1.0'),
             ('group-awesome-dist', 'product.example.com@exm:awesome-1.0'),
             ('group-foo', 'localhost@s:1'),
             ('group-bar', 'localhost@s:2')
            ]
        )
        self.failUnlessEqual(
            [ (x.troveName, x.label) for x in pd.getPlatformFactorySources() ],
            [ ('a', 'b') ]
        )

        self.failUnlessEqual(
            [ (x.name, x.flavor) for x in pd.platform.getArchitectures() ],
            [ (x.name, x.flavor) for x in pld.getArchitectures() ],
        )
        self.failUnlessEqual(
            [ (x.name, x.flavor) for x in pd.platform.getFlavorSets() ],
            [ (x.name, x.flavor) for x in pld.getFlavorSets() ],
        )
        self.assertEquals(
            [x.containerFormat for x in pd.platform.getContainerTemplates()],
            [x.containerFormat for x in pld.getContainerTemplates()],
        )

    def testNoPlatform(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        self.failUnlessEqual(prd.getPlatformSourceTrove(), None)
        self.failUnlessEqual(prd.getPlatformUseLatest(), None)
        self.failUnlessEqual(prd.getPlatformBaseFlavor(), None)
        self.failUnlessEqual(prd.getPlatformSearchPaths(), [])
        self.failUnlessEqual(prd.getPlatformFactorySources(), [])
        sio = StringIO.StringIO()
        prd.serialize(sio)
        self.assertXMLEquals(sio.getvalue(), refSerialize1)

        prd.clearPlatformSearchPaths()
        prd.clearPlatformFactorySources()

        prd.addPlatformSearchPath(troveName='a', label='b')

        prd.clearPlatformSearchPaths()
        prd.clearPlatformFactorySources()

        prd.platform = None
        prd.addPlatformFactorySource(troveName='a', label='b')

        prd.clearPlatformSearchPaths()
        prd.clearPlatformFactorySources()

    def testToPlatformDefinition2(self):
        # Platform definition doesn't exist in the product definition
        # Just make sure we don't explode
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        pl = prd.toPlatformDefinition()

    def testToPlatformDefinition3(self):
        # Platform definition exists, overrides don't
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        pl = prd.toPlatformDefinition()
        prd._rebase('some-label', pl, useLatest = False)
        # Get rid of the overrides
        bf = prd.getBaseFlavor()
        psp = prd.searchPaths
        pfs = prd.factorySources
        prd.baseFlavor = None

        prd.clearSearchPaths()
        prd.clearFactorySources()

        pl2 = prd.toPlatformDefinition()
        self.failUnlessEqual(pl2.getBaseFlavor(), bf)
        # Make sure we get the base flavor from the platform
        self.failUnlessEqual(prd._rootObj.baseFlavor, None)
        self.failUnlessEqual(prd.getBaseFlavor(), bf)

        self.failUnlessEqual(prd.searchPaths, [])
        exp = [ ('group-foo', 'product.example.com@exm:awesome-1.0', None),
            ('group-awesome-dist', 'product.example.com@exm:awesome-1.0', None)]
        exp.extend((x.troveName, x.label, x.version) for x in psp)
        self.failUnlessEqual(
            [ (x.troveName, x.label, x.version) for x in prd.getSearchPaths() ],
            exp)

        self.failUnlessEqual(prd.factorySources, [])
        exp = []
        exp.extend((x.troveName, x.label, x.version) for x in pfs)
        self.failUnlessEqual(
            [ (x.troveName, x.label, x.version) for x in prd.getFactorySources() ],
            exp)

    def testDefaultLabel(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        self.assertEquals(prd.getDefaultLabel(),
                "product.example.com@exm:awesome-1.0-devel")

    def testDefaultLabelEmptyProductDefinition(self):
        emptyprd = proddef.ProductDefinition()
        self.assertRaises(proddef.StageNotFoundError,
                emptyprd.getDefaultLabel)

    def testMissingInformation(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        prd.setConaryRepositoryHostname('')
        self.assertRaises(proddef.MissingInformationError,
                prd.getLabelForStage, "devel")

    def testStringCasting(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        ref = '<Product Definition: product-definition=product.example.com@exm:awesome-1.0>'
        self.assertEquals(str(prd), ref)

        # now try a blank ProdDef
        prd = proddef.ProductDefinition()
        ref = '<Product Definition: product-definition=None>'
        self.assertEquals(str(prd), ref)

    def testCopy(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        prd2 = prd.copy()
        for key, val in prd.__dict__.iteritems():
            val2 = prd2.__getattribute__(key)
            if val == None and val2 == None:
                # Undefined values
                continue
            if key in ['schemaDir', '_validate']:
                self.failUnlessEqual(val, val2)
                continue
            self.assertEquals(val, val2,
                    "Data element '%s' failed to copy. '%s' -> '%s'" % \
                            (key, val, val2))
            self.assertNotEquals(id(val), id(val2),
                    "Data element %s is the same after copy " \
                            "(it wasn't copied, it's the original)" % key)
    def testEq(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        prd2 = prd.copy()
        # test __eq__
        self.assertEquals(prd, prd2)
        # test __ne__
        self.assertEquals(prd != prd2, False)

        # now alter an element and re-test
        prd.buildDefinition[0].name = "\
                And now for something completely different"

        self.assertNotEquals(prd, prd2)
        self.assertEquals(prd == prd2, False)
        self.assertEquals(prd.buildDefinition[0] == prd2.buildDefinition[0],
                False)
        self.assertEquals(prd.buildDefinition[0] != prd2.buildDefinition[0],
                True)

    def testEq2(self):
        prd = proddef.ProductDefinition()
        image1 = prd.imageType('amiImage', {'swapSize' : '1024'})
        image2 = prd.imageType('amiImage', {'swapSize' : '1024'})
        self.assertEquals(image1, image2)

        self.failIf(image1 != image2, "not equal path failed")
        image3 = prd.imageType('installableIsoImage', {'swapSize' : '1024'})
        self.assertNotEquals(image1, image3)
        self.failIf(image1 == image3)

        image4 = prd.imageType('amiImage')
        self.assertNotEquals(image1, image4)
        self.failIf(image1 == image4)

        image5 = prd.imageType(None)
        self.assertNotEquals(image1, image5)

        self.assertNotEquals(image3, 1)

        class DummyImage(object):
            containerFormat = 'amiImage'
            swapSize = 1024

        self.assertNotEquals(image1, DummyImage())

    def testGetTroveName(self):
        prd = proddef.ProductDefinition()
        trvName = prd.getTroveName()
        self.failUnlessEqual(trvName, 'product-definition')
        # This is a class method, test that interface too
        self.failUnlessEqual(proddef.ProductDefinition.getTroveName(),
            'product-definition')

    def testTroveNameEncoding(self):
        prd = proddef.ProductDefinition()
        trvName = prd.getTroveName()
        self.failIf(isinstance(trvName, unicode),
            "Conary labels most not be returned as unicode")

    def testProductDefinitionLabelEncoding(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        self.failIf(isinstance(prd.getProductDefinitionLabel(), unicode),
            "Conary labels most not be returned as unicode")

    def testDefaultLabelEncoding(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        self.failIf(isinstance(prd.getDefaultLabel(), unicode),
            "Conary labels must not be returned as unicode")

    def testLabelForStageEncoding(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        self.failIf(isinstance(prd.getLabelForStage("devel"), unicode),
            "Conary labels must not be returned as unicode")

    def testPlatformNameSourceTrove1(self):
        sio = StringIO.StringIO()
        pld = proddef.PlatformDefinition()
        self.failUnlessEqual(pld.getPlatformName(), None)
        self.failUnlessEqual(pld.getPlatformVersionTrove(), None)

        pld.setBaseFlavor("Foo")
        pld.serialize(sio)
        self.assertXMLEquals(sio.getvalue(), """
<?xml version="1.0" encoding="UTF-8"?>
<platformDefinition xmlns="http://www.rpath.com/permanent/rpd-%(version)s.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-%(version)s.xsd rpd-%(version)s.xsd" version="%(version)s">
  <baseFlavor>Foo</baseFlavor>
</platformDefinition>""" % dict(version = proddef.ProductDefinition.version))

        pName = 'some name'
        pVersionTrove = 'some source trove'
        pld.setPlatformName(pName)
        pld.setPlatformVersionTrove(pVersionTrove)

        self.failUnlessEqual(pld.getPlatformName(), pName)
        self.failUnlessEqual(pld.getPlatformVersionTrove(), pVersionTrove)

        sio.truncate(0)
        pld.serialize(sio)
        self.assertXMLEquals(sio.getvalue(), """
<?xml version="1.0" encoding="UTF-8"?>
<platformDefinition xmlns="http://www.rpath.com/permanent/rpd-%(version)s.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-%(version)s.xsd rpd-%(version)s.xsd" version="%(version)s">
  <platformName>some name</platformName>
  <platformVersionTrove>some source trove</platformVersionTrove>
  <baseFlavor>Foo</baseFlavor>
</platformDefinition>""" % dict(version = proddef.ProductDefinition.version))

        sio.seek(0)
        pld = proddef.PlatformDefinition(fromStream = sio, validate = True,
            schemaDir = self.schemaDir)
        self.failUnlessEqual(pld.getPlatformName(), pName)
        self.failUnlessEqual(pld.getPlatformVersionTrove(), pVersionTrove)

    def testPlatformNameSourceTrove2(self):
        sio = StringIO.StringIO()
        prd = self.newProductDefinition(stages = [('devel', '-devel')])
        prd.addArchitecture(name = 'x86', displayName = '32 bit',
                flavor = 'is: x86')
        prd.addContainerTemplate(prd.imageType('installableIsoImage'))
        prd.addBuildDefinition(name='x86 Installable ISO Build',
            architectureRef = 'x86',
            containerTemplateRef = 'installableIsoImage',
            stages = ['devel'])

        self.failUnlessEqual(prd.getPlatformName(), None)
        self.failUnlessEqual(prd.getPlatformVersionTrove(), None)

        prd.setPlatformBaseFlavor("Foo")
        prd.serialize(sio)
        self.assertXMLEquals(sio.getvalue(), refPlatNameVersionTrove1)

        pName = 'some name'
        pVersionTrove = 'some source trove'
        prd.setPlatformName(pName)
        prd.setPlatformVersionTrove(pVersionTrove)

        self.failUnlessEqual(prd.getPlatformName(), pName)
        self.failUnlessEqual(prd.getPlatformVersionTrove(), pVersionTrove)

        sio.truncate(0)
        prd.serialize(sio)
        self.assertXMLEquals(sio.getvalue(), refPlatNameVersionTrove2)

        sio.seek(0)
        prd = proddef.ProductDefinition(fromStream = sio, validate = True,
            schemaDir = self.schemaDir)
        self.failUnlessEqual(prd.getPlatformName(), pName)
        self.failUnlessEqual(prd.getPlatformVersionTrove(), pVersionTrove)

        labelHost = "some.host"
        conaryNamespace = "namespace"

        prd.setProductShortname("awesome")
        prd.setProductVersion("1.0")
        prd.setConaryRepositoryHostname(labelHost)
        prd.setConaryNamespace(conaryNamespace)

        pld = prd.toPlatformDefinition()
        self.failUnlessEqual(pld.getPlatformName(), 'product name')
        self.failUnlessEqual(pld.getPlatformVersionTrove(), pVersionTrove)

    def testPlaformAutoLoadRecipes1(self):
        sio = StringIO.StringIO()
        pld = proddef.PlatformDefinition()
        self.failUnlessEqual(pld.getAutoLoadRecipes(), [])

        pld.setBaseFlavor("Foo")
        pld.serialize(sio)
        self.assertXMLEquals(sio.getvalue(), """
<?xml version="1.0" encoding="UTF-8"?>
<platformDefinition xmlns="http://www.rpath.com/permanent/rpd-%(version)s.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-%(version)s.xsd rpd-%(version)s.xsd" version="%(version)s">
  <baseFlavor>Foo</baseFlavor>
</platformDefinition>""" % dict(version = proddef.ProductDefinition.version))

        alRecipes = [('trove1', 'foo:bar-1'), ('trove2', 'foo:bar-2')]
        for troveName, label in alRecipes:
            pld.addAutoLoadRecipe(troveName, label)
        self.failUnlessEqual(
            [ (x.getTroveName(), x.getLabel())
                for x in pld.getAutoLoadRecipes() ],
            alRecipes)

        sio.truncate(0)
        pld.serialize(sio)
        self.assertXMLEquals(sio.getvalue(), """
<?xml version="1.0" encoding="UTF-8"?>
<platformDefinition xmlns="http://www.rpath.com/permanent/rpd-%(version)s.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-%(version)s.xsd rpd-%(version)s.xsd" version="%(version)s">
  <baseFlavor>Foo</baseFlavor>
  <autoLoadRecipes>
    <autoLoadRecipe troveName="trove1" label="foo:bar-1"/>
    <autoLoadRecipe troveName="trove2" label="foo:bar-2"/>
  </autoLoadRecipes>
</platformDefinition>""" % dict(version = proddef.ProductDefinition.version))

        sio.seek(0)
        pld = proddef.PlatformDefinition(fromStream = sio, validate = True,
            schemaDir = self.schemaDir)

        self.failUnlessEqual(
            [ (x.getTroveName(), x.getLabel())
                for x in pld.getAutoLoadRecipes() ],
            alRecipes)

    def testPlaformAutoLoadRecipes2(self):
        sio = StringIO.StringIO()
        prd = self.newProductDefinition(stages = [('devel', '-devel')])
        prd.addArchitecture('x86', '32 bit', 'is: x86')
        prd.addContainerTemplate(prd.imageType('installableIsoImage'))
        prd.addBuildDefinition(name='x86 Installable ISO Build',
            architectureRef = 'x86',
            containerTemplateRef = 'installableIsoImage',
            stages = ['devel'])

        self.failUnlessEqual(prd.getPlatformAutoLoadRecipes(), [])

        # At this point we have no platform; make sure clearing the auto load
        # recipes does the right thing
        prd.clearPlatformAutoLoadRecipes()
        self.failUnlessEqual(prd.getPlatformAutoLoadRecipes(), [])

        prd.setPlatformBaseFlavor("Foo")
        prd.serialize(sio)
        self.assertXMLEquals(sio.getvalue(), refPlatAutoLoadRecipes1)

        alRecipes = [('trove1', 'foo:bar-1'), ('trove2', 'foo:bar-2')]
        for troveName, label in alRecipes:
            prd.addPlatformAutoLoadRecipe(troveName, label)
        self.failUnlessEqual(
            [ (x.getTroveName(), x.getLabel())
                for x in prd.getPlatformAutoLoadRecipes() ],
            alRecipes)

        # Clear auto load recipes
        prd.clearPlatformAutoLoadRecipes()
        self.failUnlessEqual(prd.getPlatformAutoLoadRecipes(), [])

        # Set them again
        for troveName, label in alRecipes:
            prd.addPlatformAutoLoadRecipe(troveName, label)
        self.failUnlessEqual(
            [ (x.getTroveName(), x.getLabel())
                for x in prd.getPlatformAutoLoadRecipes() ],
            alRecipes)

        sio.truncate(0)
        prd.serialize(sio)

        self.assertXMLEquals(sio.getvalue(), refPlatAutoLoadRecipes2)

        sio.seek(0)
        prd = proddef.ProductDefinition(fromStream = sio, validate = True,
            schemaDir = self.schemaDir)

        self.failUnlessEqual(
            [ (x.getTroveName(), x.getLabel())
                for x in prd.getPlatformAutoLoadRecipes() ],
            alRecipes)

        labelHost = "some.host"
        conaryNamespace = "namespace"

        prd.setProductShortname("awesome")
        prd.setProductVersion("1.0")
        prd.setConaryRepositoryHostname(labelHost)
        prd.setConaryNamespace(conaryNamespace)

        pld = prd.toPlatformDefinition()
        self.failUnlessEqual(
            [ (x.getTroveName(), x.getLabel())
                for x in pld.getAutoLoadRecipes() ],
            alRecipes)

    def testAutoLoadRecipeRebase(self):
        prd = proddef.ProductDefinition()

        prd.setConaryRepositoryHostname('NOM')
        prd.setProductShortname('NOM')
        prd.setConaryNamespace('NOM')
        prd.setProductVersion('NOM')

        plt = prd.toPlatformDefinition()
        plt.addAutoLoadRecipe('nom', 'nom@nom:nom')

        prd._rebase('nom', plt)

        self.assertEquals(["%s=%s" % (x.getTroveName(), x.getLabel()) \
                for x in prd.getPlatformAutoLoadRecipes()], ['nom=nom@nom:nom'])

    def testGetPromoteMapsForStages(self):
        """
        Building a promote map between two stages
        """
        prd = proddef.ProductDefinition()
        prd.setProductShortname("enormous")
        prd.setProductVersion("1")
        prd.setConaryRepositoryHostname("enormous.repo")
        prd.setConaryNamespace("en")

        prd.addStage(name='devel', labelSuffix='-devel')
        prd.addStage(name='qa', labelSuffix='-qa', promoteMaps = [
            ('zen', 'extra@repo:zen-qa'),
            ('xeno', 'ultra@repo:xeno-qa'),])
        prd.addStage(name='release', labelSuffix='', promoteMaps=[
            ('zen', 'extra@repo:zen'),
            ('pico', '/micro@repo:pico'),])
        prd.addSecondaryLabel('xen', '-xen')

        self.assertEquals(prd.getPromoteMapsForStages('devel', 'qa',
                flattenLabels=['enormous.repo@en:enormous-1-devel',
                    'contrib.repo@co:ntrib']), {
            'enormous.repo@en:enormous-1-devel': # basic
                '/enormous.repo@en:enormous-1-qa',
            'enormous.repo@en:enormous-1-xen-devel': # secondary
                '/enormous.repo@en:enormous-1-xen-qa',
            'contrib.repo@co:ntrib': # flattened
                '/enormous.repo@en:enormous-1-qa',
            })

        self.assertEquals(prd.getPromoteMapsForStages('qa', 'release'), {
            'enormous.repo@en:enormous-1-qa': # basic
                '/enormous.repo@en:enormous-1',
            'enormous.repo@en:enormous-1-xen-qa': # secondary
                '/enormous.repo@en:enormous-1-xen',
            'extra@repo:zen-qa': 'extra@repo:zen', # promoteMap
            })

    def testArchitectures(self):
        prd = proddef.ProductDefinition()
        arches = prd.getArchitectures()
        self.assertEquals(arches, [])

        prd.addArchitecture('x86', 'x86', 'is: x86')
        arch = prd.getArchitecture('x86')
        self.assertEquals(arch.name, 'x86')
        self.assertEquals(arch.flavor, 'is: x86')
        arches = prd.getArchitectures()
        self.assertNotEquals(arches, [])
        prd.clearArchitectures()
        arches = prd.getArchitectures()
        arches = prd.getArchitectures()
        self.assertEquals(arches, [])

        self.assertRaises(proddef.ArchitectureNotFoundError,
                prd.getArchitecture, 'missing')
        default = 'test'
        res = prd.getArchitecture('missing', default = default)
        self.assertEquals(res, default)

    def testFlavorSets(self):
        prd = proddef.ProductDefinition()
        fSets = prd.getFlavorSets()
        self.assertEquals(fSets, [])

        prd.addFlavorSet('ami', 'ami', 'xen,domU')
        fs = prd.getFlavorSet('ami')
        self.assertEquals(fs.name, 'ami')
        self.assertEquals(fs.flavor, 'xen,domU')
        fSets = prd.getFlavorSets()
        self.assertNotEquals(fSets, [])
        prd.clearFlavorSets()
        fSets = prd.getFlavorSets()
        self.assertEquals(fSets, [])

        # now test the "missing" codepaths
        self.assertRaises(proddef.FlavorSetNotFoundError,
                prd.getFlavorSet, 'missing')
        default = 'test'
        res = prd.getFlavorSet('missing', default = default)
        self.assertEquals(res, default)

    def testFlavorSetsPlatform(self):
        prd = proddef.ProductDefinition()
        prd.addFlavorSet('ami', 'ami', 'xen,domU')

        prd.setConaryRepositoryHostname('NOM')
        prd.setProductShortname('NOM')
        prd.setConaryNamespace('NOM')
        prd.setProductVersion('NOM')

        platDef = prd.toPlatformDefinition()
        fs = platDef.getFlavorSet('ami')
        self.assertEquals(fs.name, 'ami')
        self.assertEquals(fs.flavor, 'xen,domU')
        ser = StringIO.StringIO()
        platDef.serialize(ser)
        platXml = ''.join(x.strip() for x in ser.getvalue().splitlines())

        self.failIf('<flavorSets><flavorSet flavor="xen,domU" displayName="ami" name="ami"/></flavorSets>' not in platXml)

        self.assertRaises(proddef.FlavorSetNotFoundError,
                prd.getPlatformFlavorSet, 'ami')
        prd._rebase('som-label', platDef)
        flvSet = prd.getPlatformFlavorSet('ami')
        self.assertEquals(flvSet.name, 'ami')
        self.assertEquals(flvSet.flavor, 'xen,domU')

    def testContainerTemplates(self):
        prd = proddef.ProductDefinition()
        tmpls = prd.getContainerTemplates()
        self.assertEquals(tmpls, [])

        # Test backwards compatible image definition
        from rpath_proddef import imageTypes
        img = imageTypes.Image(dict(containerFormat = 'ami'))
        prd.addContainerTemplate(img)
        tmpl = prd.getContainerTemplate('ami')
        self.assertEquals(tmpl.fields, {})
        self.assertEquals(tmpl.containerFormat, 'ami')

        tmpls = prd.getContainerTemplates()
        self.assertNotEquals(tmpls, [])
        prd.clearFlavorSets()
        tmpls = prd.getFlavorSets()
        self.assertEquals(tmpls, [])

        self.assertRaises(proddef.ContainerTemplateNotFoundError,
                prd.getContainerTemplate, 'missing')
        default = 'test'
        res = prd.getContainerTemplate('missing', default = default)
        self.assertEquals(res, default)

    def testContainerTemplatesPlatform(self):
        prd = proddef.ProductDefinition()
        img = prd.imageType('amiImage', dict(freespace = '1024'))
        prd.addContainerTemplate(img)

        prd.setConaryRepositoryHostname('NOM')
        prd.setProductShortname('NOM')
        prd.setConaryNamespace('NOM')
        prd.setProductVersion('NOM')

        platDef = prd.toPlatformDefinition()
        tmpl = platDef.getContainerTemplate('amiImage')
        self.assertEquals(tmpl.fields,
            dict(freespace = 1024))
        self.assertEquals(tmpl.containerFormat, 'amiImage')
        ser = StringIO.StringIO()
        platDef.serialize(ser)
        platXml = [x.strip() for x in ser.getvalue().splitlines()]

        # Grab just the containerTemplates node.
        ct = ''.join(platXml[-4:-1])
        self.assertXMLEquals(ct, '<containerTemplates><image freespace="1024" containerFormat="amiImage"/></containerTemplates>')

        self.assertRaises(proddef.ContainerTemplateNotFoundError,
                prd.getPlatformContainerTemplate, 'ami')
        prd._rebase('some-label', platDef)
        image = prd.getPlatformContainerTemplate('amiImage')
        self.assertEquals(image.containerFormat, 'amiImage')
        self.assertEquals(image.fields,
            dict(freespace= 1024))

        # test that addBuildDef sees the platform based container templates
        # this call should not raise ContainerTemplateNotFoundError
        prd = proddef.ProductDefinition()
        prd._rebase('some-label', platDef)
        prd.addBuildDefinition(containerTemplateRef = 'amiImage')

    def testBuildTemplates(self):
        prd = proddef.ProductDefinition()
        tmpls = prd.getBuildTemplates()
        self.assertEquals(tmpls, [])

        name = 'Ein kleines Huhn'
        displayName = "a small chicken"
        architectureRef = 'x86'
        containerTemplateRef = 'liveIso'
        flavorSetRef = 'flavRef'
        prd.addBuildTemplate(name, displayName, architectureRef,
                containerTemplateRef, flavorSetRef = flavorSetRef)
        tmpl = prd.getBuildTemplate(name)
        self.assertEquals(tmpl.name, name)
        self.assertEquals(tmpl.displayName, displayName)
        self.assertEquals(tmpl.architectureRef, architectureRef)
        self.assertEquals(tmpl.containerTemplateRef, containerTemplateRef)
        self.assertEquals(tmpl.flavorSetRef, flavorSetRef)

        tmpls = prd.getBuildTemplates()
        self.assertNotEquals(tmpls, [])
        prd.clearBuildTemplates()
        tmpls = prd.getBuildTemplates()
        self.assertEquals(tmpls, [])

        self.assertRaises(proddef.BuildTemplateNotFoundError,
                prd.getBuildTemplate, 'missing')
        default = 'test'
        res = prd.getBuildTemplate('missing', default = default)
        self.assertEquals(res, default)

    def testBuildTemplatesBuild(self):
        prd = proddef.ProductDefinition()
        tmpls = prd.getBuildTemplates()
        self.assertEquals(tmpls, [])

        name = 'buildRef'
        displayName = 'human readable'
        architectureRef = 'x86'
        containerTemplateRef = 'liveIso'
        flavorSetRef = 'flavorRef'
        prd.addContainerTemplate(prd.imageType('liveIso'))
        prd.addArchitecture(name = 'x86', displayName = 'x86',
                flavor = 'is: x86')
        prd.addFlavorSet(flavorSetRef, 'foo', 'foo')
        prd.addBuildTemplate(name,
                displayName = displayName,
                architectureRef = architectureRef,
                containerTemplateRef = containerTemplateRef,
                flavorSetRef = flavorSetRef)
        prd.addBuildDefinition(name = 'foo', buildTemplateRef = name)
        build = prd.getBuildDefinitions()[0]
        self.assertEquals(build.containerTemplateRef, None)
        self.assertEquals(build.flavorSetRef, None)
        self.assertEquals(build.architectureRef, None)
        self.assertEquals(build.getBuildBaseFlavor(), "foo is: x86")

    def testBuildTemplatesBuild2(self):
        prd = proddef.ProductDefinition()
        tmpls = prd.getBuildTemplates()
        self.assertEquals(tmpls, [])

        name = 'refName'
        displayName = 'human readable'
        architectureRef = 'x86'
        containerTemplateRef = 'liveIso'
        prd.addContainerTemplate(prd.imageType('liveIso'))
        prd.addContainerTemplate(prd.imageType('rawFsImage'))
        prd.addArchitecture(name = 'x86', displayName = '32 bit',
                flavor = 'is: x86')
        prd.addArchitecture(name = 'wrong', displayName = 'wrong',
                flavor = 'wrong')
        prd.addBuildTemplate(name, displayName = displayName,
                architectureRef = 'wrong',
                containerTemplateRef = 'rawFsImage')
        prd.addBuildDefinition(name = 'foo', buildTemplateRef = name,
                containerTemplateRef = containerTemplateRef,
                architectureRef = architectureRef)
        build = prd.getBuildDefinitions()[0]
        self.assertEquals(build.containerTemplateRef, containerTemplateRef)
        self.assertEquals(build.architectureRef, architectureRef)

    def testBuildTemplatesPlatform(self):
        prd = proddef.ProductDefinition()

        name = 'geisteskrankes Huhn'
        displayName = 'foo'
        architectureRef = 'x86'
        containerTemplateRef = 'liveIso'
        prd.addArchitecture(name = 'x86', displayName = '32 bit',
                flavor = 'is: x86')
        prd.addContainerTemplate(prd.imageType('liveIsoImage'))
        prd.addBuildTemplate(name, displayName, architectureRef,
                containerTemplateRef)

        prd.setConaryRepositoryHostname('NOM')
        prd.setProductShortname('NOM')
        prd.setConaryNamespace('NOM')
        prd.setProductVersion('NOM')

        platDef = prd.toPlatformDefinition()

        tmpl = platDef.getBuildTemplate(name)
        self.assertEquals(tmpl.name, name)
        self.assertEquals(tmpl.architectureRef, architectureRef)
        self.assertEquals(tmpl.containerTemplateRef, containerTemplateRef)
        ser = StringIO.StringIO()
        platDef.serialize(ser)
        platXml = ''.join(x.strip() for x in ser.getvalue().splitlines())

        self.failIf('<buildTemplates><buildTemplate containerTemplateRef="liveIso" architectureRef="x86" displayName="foo" name="geisteskrankes Huhn"/></buildTemplates>' not in platXml)

        self.assertRaises(proddef.BuildTemplateNotFoundError,
                prd.getPlatformBuildTemplate, name)
        prd._rebase('some-label', platDef)
        btmpl = prd.getPlatformBuildTemplate(name)
        self.assertEquals(btmpl.containerTemplateRef, containerTemplateRef)
        self.assertEqual(btmpl.architectureRef, architectureRef)
        self.assertEquals(btmpl.name, name)

        # test that addBuildDef sees the platform based build templates
        # this call should not raise ContainerTemplateNotFoundError
        prd = proddef.ProductDefinition()
        prd._rebase('some-label', platDef)
        prd.addBuildDefinition(buildTemplateRef = name)


    def testBuildTemplatesPlatform2(self):
        prd = self.newProductDefinition()

        name = 'build template'
        displayName = "human readable"
        architectureRef = 'x86'
        containerTemplateRef = 'liveIso'
        prd.addBuildTemplate(name, displayName, architectureRef,
                containerTemplateRef)

        #prd.setBaseFlavor('base,flavor is: x86')

        prd.setConaryRepositoryHostname('NOM')
        prd.setProductShortname('NOM')
        prd.setConaryNamespace('NOM')
        prd.setProductVersion('NOM')
        prd.addStage(name='release', labelSuffix='')

        platDef = prd.toPlatformDefinition()
        self.assertEquals([x.name for x in platDef.buildTemplates],
                ['build template'])

        tmpl = platDef.getBuildTemplate(name)

        nprd = self.newProductDefinition()
        nprd._rebase('some-label', platDef)
        sio = StringIO.StringIO()
        nprd.serialize(sio)

        prd = proddef.ProductDefinition(fromStream = sio.getvalue())

        self.assertEquals([x.name for x in prd.platform.buildTemplates],
                ['build template'])

    def testCommonDefinitionElementsNotRequired(self):
        prd = proddef.ProductDefinition()

        architectureRef = 'x86'
        containerTemplateRef = 'liveIso'
        prd.addArchitecture(name = 'x86', displayName = '32 bit',
                flavor = 'is: x86')
        prd.addContainerTemplate(prd.imageType('liveIsoImage'))
        prd.addBuildTemplate('build-t', 'build-td', architectureRef,
                containerTemplateRef)

        prd.setConaryRepositoryHostname('conary.example.com')
        prd.setProductShortname('prod')
        prd.setConaryNamespace('test')
        prd.setProductVersion('1')

        platDef = prd.toPlatformDefinition()

        prd = proddef.ProductDefinition()
        prd.setProductName("foo")
        prd.setProductDescription('description')
        prd.setProductShortname('prod')
        prd.setConaryRepositoryHostname('conary.example.com')
        prd.setConaryNamespace('test')
        prd.setProductVersion('1')
        prd.setProductVersionDescription('version description')
        prd.setImageGroup('group-dist')
        prd.addStage(name='release', labelSuffix='')
        prd._rebase('some-label', platDef)
        # Make sure the schema validates, even though we don't have any of the
        # commonDefinitionElements used
        sio = StringIO.StringIO()
        prd.serialize(sio)

    def testFixupVhdDiskType(self):
        # rbuilder was generating images with vhdDiskType='', which is not an
        # acceptable value.
        # Make sure in this case we drop vhdDiskType
        xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<productDefinition xmlns="http://www.rpath.com/permanent/rpd-2.0.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-2.0.xsd rpd-2.0.xsd" version="2.0">
  <productName>blah-12</productName>
  <productShortname>blah-12</productShortname>
  <productDescription></productDescription>
  <productVersion>1</productVersion>
  <productVersionDescription></productVersionDescription>
  <conaryRepositoryHostname>blah-12.eng.rpath.com</conaryRepositoryHostname>
  <conaryNamespace>rpath</conaryNamespace>
  <imageGroup>group-blah-12-appliance</imageGroup>
  <baseFlavor></baseFlavor>
  <stages>
    <stage labelSuffix="" name="Release"/>
  </stages>
  <buildDefinition>
    <build containerTemplateRef="amiImage" architectureRef="x86" name="blah-12-EC2 AMI Small (x86)" flavorSetRef="ami">
      <image autoResolve="false" freespace="1024" vhdDiskType="" swapSize="1024" baseFileName="" buildOVF10="true" installLabelPath="" amiHugeDiskMountpoint="false" vmMemory="0" diskAdapter="scsi" />
      <stage ref="Release"/>
    </build>
    <build containerTemplateRef="vmwareImage" architectureRef="x86" name="blah-vmware (32-bit)" flavorSetRef="vmware">
      <image vhdDiskType="scsi" buildOVF10="false"/>
      <stage ref="Release"/>
    </build>
    <build containerTemplateRef="vhdImage" architectureRef="x86" name="blah-vhd (32-bit)" flavorSetRef="vhd">
      <image vhdDiskType="ide"/>
      <stage ref="Release"/>
    </build>
  </buildDefinition>
  <platform sourceTrove="platform-definition=/conary.rpath.com@rpl:2/2.0.beta2-2">
    <platformName>rPath Linux 2</platformName>
    <platformVersionTrove>group-os</platformVersionTrove>
    <baseFlavor>~X</baseFlavor>
    <searchPaths>
      <searchPath isResolveTrove="true" troveName="group-os" version="2.0.1-0.1-7" isGroupSearchPathTrove="true" label="conary.rpath.com@rpl:2"/>
    </searchPaths>
    <factorySources>
      <factorySource troveName="group-factories" version="2.0.1-0.1-7" label="conary.rpath.com@rpl:2"/>
    </factorySources>
    <architectures>
      <architecture flavor="is:x86(~i486, ~i586, ~i686, ~cmov, ~mmx, ~sse, ~sse2)" displayName="x86 (32-bit)" name="x86"/>
    </architectures>
    <flavorSets>
      <flavorSet flavor="~xen, ~domU, ~!dom0, ~!vmware" displayName="AMI" name="ami"/>
      <flavorSet flavor="~vmware" displayName="VMware" name="vmware"/>
      <flavorSet flavor="~!vmware" displayName="VHD" name="vhd"/>
    </flavorSets>
    <containerTemplates>
      <image autoResolve="false" freespace="1024" swapSize="1024" baseFileName="" installLabelPath="" amiHugeDiskMountpoint="false" containerFormat="amiImage"/>
    </containerTemplates>
    <buildTemplates>
      <buildTemplate containerTemplateRef="amiImage" architectureRef="x86" name="EC2 AMI Small" flavorSetRef="ami"/>
      <buildTemplate containerTemplateRef="vmwareImage" architectureRef="x86" name="VMware 32-bit" flavorSetRef="vmware"/>
      <buildTemplate containerTemplateRef="vhdImage" architectureRef="x86" name="VHD 32-bit" flavorSetRef="vhd"/>
    </buildTemplates>
  </platform>
</productDefinition>
"""
        pd = proddef.ProductDefinition(fromStream = xml)
        self.failUnlessEqual(pd.preMigrateVersion, '2.0')
        sio = StringIO.StringIO()
        pd.serialize(sio)
        # This means we validated the schema - but just to make sure

        img0 = pd.buildDefinition[0].image
        img1 = pd.buildDefinition[1].image
        img2 = pd.buildDefinition[2].image

        self.failUnlessEqual(img0.vhdDiskType, None)
        self.failUnlessEqual(img1.vhdDiskType, None)
        self.failUnlessEqual(img2.vhdDiskType, None)

        self.failUnlessEqual(img0.diskAdapter, 'lsilogic')
        self.failUnlessEqual(img1.diskAdapter, 'lsilogic')
        self.failUnlessEqual(img2.diskAdapter, 'ide')

        # Was buildOVF10 saved?
        self.failUnlessEqual(img0.buildOVF10, True)
        self.failUnlessEqual(img1.buildOVF10, False)
        self.failUnlessEqual(img2.buildOVF10, None)

        # Serialize as 2.0
        sio = StringIO.StringIO()
        pd.serialize(sio, version = '2.0')
        # We shouldn't produce the broken values anymore
        xml = xml.replace(' vhdDiskType=""', '')
        xml = xml.replace(' vhdDiskType="scsi"', ' diskAdapter="lsilogic"')
        xml = xml.replace(' diskAdapter="scsi"', ' diskAdapter="lsilogic"')
        xml = xml.replace(' vhdDiskType="ide"', ' diskAdapter="ide"')
        xml = xml.replace(' diskAdapter="ide"', ' diskAdapter="ide"')
        self.assertXMLEquals(sio.getvalue(), xml)

    def testAddBuildDefinitionFiltersEmptyVhdDiskType(self):
        prd = proddef.ProductDefinition()
        image = prd.imageType(None, {
            'freespace': '2048', 'vhdDiskType' : '', })
        self.failUnlessEqual(image.vhdDiskType, None)
        self.failUnlessEqual(image.freespace, 2048)

    def testEmptyListElements(self):
        xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<productDefinition xmlns="http://www.rpath.com/permanent/rpd-%(version)s.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-%(version)s.xsd rpd-%(version)s.xsd" version="%(version)s">
  <productName>blah-12</productName>
  <productShortname>blah-12</productShortname>
  <productDescription></productDescription>
  <productVersion>1</productVersion>
  <productVersionDescription></productVersionDescription>
  <conaryRepositoryHostname>blah-12.eng.rpath.com</conaryRepositoryHostname>
  <conaryNamespace>rpath</conaryNamespace>
  <imageGroup>group-blah-12-appliance</imageGroup>
  <baseFlavor></baseFlavor>
  <stages>
    <stage labelSuffix="" name="Release"/>
  </stages>
  @EXTRAS@
</productDefinition>
""" % dict(version = proddef.ProductDefinition.version)

        emptyElements = """
  <searchPaths>
  </searchPaths>
  <factorySources>
  </factorySources>
  <autoLoadRecipes />
  <secondaryLabels />
  <architectures />
  <flavorSets />
  <containerTemplates />
  <buildTemplates />
  <buildDefinition>
  </buildDefinition>
"""
        pd = proddef.ProductDefinition(fromStream = xml.replace("@EXTRAS@",
            emptyElements))
        sio = StringIO.StringIO()
        pd.serialize(sio)

        extras = """
  <architectures />
  <flavorSets />
  <buildTemplates />
"""
        self.assertXMLEquals(sio.getvalue(), xml.replace("@EXTRAS@", extras))

    def testImageless(self):
        # RBL-5511
        pd = self.newProductDefinition()
        pd.addContainerTemplate(pd.imageType('imageless'))
        sio = StringIO.StringIO()
        pd.serialize(sio)

        sio.seek(0)
        pd2 = proddef.ProductDefinition(fromStream = sio)
        self.failUnlessEqual(pd2.containerTemplates[-1].containerFormat,
            'imageless')

    @testhelp.context('RBL-3886')
    def testLegacyXml(self):
        pd = proddef.ProductDefinition(fromStream = legacyXML)
        buildFlavors = [x.getBuildBaseFlavor() for x in
                pd.getBuildDefinitions()]
        # There is no build.flavor anymore
        raise testhelp.SkipTestException("Refactoring: build objects have no flavor member")
        #buildFlavors = [x.flavor for x in pd.getBuildDefinitions()]
        self.assertEquals(buildFlavors, [None, None, None, None, None, None])

    def testLegacyXml2(self):
        pd = proddef.ProductDefinition(fromStream = legacyXML)
        sio = StringIO.StringIO()

        npd = proddef.ProductDefinition()
        npd.addArchitecture(name = 'x86',
                displayName = "32 bit",
                flavor = 'is:x86(i486, i586, cmov, mmx, sse)')
        npd.addArchitecture(name = 'x86_64',
                displayName = "64 bit",
                flavor = 'is:x86_64 x86(i486, i586, cmov, mmx, sse)')
        npd.addFlavorSet(name = 'vmware', displayName = 'vmware',
                flavor = 'vmware')
        npd.addFlavorSet(name = 'xen', displayName = 'xen',
                flavor = 'xen,domU')
        npd.addFlavorSet(name = 'unused', displayName = 'unused',
                flavor = '~!xen,~!dom0,~!domU')

        npd.setConaryRepositoryHostname('NOM')
        npd.setProductShortname('NOM')
        npd.setConaryNamespace('NOM')
        npd.setProductVersion('NOM')

        plt = npd.toPlatformDefinition()
        pd._rebase('some-label', plt)
        pd.serialize(sio)
        self.assertNotEquals(sio.getvalue(), legacyXML)

    def testLegacyBuildDef(self):
        pd = proddef.ProductDefinition(fromStream = legacyXML2)
        # these results are a bit atypical, but no real build definition in the
        # wild has a architecture-less build with a custom flavor of "random2"
        # nor actual platform overrides
        self.assertEquals([ \
                (x.containerTemplateRef, x.architectureRef, x.flavorSetRef) \
                        for x in pd.buildDefinition],
                [('installableIsoImage', None, None),
                 ('rawHdImage', None, None),
                 ('rawHdImage', None, None),
                 ('rawHdImage', None, None),
                 ('rawHdImage', 'missing', None)])

    def testLegacyBuildDef2(self):
        # repeat the legacy build test but with a proddef that needs a default
        # platform defined
        pd = proddef.ProductDefinition(fromStream = legacyXML3)
        self.assertEquals([ \
                (x.containerTemplateRef, x.architectureRef, x.flavorSetRef) \
                        for x in pd.buildDefinition],
                [('installableIsoImage', 'x86', 'generic'),
                 ('rawHdImage', 'x86', 'generic'),
                 ('rawHdImage', None, 'generic'),
                 ('rawHdImage', None, 'generic'),
                 ('rawHdImage', 'missing', None)])

    def testBadBuildBaseFlavor(self):
        prd = proddef.ProductDefinition()
        prd.addFlavorSet('foo', 'foo', 'is: x86')

        realParseFlavor = deps.parseFlavor
        self.count = 0
        message = "simulated failure for testing"
        def mockedParseFlavor(*args, **kwargs):
            self.count += 1
            if self.count == 3:
                raise RuntimeError(message)
            return realParseFlavor(*args, **kwargs)
        self.mock(deps, 'parseFlavor', mockedParseFlavor)

        err = self.failUnlessRaises(proddef.ProductDefinitionError,
            prd.addBuildDefinition, flavorSetRef = 'foo')
        self.assertEquals(str(err), message)

    def testBuildFlavors(self):
        prd = self.newProductDefinition()
        prd.addFlavorSet('foo', 'foo', 'is: x86')
        prd.addBuildDefinition(flavorSetRef = 'foo', flavor = 'bar')

        buildDef = prd.getBuildDefinitions()[0]
        self.assertEquals(buildDef.getBuildBaseFlavor(), 'bar is: x86')

        sio = StringIO.StringIO()
        prd.serialize(sio)
        prd2 = proddef.ProductDefinition(fromStream = sio.getvalue())

        buildDef2 = prd2.getBuildDefinitions()[0]
        self.assertEquals(buildDef2.getBuildBaseFlavor(), 'bar is: x86')

    def testBuildFlavorOrder(self):
        # this test concentrates on proving that proddef type options override
        # platform def type options.
        # set up a platform def with platformy options
        prd = proddef.ProductDefinition()
        prd.addArchitecture(name = 'arch', displayName = 'arch',
                flavor = 'is: platArch')
        prd.addFlavorSet(name = "flavSet", displayName = 'flavSet',
                flavor = 'platFlav')
        prd.setBaseFlavor('platBaseFlav')

        prd.setConaryRepositoryHostname('NOM')
        prd.setProductShortname('NOM')
        prd.setConaryNamespace('NOM')
        prd.setProductVersion('NOM')

        plt = prd.toPlatformDefinition()

        # now set up a proddef to override those flavors
        prd = proddef.ProductDefinition()
        prd.addArchitecture(name = 'arch', displayName = 'arch',
                flavor = 'is: prodArch')
        prd.addFlavorSet(name = "flavSet", displayName = 'flavSeflavSett',
                flavor = '!platFlav')
        prd.setBaseFlavor('!platBaseFlav')

        prd._rebase('label', plt)

        self.assertEquals(prd.getBaseFlavor(), '!platBaseFlav')

        prd.addBuildDefinition(flavorSetRef = 'flavSet',
                architectureRef = 'arch', flavor = 'unrelated')

        buildDef = prd.getBuildDefinitions()[0]
        self.assertEquals(buildDef.getBuildBaseFlavor(),
                '!platBaseFlav,!platFlav,unrelated is: prodArch')

    def testBuildFlavorOrder2(self):
        # this test concentrates on the order of flavorSet, architecture
        # and flavor
        # set up a platform def with platformy options
        prd = proddef.ProductDefinition()
        prd.addArchitecture(name = 'a1', displayName = 'a1', flavor = 'a,!c')
        prd.addFlavorSet(name = "f1", displayName = 'f1', flavor = '!a,!b')
        prd.setBaseFlavor('b,c,d')

        prd.setConaryRepositoryHostname('NOM')
        prd.setProductShortname('NOM')
        prd.setConaryNamespace('NOM')
        prd.setProductVersion('NOM')

        plt = prd.toPlatformDefinition()

        # now set up a proddef to override those flavors
        prd = proddef.ProductDefinition()
        prd.addArchitecture(name = 'a2', displayName = 'a2', flavor = 'e,!g')
        prd.addFlavorSet(name = "f2", displayName = 'f2', flavor = '!e,!f')
        prd.setBaseFlavor('f,g,h')

        prd._rebase('label', plt)

        self.assertEquals(prd.getBaseFlavor(), 'b,c,d,f,g,h')

        prd.addBuildDefinition(flavorSetRef = 'f1',
                architectureRef = 'a1', flavor = '!d')

        buildDef = prd.getBuildDefinitions()[0]
        # architecture beats flavorset: a
        # flavorset beats baseFlavor: !b
        # architecture bears baseFlavor: !c
        # build's flavor beats baseFlavor: !d
        # f,g,h are uncontested from proddef
        self.assertEquals(buildDef.getBuildBaseFlavor(),
                'a,!b,!c,!d,f,g,h')

        prd.addBuildDefinition(name = 'build2', flavorSetRef = 'f2',
                architectureRef = 'a2', flavor = '!h')

        buildDef = [x for x in prd.getBuildDefinitions() \
                if x.name == 'build2'][0]
        # architecture beats flavorset: e
        # flavorset beats baseFlavor: !f
        # architecture bears baseFlavor: !g
        # build's flavor beats baseFlavor: !h
        # b,c,d are uncontested from platdef
        self.assertEquals(buildDef.getBuildBaseFlavor(),
                'b,c,d,e,!f,!g,!h')

    def testBuildFlavorPlatformDeref(self):
        prd = proddef.ProductDefinition()
        tmpls = prd.getBuildTemplates()
        self.assertEquals(tmpls, [])

        name = 'buildRef'
        displayName = 'human readable'
        architectureRef = 'x86'
        containerTemplateRef = 'liveIso'
        flavorSetRef = 'flavorRef'
        prd.addContainerTemplate(prd.imageType('liveIso'))
        prd.addArchitecture(name = 'x86', displayName = 'x86',
                flavor = 'is: x86')
        prd.addFlavorSet(flavorSetRef, 'foo', 'foo')
        prd.addBuildTemplate(name,
                displayName = displayName,
                architectureRef = architectureRef,
                containerTemplateRef = containerTemplateRef,
                flavorSetRef = flavorSetRef)

        prd.setConaryRepositoryHostname('NOM')
        prd.setProductShortname('NOM')
        prd.setConaryNamespace('NOM')
        prd.setProductVersion('NOM')

        plt = prd.toPlatformDefinition()
        prd = proddef.ProductDefinition()
        prd._rebase('NOM@NOM:NOM', plt)

        prd.addBuildDefinition(name = 'foo', buildTemplateRef = name)
        build = prd.getBuildDefinitions()[0]
        self.assertEquals(build.containerTemplateRef, None)
        self.assertEquals(build.flavorSetRef, None)
        self.assertEquals(build.architectureRef, None)
        self.assertEquals(build.getBuildBaseFlavor(), "foo is: x86")

    def testDuplicateFlavorSet(self):
        prd = self.newProductDefinition()
        prd.addFlavorSet(name = 'foo', displayName = 'foo', flavor = 'busted')
        prd.addFlavorSet(name = 'foo', displayName = 'foo', flavor = 'correct')

        self.assertEquals([(x.name, x.flavor) for x in prd.getFlavorSets()],
                [('foo', 'correct')])

        prd = self.newProductDefinition()
        prd.clearFlavorSets()
        prd.addFlavorSet(name = 'foo', displayName = 'foo', flavor = 'busted')
        prd.addFlavorSet(name = 'foo', displayName = 'foo', flavor = 'correct')

        sio = StringIO.StringIO()
        prd.serialize(sio)

        prd = proddef.ProductDefinition(fromStream = sio.getvalue())
        self.assertEquals([(x.name, x.flavor) for x in prd.getFlavorSets()],
                [('foo', 'correct')])

    def testGetBuildImage(self):
        prd = proddef.ProductDefinition()
        prd.addContainerTemplate(prd.imageType('installableIsoImage',
            {'swapSize' : '1024'}))

        prd.setConaryRepositoryHostname('NOM')
        prd.setProductShortname('NOM')
        prd.setConaryNamespace('NOM')
        prd.setProductVersion('NOM')

        plt = prd.toPlatformDefinition()
        prd = proddef.ProductDefinition()
        prd._rebase('some-label', plt)

        prd.addBuildDefinition('foo',
                image = prd.imageType(None, {'freespace': '2048'}),
                containerTemplateRef = 'installableIsoImage')

        build = prd.getBuildDefinitions()[0]

        image = build.getBuildImage()
        self.assertEquals(image.containerFormat, 'installableIsoImage')
        self.assertEquals(image.fields, {'freespace': 2048, 'swapSize': 1024})

    def testSearchPathAttrs(self):
        prd = self.newProductDefinition()
        prd.addSearchPath(troveName = 'foo', label = 'test.rpath.local@foo:1')
        prd.addSearchPath(troveName = 'bar', label = 'test.rpath.local@foo:1',
                isResolveTrove = False)
        prd.addSearchPath(troveName = 'baz', label = 'test.rpath.local@foo:1',
                isGroupSearchPathTrove = False)

        for i in range(3):
            res = prd.getSearchPaths()
            res = sorted(["%s=%s" % (x.troveName, x.label) for x in res])
            self.assertEquals(res, ['bar=test.rpath.local@foo:1',
                                    'baz=test.rpath.local@foo:1',
                                    'foo=test.rpath.local@foo:1'])

            res = prd.getResolveTroves()
            res = sorted(["%s=%s" % (x.troveName, x.label) for x in res])
            self.assertEquals(res, ['baz=test.rpath.local@foo:1',
                                    'foo=test.rpath.local@foo:1'])

            res = prd.getGroupSearchPaths()
            res = sorted(["%s=%s" % (x.troveName, x.label) for x in res])
            self.assertEquals(res, ['bar=test.rpath.local@foo:1',
                                    'foo=test.rpath.local@foo:1'])
            sio = StringIO.StringIO()
            prd.serialize(sio)
            prd = proddef.ProductDefinition(fromStream = sio.getvalue())

    def testSearchPathAttrs2(self):
        # this time, cast the proddef to a platform and try again
        prd = self.newProductDefinition()
        prd.addSearchPath(troveName = 'foo', label = 'test.rpath.local@foo:1')
        prd.addSearchPath(troveName = 'bar', label = 'test.rpath.local@foo:1',
                isResolveTrove=False)
        prd.addSearchPath(troveName = 'baz', label = 'test.rpath.local@foo:1',
                isGroupSearchPathTrove=False)
        prd.setConaryRepositoryHostname('NOM')
        prd.setProductShortname('NOM')
        prd.setConaryNamespace('NOM')
        prd.setProductVersion('NOM')

        # move the searchPath items to the platform level
        plt = prd.toPlatformDefinition()
        prd = self.newProductDefinition()
        prd._rebase('NOM', plt)

        for i in range(3):
            res = prd.getSearchPaths()
            res = sorted(["%s=%s" % (x.troveName, x.label) for x in res])
            self.assertEquals(res, [
                                    'bar=test.rpath.local@foo:1',
                                    'baz=test.rpath.local@foo:1',
                                    'foo=test.rpath.local@foo:1',
                                    'group-os=NOM@NOM:NOM-NOM',
                                    ])
            res = prd.getResolveTroves()
            res = sorted(["%s=%s" % (x.troveName, x.label) for x in res])
            self.assertEquals(res, [
                                    'baz=test.rpath.local@foo:1',
                                    'foo=test.rpath.local@foo:1',
                                    'group-os=NOM@NOM:NOM-NOM',
                                    ])
            res = prd.getGroupSearchPaths()
            res = sorted(["%s=%s" % (x.troveName, x.label) for x in res])
            self.assertEquals(res, [
                                    'bar=test.rpath.local@foo:1',
                                    'foo=test.rpath.local@foo:1',
                                    'group-os=NOM@NOM:NOM-NOM',
                                    ])
            sio = StringIO.StringIO()
            prd.serialize(sio)
            prd = proddef.ProductDefinition(fromStream = sio.getvalue())

    def testSearchPathAttrs3(self):
        # this time, cast the proddef to a platform and try again
        prd = proddef.ProductDefinition()
        prd.addSearchPath(troveName = 'foo', label = 'test.rpath.local@foo:1')
        prd.addSearchPath(troveName = 'bar', label = 'test.rpath.local@foo:1',
                isResolveTrove=False)
        prd.addSearchPath(troveName = 'baz', label = 'test.rpath.local@foo:1',
                isGroupSearchPathTrove=False)
        prd.setConaryRepositoryHostname('NOM')
        prd.setProductShortname('NOM')
        prd.setConaryNamespace('NOM')
        prd.setProductVersion('NOM')

        # move the searchPath items to the platform level
        plt = prd.toPlatformDefinition()
        for i in range(3):
            res = plt.getSearchPaths()
            res = sorted(["%s=%s" % (x.troveName, x.label) for x in res])
            self.assertEquals(res, ['None=NOM@NOM:NOM-NOM',
                                    'bar=test.rpath.local@foo:1',
                                    'baz=test.rpath.local@foo:1',
                                    'foo=test.rpath.local@foo:1'])

            res = plt.getResolveTroves()
            res = sorted(["%s=%s" % (x.troveName, x.label) for x in res])
            self.assertEquals(res, ['None=NOM@NOM:NOM-NOM',
                                    'baz=test.rpath.local@foo:1',
                                    'foo=test.rpath.local@foo:1'])

            res = plt.getGroupSearchPaths()
            res = sorted(["%s=%s" % (x.troveName, x.label) for x in res])
            self.assertEquals(res, ['None=NOM@NOM:NOM-NOM',
                                    'bar=test.rpath.local@foo:1',
                                    'foo=test.rpath.local@foo:1'])
            sio = StringIO.StringIO()
            plt.serialize(sio)
            plt = proddef.PlatformDefinition(fromStream = sio.getvalue())

    def testSearchPathTroveTup(self):
        prd = proddef.ProductDefinition()

        prd.addSearchPath('foo', 'foo.rpath.local@rpl:1')
        res = [x.getTroveTup(template = False) for x in prd.getSearchPaths()]
        self.assertEquals(res, [('foo', 'foo.rpath.local@rpl:1', None)])

        prd.addSearchPath('bar', 'foo.rpath.local@rpl:1', '1.1-1-1')
        res = [x.getTroveTup(template = False) for x in prd.getSearchPaths()]
        self.assertEquals(res, [('foo', 'foo.rpath.local@rpl:1', None),
                                ('bar', 'foo.rpath.local@rpl:1/1.1-1-1', None)])

        res = [x.getTroveTup(template = True) for x in prd.getSearchPaths()]
        self.assertEquals(res, [('foo', 'foo.rpath.local@rpl:1', None),
                                ('bar', 'foo.rpath.local@rpl:1', None)])

    def testRebasePlatform(self):
        # this is a meta test. Its purpose is to ensure all items in the
        # platform get inserted into proddefs that base off them
        # if the assertion below fails, be sure to set the attribute you added
        # before adding it to the list of known attrs.
        plt = proddef.PlatformDefinition()
        attrs = set(plt.__dict__.keys())
        attrs = attrs.difference(
                set([
                    '_rootObj',
                    '_sourceTrove',
                    '_useLatest',
                    '_validate',
                    '_preMigrateVersion',
                    ]))
        self.failIf(attrs, "the following attributes are not being tested, "
                "please set them in this test before adding them to the "
                "whitelist: '%s'" % ("', '".join(attrs)))
        plt.addArchitecture('arch', 'arch', 'is: x86')
        plt.addAutoLoadRecipe(troveName = 'foo', label = 'nom@nom:nom')
        plt.setBaseFlavor('base,flavor')
        plt.addContainerTemplate(plt.imageType('installableIsoImage'))
        plt.addFlavorSet(name = 'flvSet', displayName = 'flvSet',
                flavor = 'flavorSet')
        plt.addBuildTemplate(name = 'buildTemp', displayName = 'buildTemp',
                architectureRef = 'arch',
                containerTemplateRef = 'installableIsoImage',
                flavorSetRef = 'flvSet')
        plt.addFactorySource(troveName = 'troveName', label = 'label',
                version = 'version')
        plt.setPlatformName('platName')
        plt.setPlatformVersionTrove('troveSpec')
        plt.addSearchPath(troveName = 'trvName', label = 'nom@nom:nom',
                version = '3.2')
        plt.sourceTrove = 'srcTrove'
        plt.useLatests = False

        sio = StringIO.StringIO()
        plt.serialize(sio)
        # Drop the first two lines (XML declaration and top-level node
        # versioning which would fail the equality test, since we have no
        # version attribute in <platform> nodes)
        sio.seek(0)
        originalXml = ''.join([ "<platformDefinition>\n" ] + sio.readlines()[2:])

        prd = proddef.ProductDefinition()
        prd._rebase('nom', plt)

        newPlt = prd.platform
        # newPlt is a Platform, not a PlatformDefinition, so we need to change
        # the top-level node
        newPlt.RootNode = 'platformDefinition'
        # And we need to get rid of the source trove
        newPlt.sourceTrove = None
        newPlt._rootObj.get_version = lambda: prd.version

        sio = StringIO.StringIO()
        newPlt.serialize(sio)
        sio.seek(0)
        newXml = ''.join([ "<platformDefinition>\n" ] + sio.readlines()[2:])
        # keep in mind that since we're serializing the platdef objects to test
        # for equality, this test is sensitive to bugs in the serialization
        # codepaths. presumably such issues would be caught elsewhere
        self.assertXMLEquals(originalXml, newXml)

    def testPlatformNamespace(self):
        pld = proddef.PlatformDefinition(fromStream = refPlatSerialize1)
        self.assertEquals(pld.defaultNamespace,
                'http://www.rpath.com/permanent/rpd-%s.xsd' %
                    proddef.ProductDefinition.version)

        pld = proddef.PlatformDefinition(
                fromStream = refPlatSerialize1.replace(
                    proddef.ProductDefinition.version, '1.3'))
        # Silent conversion at load, so we still expect latest
        self.assertEquals(pld.defaultNamespace,
                'http://www.rpath.com/permanent/rpd-%s.xsd' %
                    proddef.ProductDefinition.version)

    def testPlatformContentProvider(self):
        # RBL-5300
        prd = self.newProductDefinition()
        pld = prd.toPlatformDefinition()

        dataSources = [
            pld.newDataSource(
                name="rhel-i386-server-5",
                description="Red Hat Enterprise Linux (v. 5 for 32-bit x86)"),
            pld.newDataSource(
                name="rhel-x86_64-server-5",
                description="Red Hat Enterprise Linux (v. 5 for 64-bit x86_64)"),
        ]
        contentSourceTypes = [
            pld.newContentSourceType(
                name = "RHN", description="Red Hat Network Hosted",
                isSingleton = True),
            pld.newContentSourceType(
                name = "satellite", description="Red Hat Network Satellite"),
            pld.newContentSourceType(
                name = "proxy", description="Red Hat Network Proxy"),
        ]

        pld.setContentProvider(description = "Red Hat Network", name = "rhn",
            contentSourceTypes = contentSourceTypes, dataSources = dataSources)

        sio = StringIO.StringIO()
        pld.serialize(sio)
        self.assertXMLEquals(sio.getvalue(), """\
<platformDefinition xmlns="http://www.rpath.com/permanent/rpd-%(version)s.xsd"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.rpath.com/permanent/rpd-%(version)s.xsd rpd-%(version)s.xsd"
version="%(version)s">
    <platformName>product name</platformName>
    <baseFlavor/>
    <contentProvider name="rhn" description="Red Hat Network">
      <contentSourceType name="RHN" description="Red Hat Network Hosted" isSingleton="true" />
      <contentSourceType name="satellite" description="Red Hat Network Satellite" />
      <contentSourceType name="proxy" description="Red Hat Network Proxy" />
      <dataSource description="Red Hat Enterprise Linux (v. 5 for 32-bit x86)" name="rhel-i386-server-5" />
      <dataSource description="Red Hat Enterprise Linux (v. 5 for 64-bit x86_64)" name="rhel-x86_64-server-5" />
    </contentProvider>
    <searchPaths>
        <searchPath isPlatformTrove="true" isGroupSearchPathTrove="true" troveName="group-os"
             isResolveTrove="true"
             label="conary.example.com@lnx:product short name-0.1"/>
    </searchPaths>
</platformDefinition>
""" % dict(version = proddef.ProductDefinition.version))
        sio.seek(0)
        pld = proddef.PlatformDefinition(fromStream = sio)
        cprov = pld.getContentProvider()
        self.failUnlessEqual(cprov.name, "rhn")
        self.failUnlessEqual(cprov.description, "Red Hat Network")
        expected = [
            ("rhel-i386-server-5",
                "Red Hat Enterprise Linux (v. 5 for 32-bit x86)"),
            ("rhel-x86_64-server-5",
                "Red Hat Enterprise Linux (v. 5 for 64-bit x86_64)"),
        ]
        self.failUnlessEqual(
            [ (x.name, x.description)
                for x in cprov.dataSources ],
            expected)
        expected = [
            ('RHN', 'Red Hat Network Hosted', True),
            ('satellite', 'Red Hat Network Satellite', None),
            ('proxy', 'Red Hat Network Proxy', None),
        ]
        self.failUnlessEqual(
            [ (x.name, x.description, x.isSingleton)
                for x in cprov.contentSourceTypes ],
            expected)

        # Create product
        prd = self.newProductDefinition()
        # Rebase it, make sure we copy the content provider too
        prd._rebase(label = None, nplat = pld)
        cprov = prd.platform.getContentProvider()
        self.failUnlessEqual(cprov.name, "rhn")

        # Make sure it comes back after serialization too
        sio = StringIO.StringIO()
        prd.serialize(sio)
        sio.seek(0)

        prd = proddef.ProductDefinition(fromStream = sio)
        cprov = prd.platform.getContentProvider()
        self.failUnlessEqual(cprov.name, "rhn")
        self.failUnlessEqual(
            [ (x.name, x.description, x.isSingleton)
                for x in cprov.contentSourceTypes ],
            expected)

    def testPlatformUsageTerms(self):
        prd = self.newProductDefinition()
        pld = prd.toPlatformDefinition()
        platformUsageTerms = "Vry sikrit"
        pld.setPlatformUsageTerms(platformUsageTerms)
        self.failUnlessEqual(pld.getPlatformUsageTerms(), platformUsageTerms)

        sio = StringIO.StringIO()
        pld.serialize(sio)
        sio.seek(0)

        pld = proddef.PlatformDefinition(fromStream = sio)
        self.failUnlessEqual(pld.getPlatformUsageTerms(), platformUsageTerms)

    class MockClient(object):
        class MockRepos(object):
            TroveMap = {
                ('platform-definition:source', 'localhost@platform:1/1-1',
                    None) :
                    ('platform-definition:source',
                        VFS('/localhost@platform:1/1-1'), ''),
                ('platform-definition:source', 'localhost@platform:1',
                    None) :
                    ('platform-definition:source',
                        VFS('/localhost@platform:1/1-1'), ''),
            }
            PlatformDefinitionXML = """
                <platformDefinition>
                  <baseFlavor>vanilla</baseFlavor>
                </platformDefinition>
            """

            class MockFileContents(object):
                def __init__(self, xmlData):
                    self.xmlData = xmlData
                def get(self):
                    return StringIO.StringIO(self.xmlData)

            def findTroves(self, label, trvSpecs, allowMissing = False):
                ret = dict()
                for key in trvSpecs:
                    if key not in self.TroveMap:
                        raise Exception("Mock me! %s" % (key, ))
                    ret[key] = [ self.TroveMap[key] ]
                return ret

            def getFileContents(self, fileSpecs):
                if fileSpecs[0][0] != 'fileId3':
                    raise Exception("Queried wrong file")
                return [ self.MockFileContents(self.PlatformDefinitionXML) ]

        class MockChangeSet(object):
            class MockThawChangeSet(object):
                FileList = [
                    ('pathId1',
                        proddef.PlatformDefinition._troveFileNames[-1],
                        'fileId1', 'fileVer1'),
                    ('pathId2', 'path2', '_', '_'),
                    ('pathId3',
                        proddef.PlatformDefinition._troveFileNames[0],
                        'fileId3', 'fileVer3'),
                ]
                NameVersionFlavor = ('platform-definition', 'host@ns:1', '')
                def getNewFileList(self):
                    return self.FileList
                def getNewNameVersionFlavor(self):
                    return self.NameVersionFlavor

            def iterNewTroveList(self):
                return [ self.MockThawChangeSet() ]

        def createChangeSet(self, jobList, withFiles = True,
                withFileContents = False):
            return self.MockChangeSet()

        def getRepos(self):
            return self.MockRepos()


    def testLoadPlatformDefinitionMultiFiles(self):
        prd = self.newProductDefinition()
        pld = prd.toPlatformDefinition()
        label = 'localhost@platform:1'

        client = self.MockClient()
        pld.loadFromRepository(client, label)
        self.failUnlessEqual(pld.baseFlavor, 'vanilla')

        # Now with getFileContentsFromTrove
        class MockClient2(self.MockClient):
            class MockRepos(self.MockClient.MockRepos):
                def getFileContentsFromTrove(self, name, version, flavor,
                                             fileList):
                    if fileList[0] != proddef.PlatformDefinition._troveFileNames[0]:
                        raise Exception("Queried wrong file")
                    return [ self.MockFileContents(self.PlatformDefinitionXML) ]

            def createChangeSet(self, jobList, withFiles = True,
                    withFileContents = False):
                raise Exception("client has getFileContentsFromTrove, should "
                    "not call createChangeSet")

        client = MockClient2()
        pld.loadFromRepository(client, label)
        self.failUnlessEqual(pld.baseFlavor, 'vanilla')

    def testLabelFromString(self):
        tests = [
            ('/foo@bar:baz/1.2-3', 'foo@bar:baz'),
            ('/foo@bar:baz', 'foo@bar:baz'),
            ('/a@b:c//foo@bar:baz/1.2-3', 'foo@bar:baz'),
            ('/a@b:c//foo@bar:baz', 'foo@bar:baz'),
            ('/foo@bar:c//baz/1.2-3', 'foo@bar:baz'),
            ('/foo@bar:c//baz', 'foo@bar:baz'),
            ('/foo@b:c//bar:baz/1.2-3', 'foo@bar:baz'),
            ('/foo@b:c//bar:baz', 'foo@bar:baz'),
            ('foo@bar:baz/1.2-3', 'foo@bar:baz'),
            ('foo@bar:baz', 'foo@bar:baz'),
        ]
        for verstr, expected in tests:
            self.failUnlessEqual(
                proddef.ProductDefinition.labelFromString(verstr), expected)

    def testVersionedRebase(self):
        prd = self.newProductDefinition()

        label = 'localhost@platform:1/1-1'

        class MockClient(self.MockClient):
            class MockRepos(self.MockClient.MockRepos):
                PlatformDefinitionXML = """
                    <platformDefinition>
                      <baseFlavor>vanilla</baseFlavor>
                      <searchPaths>
                        <searchPath isResolveTrove="true" troveName="group-plat"
                            isGroupSearchPathTrove="true"
                            label="localhost@plat:1/3-1"
                            isPlatformTrove="true" />
                        <searchPath isResolveTrove="true" troveName="group-cny"
                            isGroupSearchPathTrove="true"
                            label="localhost@cny:3" />
                      </searchPaths>
                    </platformDefinition>
                """
                TroveMap = self.MockClient.MockRepos.TroveMap.copy()
                TroveMap[('group-cny', 'localhost@cny:3', None)] = \
                    ('group-cny', VFS('/localhost@cny:3/3.0-4-5'), None)
                TroveMap[('group-plat', 'localhost@plat:1/1.2-3-4', None)] = \
                    ('group-plat', VFS('/localhost@plat:1/1.2-3-4'), None)

        client = MockClient()
        # The upstream platform has group-plat=3-1, but the TroveMap above
        # will verify we correctly query for 1.2-3-4
        prd.rebase(client, label, platformVersion = '1.2-3-4')

    def testSearchPathWithFlavor(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        prd.addSearchPath(label='localhost@other:label-1',
            isResolveTrove=True, isGroupSearchPathTrove=False,
            troveName='foo', flavor='bar !baz is: x86')
        sio = StringIO.StringIO()
        prd.serialize(sio)
        self.assertXMLEquals(sio.getvalue(), refSerializeSearchPathWithFlavor)

        self.failUnlessEqual(
            [ dict(troveName=x.troveName, label=x.label, flavor=x.flavor)
                for x in prd.getSearchPaths() ],
            [
                {
                    'flavor': None,
                    'troveName': 'group-foo',
                    'label': 'localhost@s:1'
                },
                {
                    'flavor': None,
                    'troveName': 'group-bar',
                    'label': 'localhost@s:2'
                },
                {
                    'flavor': 'bar !baz is: x86',
                    'troveName': 'foo',
                    'label': 'localhost@other:label-1'
                }
            ]
        )


    def testSearchPathNoTroveName(self):
        prd = proddef.ProductDefinition(fromStream = refSerialize1)
        prd.addSearchPath(label='localhost@other:label-1',
            isResolveTrove = True, isGroupSearchPathTrove = False)
        sio = StringIO.StringIO()
        prd.serialize(sio)
        self.assertXMLEquals(sio.getvalue(), refSerializeSearchPathNoTroveName)

        self.failUnlessEqual(
            [ dict(troveName = x.troveName, label = x.label,
                   isResolveTrove=x.isResolveTrove,
                   isGroupSearchPathTrove=x.isGroupSearchPathTrove)
                for x in prd.getSearchPaths() ],
            [
                {
                    'isGroupSearchPathTrove': True,
                    'troveName': 'group-foo',
                    'isResolveTrove': True,
                    'label': 'localhost@s:1'
                },
                {
                    'isGroupSearchPathTrove': True,
                    'troveName': 'group-bar',
                    'isResolveTrove': True,
                    'label': 'localhost@s:2'
                },
                {
                    'isGroupSearchPathTrove': False,
                    'troveName': None,
                    'isResolveTrove': True,
                    'label': 'localhost@other:label-1'
                }
            ]
        )

        self.failUnlessEqual(
            [ dict(troveName = x.troveName, label = x.label,
                   isResolveTrove=x.isResolveTrove,
                   isGroupSearchPathTrove=x.isGroupSearchPathTrove)
                for x in prd.getGroupSearchPaths() ],
            [
                {
                    'isGroupSearchPathTrove': True,
                    'troveName': 'group-foo',
                    'isResolveTrove': True,
                    'label': 'localhost@s:1'
                },
                {
                    'isGroupSearchPathTrove': True,
                    'troveName': 'group-bar',
                    'isResolveTrove': True,
                    'label': 'localhost@s:2'
                },
            ]
        )

    def testPublishUpstreamPlatformSearchPaths(self):
        pd = self.newProductDefinition()
        self.failUnlessEqual(pd.publishUpstreamPlatformSearchPaths, True)
        pd.publishUpstreamPlatformSearchPaths = False
        self.failUnlessEqual(pd.publishUpstreamPlatformSearchPaths, False)
        pd.publishUpstreamPlatformSearchPaths = True
        self.failUnlessEqual(pd.publishUpstreamPlatformSearchPaths, True)

        # Make sure the setting survived a reload
        pd.publishUpstreamPlatformSearchPaths = False
        sio = StringIO.StringIO()
        pd.serialize(sio)
        sio.seek(0)
        pd = proddef.ProductDefinition(fromStream=sio)
        self.failUnlessEqual(pd.publishUpstreamPlatformSearchPaths, False)

    def testToPlatformDefinition_publishUpstreamPlatformSearchPaths(self):
        prd = proddef.ProductDefinition(fromStream = refToPlat4)
        pld = proddef.PlatformDefinition(fromStream = refPlatSerialize1)
        nlabel = 'some@label:1'
        # Get rid of this product's search paths, so we can inherit the ones
        # from the platform
        prd._rootObj.searchPaths = None
        # and the platform's are something we control
        pld._rootObj.searchPaths = None
        pld.addSearchPath("group-plat1", label="localhost@plat:1")
        pld.addSearchPath("group-plat2", label="localhost@plat:2")
        prd._rebase(nlabel, pld)

        # Make sure the search paths are all coming from the platform
        self.failUnlessEqual([ x.troveName for x in prd.getSearchPaths() ],
            ['group-plat1', 'group-plat2'])

        npld = prd.toPlatformDefinition()
        self.failUnlessEqual(
            [ (x.troveName, x.label, x.isResolveTrove, x.isGroupSearchPathTrove)
                for x in npld.getSearchPaths() ],
            [
              ('group-foo', 'product.example.com@exm:awesome-1.0', True, True),
              ('group-awesome-dist', 'product.example.com@exm:awesome-1.0', True, True),
              ('group-plat1', 'localhost@plat:1', True, True),
              ('group-plat2', 'localhost@plat:2', True, True),
            ])

        # Reset the magic flag
        prd.publishUpstreamPlatformSearchPaths = False
        npld = prd.toPlatformDefinition()
        self.failUnlessEqual(
            [ (x.troveName, x.label, x.isResolveTrove, x.isGroupSearchPathTrove)
                for x in npld.getSearchPaths() ],
            [
              ('group-foo', 'product.example.com@exm:awesome-1.0', True, True),
              ('group-awesome-dist', 'product.example.com@exm:awesome-1.0', True, True),
            ])

class MigrationTest(BaseTest):
    def testMigration1(self):
        xmlPath = os.path.join(self.getArchiveDir(), 'migration', 'old-1.xml')
        legacyXml = open(xmlPath).read()
        prd = proddef.ProductDefinition(fromStream = legacyXml)

        # verify we captured the old schema def correctly
        self.failUnlessEqual(prd.preMigrateVersion, '1.3')

        sio = StringIO.StringIO()
        prd.serialize(sio)
        newXml = sio.getvalue()

        # ideally we'd compare the xml to a reference version but attribute
        # ordering appears to be a real problem
        self.failUnless(('version="%s"' % proddef.ProductDefinition.version)
            in newXml)
        self.failUnless('<build containerTemplateRef' in newXml)

    def testMigration2(self):
        prd = self.newProductDefinition()

        plt = prd.toPlatformDefinition()
        prd._rebase('NOM', plt)

        sio = StringIO.StringIO()
        prd.serialize(sio)
        prd = proddef.ProductDefinition(fromStream = sio.getvalue())
        self.failUnless(prd.platform.containerTemplates)
        self.failUnless(prd.platform.architectures)
        self.failUnless(prd.platform.flavorSets)
        self.failUnless(prd.platform.buildTemplates)
        self.failUnless(prd.platform.baseFlavor)
        self.failIf(prd.baseFlavor)
        # verify we captured the old schema def correctly
        self.failUnlessEqual(prd.preMigrateVersion, prd.version)
        # We don't migrate the platform sub-object individually
        self.failUnlessEqual(prd.platform.preMigrateVersion, None)

    def testMigration3(self):
        prd = proddef.ProductDefinition(fromStream = legacyXML)
        # test that flavors and architectures had decent guesses picked for them
        # these aren't necessarily the human concept of "best match" so much as
        # the actual best flavor based on the exisitng flavorSet
        self.assertEquals([(x.flavorSetRef, x.architectureRef) \
                for x in prd.getBuildDefinitions()],
                [('generic', 'x86'),
                 ('generic', 'x86_64'),
                 ('xen', 'x86'),
                 ('xen', 'x86_64'),
                 ('vmware', 'x86_64'),
                 ('virtual_iron', 'x86_64')])
        # verify we captured the old schema def correctly
        self.failUnlessEqual(prd.preMigrateVersion, '1.3')

    def testMigration4(self):
        stream = legacyXML.replace('rawHdImage', 'amiImage')
        stream = stream.replace('rawFsImage', 'amiImage')
        prd = proddef.ProductDefinition(fromStream = stream)
        # test that flavors and architectures had decent guesses picked for them
        # these aren't necessarily the human concept of "best match" so much as
        # the actual best flavor based on the exisitng flavorSet
        self.assertEquals([(x.flavorSetRef, x.architectureRef) \
                for x in prd.getBuildDefinitions()],
                [('generic', 'x86'),
                 ('generic', 'x86_64'),
                 ('ami', 'x86'),
                 ('ami', 'x86_64'),
                 ('vmware', 'x86_64'),
                 ('virtual_iron', 'x86_64')])

    def testMigration5(self):
        prd = self.newProductDefinition()
        # add a container template, this alone should be enough to stop the
        # addition of other defaults
        prd.addContainerTemplate(prd.imageType('installableIsoImage'))

        # we need a platform present for this test
        prd._ensurePlatformExists()
        sio = StringIO.StringIO()
        prd.serialize(sio)
        prd2 = proddef.ProductDefinition(fromStream = sio.getvalue())

        # ensure the marshalled proddef doesn't have the defaults
        self.assertEquals(prd2.platform.getContainerTemplates(), [])

    def testMigration__2_0__3_0__1(self):
        # Make sure we copy deprecated values correctly
        global XML
        data = XML.replace(proddef.ProductDefinition.version, "2.0")
        data = data.replace("amiHugeDiskMountpoint", "amiHugeDiskMountPoint")
        data = data.replace("vhdDiskType", "vhdDisktype")
        data = data.replace("vmwareImage", "netBootImage")
        prd = proddef.ProductDefinition(fromStream = data)
        image = prd.containerTemplates[0]
        self.failUnlessEqual(image.containerFormat, 'amiImage')
        self.failUnlessEqual(image.amiHugeDiskMountpoint, "/mnt/floppy")
        # verify we captured the old schema def correctly
        self.failUnlessEqual(prd.preMigrateVersion, '2.0')

        image = prd.containerTemplates[9]
        self.failUnlessEqual(image.containerFormat, 'vhdImage')
        self.failUnlessEqual(image.vhdDiskType, "dynamic")

        self.failUnlessEqual(prd.buildDefinition[4].containerTemplateRef,
            'netbootImage')
        # Make sure schema validates
        sio = StringIO.StringIO()
        prd.serialize(sio)

        sio = StringIO.StringIO()
        prd.serialize(sio, version = '2.0')
        # The global XML does not have the schema definition done with a local
        # name
        data = data.replace(
            'xsi:schemaLocation="http://www.rpath.com/permanent/rpd-2.0.xsd',
            'xsi:schemaLocation="http://www.rpath.com/permanent/rpd-2.0.xsd rpd-2.0.xsd')
        # We will not produce bad data again
        data = data.replace('amiHugeDiskMountPoint', 'amiHugeDiskMountpoint')
        data = data.replace('vhdDisktype', 'vhdDiskType')
        data = data.replace('netBootImage', 'netbootImage')
        self.assertXMLEquals(sio.getvalue(), data)

    def testMigrationFrom_1_0(self):
        xmlPath = os.path.join(self.getArchiveDir(), 'migration',
            'product-definition-1.0-1.xml')
        pd = proddef.ProductDefinition(fromStream = file(xmlPath))
        self.failUnlessEqual(
            [(x.troveName, x.label) for x in pd.searchPaths],
            [('group-os', 'conary.rpath.com@rpl:2')])
        # verify we captured the old schema def correctly
        self.failUnlessEqual(pd.preMigrateVersion, '1.0')

    def testMigrationFrom_1_1(self):
        xmlPath = os.path.join(self.getArchiveDir(), 'migration',
            'product-definition-1.1-1.xml')
        pd = proddef.ProductDefinition(fromStream = file(xmlPath))
        self.failUnlessEqual(pd.platform.sourceTrove, "aa")
        self.failUnlessEqual(
            [ (x.architectureRef, x.containerTemplateRef)
                for x in pd.buildDefinition ],
            [ ('x86', 'installableIsoImage'), ('x86_64', 'installableIsoImage')])
        # verify we captured the old schema def correctly
        self.failUnlessEqual(pd.preMigrateVersion, '1.1')

    def testMigrationFrom_1_2(self):
        xmlPath = os.path.join(self.getArchiveDir(), 'migration',
            'product-definition-1.2-1.xml')
        pd = proddef.ProductDefinition(fromStream = file(xmlPath))
        # verify we captured the old schema def correctly
        self.failUnlessEqual(pd.preMigrateVersion, '1.2')
        # Not looking for something in particular

    def testMigrationFrom_1_3(self):
        xmlPath = os.path.join(self.getArchiveDir(), 'migration',
            'product-definition-1.3-1.xml')
        pd = proddef.ProductDefinition(fromStream = file(xmlPath))
        # verify we captured the old schema def correctly
        self.failUnlessEqual(pd.preMigrateVersion, '1.3')
        # Not looking for something in particular

    def testMigrationFrom_2_0(self):
        xmlPath = os.path.join(self.getArchiveDir(), 'migration',
            'product-definition-2.0-1.xml')
        pd = proddef.ProductDefinition(fromStream = file(xmlPath))
        # verify we captured the old schema def correctly
        self.failUnlessEqual(pd.preMigrateVersion, '2.0')
        # Not looking for something in particular

        sio = StringIO.StringIO()
        pd.serialize(sio, version = '2.0')
        self.assertXMLEquals(sio.getvalue(), file(xmlPath).read())

    def testMigrationFrom_3_0(self):
        xmlPath = os.path.join(self.getArchiveDir(), 'migration',
            'product-definition-3.0-1.xml')
        pd = proddef.ProductDefinition(fromStream = file(xmlPath))
        # verify we captured the old schema def correctly
        self.failUnlessEqual(pd.preMigrateVersion, '3.0')
        # Not looking for something in particular

        sio = StringIO.StringIO()
        pd.serialize(sio, version = '3.0')
        self.assertXMLEquals(sio.getvalue(), file(xmlPath).read())

refSerialize1 = """\
<?xml version='1.0' encoding='UTF-8'?>
<productDefinition xmlns="http://www.rpath.com/permanent/rpd-%(version)s.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-%(version)s.xsd rpd-%(version)s.xsd" version="%(version)s">
  <productName>My Awesome Appliance</productName>
  <productShortname>awesome</productShortname>
  <productDescription>
      This here is my awesome appliance.
      Is it not nifty?
      Worship the appliance.
  </productDescription>
  <productVersion>1.0</productVersion>
  <productVersionDescription>
      Version 1.0 features "stability" and "usefulness", which is a
      vast improvement over our pre-release code.
  </productVersionDescription>
  <conaryRepositoryHostname>product.example.com</conaryRepositoryHostname>
  <conaryNamespace>exm</conaryNamespace>
  <imageGroup>group-awesome-dist</imageGroup>
  <baseFlavor>is: x86 x86_64</baseFlavor>
  <stages>
    <stage labelSuffix="-devel" name="devel"/>
    <stage labelSuffix="-qa" name="qa"/>
    <stage labelSuffix="" name="release"/>
  </stages>
  <searchPaths>
    <searchPath isResolveTrove="true" troveName="group-foo" isGroupSearchPathTrove="true" label="localhost@s:1" version="1-1-1"/>
    <searchPath isResolveTrove="true" troveName="group-bar" isGroupSearchPathTrove="true" label="localhost@s:2" version="1-1-1"/>
  </searchPaths>
  <architectures>
    <architecture flavor="is: x86 x86_64" displayName="64 bit" name="x86_64"/>
  </architectures>
  <flavorSets>
    <flavorSet flavor="~cheese" displayName="cheese" name="cheese"/>
  </flavorSets>
  <containerTemplates>
    <image containerFormat="installableIsoImage"/>
  </containerTemplates>
  <buildDefinition>
    <build containerTemplateRef="installableIsoImage" architectureRef="x86_64" name="x86_64 build">
      <stage ref="qa"/>
      <stage ref="release"/>
      <imageGroup>group-foo</imageGroup>
    </build>
  </buildDefinition>
</productDefinition>
""" % dict(version = proddef.ProductDefinition.version)

# Change version to something we still know about
refSerialize2 = refSerialize1.replace(proddef.ProductDefinition.version, '2.0')

platform1 = """
  <platform sourceTrove="foo=bar@baz:1">
    <baseFlavor>black-coffee,!cream,~sugar</baseFlavor>
  </platform>"""

refSerialize3 = refSerialize1.replace('</buildDefinition>',
    '</buildDefinition>%s' % platform1)

refSerializeSearchPathNoTroveName = refSerialize1.replace('</searchPaths>',
    """<searchPath isGroupSearchPathTrove="false" isResolveTrove="true" label="localhost@other:label-1"/>
</searchPaths>""")

refSerializeSearchPathWithFlavor = refSerialize1.replace('</searchPaths>',
    """<searchPath isGroupSearchPathTrove="false" isResolveTrove="true" label="localhost@other:label-1" troveName="foo" flavor="bar !baz is: x86"/>
</searchPaths>""")


platform2 = """
  <platform sourceTrove="foo=bar@baz:1" useLatest="true">
    <baseFlavor>black-coffee,!cream,~sugar</baseFlavor>
    <searchPaths>
      <searchPath isResolveTrove="true" troveName="c" isGroupSearchPathTrove="true" label="d"/>
    </searchPaths>
    <factorySources>
      <factorySource troveName="a" label="b"/>
    </factorySources>
    <flavorSets>
      <flavorSet name='foo' displayName='foo' flavor='foo'/>
    </flavorSets>
  </platform>"""

refSerialize4 = refSerialize1.replace('</buildDefinition>',
    '</buildDefinition>%s' % platform2)

refPlatSerialize1 = """\
<?xml version="1.0" encoding="UTF-8"?>
<platformDefinition xmlns="http://www.rpath.com/permanent/rpd-%(version)s.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-%(version)s.xsd rpd-%(version)s.xsd" version="%(version)s">
  <platformName>My Awesome Appliance</platformName>
  <baseFlavor>black-coffee,!cream,~sugar is: x86 x86_64</baseFlavor>
  <platformInformation>
    <originLabel>bar@baz:1</originLabel>
  </platformInformation>
  <searchPaths>
    <searchPath isResolveTrove="true" troveName="group-foo" isGroupSearchPathTrove="true" label="product.example.com@exm:awesome-1.0"/>
    <searchPath isPlatformTrove="true" isResolveTrove="true" troveName="group-awesome-dist" isGroupSearchPathTrove="true" label="product.example.com@exm:awesome-1.0"/>
    <searchPath isResolveTrove="true" troveName="group-foo" isGroupSearchPathTrove="true" label="localhost@s:1" version="1-1-1"/>
    <searchPath isResolveTrove="true" troveName="group-bar" isGroupSearchPathTrove="true" label="localhost@s:2" version="1-1-1"/>
  </searchPaths>
  <factorySources>
    <factorySource troveName="a" label="b"/>
  </factorySources>
  <architectures>
    <architecture flavor="is: x86 x86_64" displayName="64 bit" name="x86_64"/>
  </architectures>
  <flavorSets>
    <flavorSet flavor="~cheese" displayName="cheese" name="cheese"/>
  </flavorSets>
  <containerTemplates>
    <image containerFormat="installableIsoImage"/>
  </containerTemplates>
</platformDefinition>
""" % dict(version = proddef.ProductDefinition.version)

refToPlat4 = refSerialize1.replace('  <searchPaths>', '''\
  <platformInformation>
    <originLabel>bar@baz:1</originLabel>
  </platformInformation>
  <searchPaths>''')

refPlatSerialize2 = refPlatSerialize1.replace("""
  <flavorSets>
    <flavorSet flavor="~cheese" displayName="cheese" name="cheese"/>
  </flavorSets>""", "")

refSerialize5 = """\
<?xml version='1.0' encoding='UTF-8'?>
<productDefinition xmlns="http://www.rpath.com/permanent/rpd-%(version)s.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-%(version)s.xsd rpd-%(version)s.xsd" version="%(version)s">
  <productName>My Awesome Appliance</productName>
  <productShortname>awesome</productShortname>
  <productDescription>Some long
product description
</productDescription>
  <productVersion>1.0</productVersion>
  <productVersionDescription>This version
has bugs
</productVersionDescription>
  <conaryRepositoryHostname>localhost</conaryRepositoryHostname>
  <conaryNamespace>exm</conaryNamespace>
  <imageGroup>group-awesome-dist</imageGroup>
  <baseFlavor>~!perl</baseFlavor>
  <stages>
    <stage labelSuffix="-devel" name="devel"/>
    <stage labelSuffix="-qa" name="qa"/>
    <stage labelSuffix="" name="release"/>
  </stages>
  <searchPaths>
    <searchPath troveName="group-rap-standard" label="rap.rpath.com@rpath:linux-1"/>
  </searchPaths>
  <factorySources>
    <factorySource troveName="group-factories" label="products.rpath.com@rpath:factories-1"/>
  </factorySources>
  <buildDefinition>
    <build baseFlavor="is: x86" name="x86 Installable ISO Build">
      <installableIsoImage/>
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
    </build>
    <build baseFlavor="is: x86 x86_64" name="x86-64 Installable ISO Build">
      <installableIsoImage/>
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
    </build>
    <build baseFlavor="~xen, ~domU is: x86" name="x86 Citrix Xenserver Virtual Appliance">
      <xenOvaImage/>
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
    </build>
    <build baseFlavor="~xen, ~domU is: x86" name="Another Xen Build">
      <rawHdImage autoResolve="true" baseFileName="/poo/moo/foo"/>
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
    </build>
    <build baseFlavor="~vmware is: x86 x86_64" name="VMWare build">
      <vmwareImage autoResolve="true" baseFileName="foobar"/>
      <stage ref="devel"/>
      <stage ref="qa"/>
    </build>
    <build baseFlavor="~vmware is: x86 x86_64" name="Totally VMware optional build from a different group">
      <vmwareImage/>
      <imageGroup>group-foo-dist</imageGroup>
    </build>
  </buildDefinition>
</productDefinition>
""" % dict(version = proddef.ProductDefinition.version)

archImageTempl1 = """
  <architectures>
    <architecture flavor="grub.static, dietlibc is:x86(i486, i586, cmov, mmx, sse)" displayName="32 bit" name="x86"/>
    <architecture flavor="!grub.static, !dietlibc is:x86_64 x86(i486, i586, cmov, mmx, sse)" displayName="64 bit" name="x86_64"/>
  </architectures>"""

refSerialize6 = refSerialize1.replace("""
  <architectures>
    <architecture flavor="is: x86 x86_64" displayName="64 bit" name="x86_64"/>
  </architectures>""",
    archImageTempl1).replace("""<flavorSets>
    <flavorSet flavor="~cheese" displayName="cheese" name="cheese"/>
  </flavorSets>
  <containerTemplates>
    <image containerFormat="installableIsoImage"/>
  </containerTemplates>""", """<flavorSets>
    <flavorSet flavor="~cheese" displayName="cheese" name="cheese"/>
    <flavorSet flavor="~xen, ~domU, ~!vmware" displayName="xen domU" name="xen domU"/>
    <flavorSet flavor="~vmware, ~!xen, ~!domU" displayName="vmware" name="vmware"/>
  </flavorSets>
  <containerTemplates>
    <image containerFormat="installableIsoImage"/>
    <image containerFormat="rawFsImage"/>
  </containerTemplates>""")

refSerialize7 = refSerialize6.replace('</build>',
    """</build>
    <build containerTemplateRef="installableIsoImage" architectureRef="x86" name="build1" flavorSetRef="cheese">
      <stage ref="devel"/>
      <stage ref="qa"/>
      <stage ref="release"/>
    </build>""")

refSecondaryLabels = """
  <secondaryLabels>
    <secondaryLabel name="Xen">-xen</secondaryLabel>
    <secondaryLabel name="VMware">my@label:vmware</secondaryLabel>
  </secondaryLabels>"""

refSerialize8 = refSerialize1.replace('</searchPaths>',
    '</searchPaths>%s' % refSecondaryLabels)

refPromoteMaps = """\
      <promoteMaps>
        <promoteMap name="myblah" label="host@myblah:devel"/>
        <promoteMap name="myblip" label="host@myblip:devel"/>
      </promoteMaps>"""

refSerialize9 = refSerialize1.replace('name="devel"/>',
    """name="devel">
%s
    </stage>""" % refPromoteMaps)

platform3 = """
  <platform sourceTrove="foo=bar@baz:1" useLatest="true">
    <baseFlavor>black-coffee,!cream,~sugar</baseFlavor>
    <searchPaths>
      <searchPath isResolveTrove="true" troveName="c" isGroupSearchPathTrove="true" label="d"/>
    </searchPaths>
    <factorySources>
      <factorySource troveName="a" label="b"/>
    </factorySources>
  </platform>"""

refSerialize10 = refSerialize1.replace('</buildDefinition>',
    '</buildDefinition>%s' % platform3)

sourceGroup = """
  <sourceGroup>group-awesome</sourceGroup>"""

sourceGroup2 = """
  <sourceGroup>group-radical</sourceGroup>"""

refSerialize11 = refSerialize1.replace('</imageGroup>',
    '</imageGroup>%s' % sourceGroup, 1)

refSerialize12 = refSerialize1.replace('</imageGroup>',
    '</imageGroup>%s' % sourceGroup)

refPlatSerialize6 = """<?xml version='1.0' encoding='UTF-8'?>
<platformDefinition xmlns="http://www.rpath.com/permanent/rpd-%(version)s.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-%(version)s.xsd rpd-%(version)s.xsd" version="%(version)s">
  <platformName>My Awesome Appliance</platformName>
  <baseFlavor>black-coffee,!cream,~sugar is: x86 x86_64</baseFlavor>
  <platformInformation>
    <originLabel>bar@baz:1</originLabel>
  </platformInformation>
  <searchPaths>
    <searchPath isResolveTrove="true" troveName="group-foo" isGroupSearchPathTrove="true" label="product.example.com@exm:awesome-1.0"/>
    <searchPath isPlatformTrove="true" isResolveTrove="true" troveName="group-awesome-dist" isGroupSearchPathTrove="true" label="product.example.com@exm:awesome-1.0"/>
    <searchPath isResolveTrove="true" troveName="group-foo" isGroupSearchPathTrove="true" label="localhost@s:1" version="1-1-1"/>
    <searchPath isResolveTrove="true" troveName="group-bar" isGroupSearchPathTrove="true" label="localhost@s:2" version="1-1-1"/>
  </searchPaths>
  <factorySources>
    <factorySource troveName="a" label="b"/>
  </factorySources>
  <architectures>
    <architecture flavor="!grub.static, !dietlibc is:x86_64 x86(i486, i586, cmov, mmx, sse)" displayName="64 bit" name="x86_64"/>
  </architectures>
  <containerTemplates>
    <image containerFormat="installableIsoImage"/>
  </containerTemplates>
</platformDefinition>
""" % dict(version = proddef.ProductDefinition.version)

refPlatNameVersionTrove1 = """
<?xml version="1.0" encoding="UTF-8"?>
<productDefinition xmlns="http://www.rpath.com/permanent/rpd-%(version)s.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-%(version)s.xsd rpd-%(version)s.xsd" version="%(version)s">
  <productName>product name</productName>
  <productShortname>product short name</productShortname>
  <productDescription>product description</productDescription>
  <productVersion>0.1</productVersion>
  <productVersionDescription>version 0.1 description</productVersionDescription>
  <conaryRepositoryHostname>conary.example.com</conaryRepositoryHostname>
  <conaryNamespace>lnx</conaryNamespace>
  <imageGroup>group-os</imageGroup>
  <baseFlavor></baseFlavor>
  <stages>
    <stage labelSuffix="-devel" name="devel"/>
  </stages>
  <architectures>
    <architecture flavor="is: x86" displayName="32 bit" name="x86"/>
  </architectures>
  <containerTemplates>
    <image containerFormat="installableIsoImage"/>
  </containerTemplates>
  <buildDefinition>
    <build containerTemplateRef="installableIsoImage" architectureRef="x86" name="x86 Installable ISO Build">
      <stage ref="devel"/>
    </build>
  </buildDefinition>
  <platform>
    <baseFlavor>Foo</baseFlavor>
  </platform>
</productDefinition>""" % dict(version = proddef.ProductDefinition.version)

refPlatNameVersionTrove2 = """
<?xml version="1.0" encoding="UTF-8"?>
<productDefinition xmlns="http://www.rpath.com/permanent/rpd-%(version)s.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-%(version)s.xsd rpd-%(version)s.xsd" version="%(version)s">
  <productName>product name</productName>
  <productShortname>product short name</productShortname>
  <productDescription>product description</productDescription>
  <productVersion>0.1</productVersion>
  <productVersionDescription>version 0.1 description</productVersionDescription>
  <conaryRepositoryHostname>conary.example.com</conaryRepositoryHostname>
  <conaryNamespace>lnx</conaryNamespace>
  <imageGroup>group-os</imageGroup>
  <baseFlavor></baseFlavor>
  <stages>
    <stage labelSuffix="-devel" name="devel"/>
  </stages>
  <architectures>
    <architecture flavor="is: x86" displayName="32 bit" name="x86"/>
  </architectures>
  <containerTemplates>
    <image containerFormat="installableIsoImage"/>
  </containerTemplates>
  <buildDefinition>
    <build containerTemplateRef="installableIsoImage" architectureRef="x86" name="x86 Installable ISO Build">
      <stage ref="devel"/>
    </build>
  </buildDefinition>
  <platform>
    <platformName>some name</platformName>
    <platformVersionTrove>some source trove</platformVersionTrove>
    <baseFlavor>Foo</baseFlavor>
  </platform>
</productDefinition>""" % dict(version = proddef.ProductDefinition.version)

refPlatAutoLoadRecipes1 = refPlatNameVersionTrove1

refPlatAutoLoadRecipes2 = """
<?xml version="1.0" encoding="UTF-8"?>
<productDefinition xmlns="http://www.rpath.com/permanent/rpd-%(version)s.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpd-%(version)s.xsd rpd-%(version)s.xsd" version="%(version)s">
  <productName>product name</productName>
  <productShortname>product short name</productShortname>
  <productDescription>product description</productDescription>
  <productVersion>0.1</productVersion>
  <productVersionDescription>version 0.1 description</productVersionDescription>
  <conaryRepositoryHostname>conary.example.com</conaryRepositoryHostname>
  <conaryNamespace>lnx</conaryNamespace>
  <imageGroup>group-os</imageGroup>
  <baseFlavor></baseFlavor>
  <stages>
    <stage labelSuffix="-devel" name="devel"/>
  </stages>
  <architectures>
    <architecture flavor="is: x86" displayName="32 bit" name="x86"/>
  </architectures>
  <containerTemplates>
    <image containerFormat="installableIsoImage"/>
  </containerTemplates>
  <buildDefinition>
    <build containerTemplateRef="installableIsoImage" architectureRef="x86" name="x86 Installable ISO Build">
      <stage ref="devel"/>
    </build>
  </buildDefinition>
  <platform>
    <baseFlavor>Foo</baseFlavor>
    <autoLoadRecipes>
      <autoLoadRecipe troveName="trove1" label="foo:bar-1"/>
      <autoLoadRecipe troveName="trove2" label="foo:bar-2"/>
    </autoLoadRecipes>
  </platform>
</productDefinition>""" % dict(version = proddef.ProductDefinition.version)

# Secret key , passphrase is rpath
secretKey = """\
-----BEGIN PGP PRIVATE KEY BLOCK-----
Version: GnuPG v2.0.9 (GNU/Linux)

lQHhBEuIJTQRBADx975hVuvL3gnzQkyL2ESc4va0NsHoD7VvUdZZa18RcMyGa/kn
8edixGgtOmR+R5x43CZ3CysNooqtC8O5qutrSKDVVvvML7Q1tMobf8HiiodcPOoS
KQeZZOv7rePpbw74ltoYax9zuVf02iGxMh3b/YIdeDE9L+LQB8hPwujl7wCgxlmL
Xf/haNN2LIORTpDdQwLZFoUD/jcKV2YkPSbm921sBlRR64qA+mrRfRjuc/luw9W8
A53/f+AXPLQn+N8CQInfOBKnnf5hDkvfTNScC41OOoAeaiTe1mL88gZj5V2EkvXp
J9A7zc5oyw0WiQHbVFhLcb78nkPjTPjxNFa5h9aiPeWizKcIndNG3nUID7tZndVN
XXJaBACWHBHrIDwNht0dSUZ9f+eb5GcZhsXnphLm7Ux69D82TGAYc/YqRZTNR+kp
od1U5I3F3WlIyt17qZwJY38dzU6dU3y8wd/P2lYbrO56LmNzu22jVHYBG8NsBQGn
6+eWFOZpMSFwxm7XvAfciIwlSOQW7/u7gXgRL1ylgdZY0U7JbP4CAwKlDrwZVjN4
DmB9rBESwrB/8mIWWRcQu/fvfZMpXqc0AlDkD0yFWf+oWUR4XOXjfBTL9DJNP1bx
QwlUMLQcU3VwZXIgS2V5IDx0ZXN0QGV4YW1wbGUuY29tPohgBBMRAgAgBQJLiCU0
AhsDBgsJCAcDAgQVAggDBBYCAwECHgECF4AACgkQwax2mcUVpcGxRACeN7e7yt3T
bRugKfuLYeALhQ6PeiUAoJ9fDzmlylZLglJN3tHb9pAbFH/qnQFYBEuIJTQQBACY
bTParAXZ8ysFlEv6X5tblpUvwtYiqYnhUJF+0X+qnwTTGGUJPxWp83qLRnF3yJkZ
owuDUDtQTRKd5SoOrATTz6CEvkjhFHHVmsVA0dSFeo0Bl0kr4AxXjNR3rYLA0Ah4
PREOeo6jbh5M2n7ZnvA69BP4rT5yrFNsE/G/c4j9owADBQP+JEcB1KBo98x2ywQC
OMXzeQSZkRMB3nY3B3PmBki8k/PMCowelqcC5CViu8aj2Dd+GzrizBAGALgWU1xk
bu1gvg6cJEfSn3A+ajRibfxgCp5Hku8vl77bPBsZzu3pOq+6HXGgLWU6h+5S9xIb
8go1R/PcFzjv1WThWvlDpbEo7Rr+AgMCpQ68GVYzeA5gbxRGVJ9b+CPQlw1d1VcG
qX9Ox8s3nM8fMvv1K1tBIZUKpoT1/FmSuR+3nlzdkiSLJ1uJTbGYHLEHynAXLy2I
SQQYEQIACQUCS4glNAIbDAAKCRDBrHaZxRWlwdbFAKCDCVhvqXuCisfJXHgcqSlA
3B/C5gCfVqembUTkXUE4Z7Yxk+n3TPi/+Tc=
=asN5
-----END PGP PRIVATE KEY BLOCK-----
"""
