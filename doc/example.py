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
Example code for interacting with rPath product definition xml files.
"""

from rpath_common.proddef import api1 as proddef
import sys

# This is an example of how this module would be used to generate the XML
# for the proddef source trove.
#
# This should produce an xml file equivalent to example.xml
baseFlavor = """
    ~MySQL-python.threadsafe, ~X, ~!alternatives, !bootstrap,
    ~builddocs, ~buildtests, !cross, ~desktop, ~!dietlibc, ~!dom0, ~!domU,
    ~emacs, ~gcj, ~gnome, ~grub.static, ~gtk, ~ipv6, ~kde, ~!kernel.debug,
    ~kernel.debugdata, ~!kernel.numa, ~kernel.smp, ~krb, ~ldap, ~nptl,
    ~!openssh.smartcard, ~!openssh.static_libcrypto, pam, ~pcre, ~perl,
    ~!pie, ~!postfix.mysql, ~python, ~qt, ~readline, ~!sasl, ~!selinux,
    ~sqlite.threadsafe, ssl, ~tcl, tcpwrappers, ~tk, ~uClibc, !vmware,
    ~!xen, ~!xfce, ~!xorg-x11.xprint
    """
productDescription = """
      This here is my awesome appliance.
      Is it not nifty?
      Worship the appliance.
"""

productVersionDescription = """
      Version 1.0 features "stability" and "usefulness", which is a 
      vast improvement over our pre-release code.
"""

prodDef = proddef.ProductDefinition()
prodDef.setProductName("My Awesome Appliance")
prodDef.setProductShortname("awesome")
prodDef.setProductDescription(productDescription)
prodDef.setProductVersion("1.0")
prodDef.setProductVersionDescription(productVersionDescription)
prodDef.setConaryRepositoryHostname("product.example.com")
prodDef.setConaryNamespace("exm")
prodDef.setImageGroup("group-awesome-dist")
prodDef.setBaseFlavor(baseFlavor)
prodDef.addStage(name='devel', labelSuffix='-devel')
prodDef.addStage(name='qa', labelSuffix='-qa')
prodDef.addStage(name='release', labelSuffix='')

prodDef.addSearchPath(troveName='group-rap-standard',
                        label='rap.rpath.com@rpath:linux-1')
prodDef.addSearchPath(troveName='group-postgres',
                        label='products.rpath.com@rpath:postgres-8.2')
prodDef.addFactorySource(troveName='group-factories',
                        label='products.rpath.com@rpath:factories-1')

prodDef.addBuildDefinition(name='x86 Installable ISO Build',
                        baseFlavor='is: x86',
                        imageType=prodDef.imageType('installableIsoImage'),
                        stages = ['devel', 'qa', 'release'])

prodDef.addBuildDefinition(name='x86-64 Installable ISO Build',
                        baseFlavor='is: x86 x86_64',
                        imageType=prodDef.imageType('installableIsoImage'),
                        stages = ['devel', 'qa', 'release'])

prodDef.addBuildDefinition(name='x86 Citrix Xenserver Virtual Appliance',
                        baseFlavor='~xen, ~domU is: x86',
                        imageType=prodDef.imageType('xenOvaImage'),
                        stages = ['devel', 'qa', 'release'])

prodDef.addBuildDefinition(name='Another Xen Build',
                        baseFlavor='~xen, ~domU is: x86',
                        imageType=prodDef.imageType('rawHdImage',
                            dict(autoResolve="true",
                            baseFileName="/poo/moo/foo")),
                        stages = ['devel', 'qa', 'release'])

prodDef.addBuildDefinition(name='VMWare build',
                        baseFlavor='~vmware is: x86 x86_64',
                        imageType=prodDef.imageType('vmwareImage',
                            dict(autoResolve="true",
                            baseFileName="foobar")),
                        stages = ['devel', 'qa'])

prodDef.addBuildDefinition(name='Totally VMware optional build from a different group',
                        baseFlavor='~vmware is: x86 x86_64',
                        imageGroup='group-foo-dist',
                        imageType=prodDef.imageType('vmwareImage'))

# Don't use addSecondaryLabel unless you know what you're doing
prodDef.addSecondaryLabel('Xen', '-xen')
prodDef.addSecondaryLabel('VMware', 'my@label:vmware')

# Don't use addPromoteMap unless you know what you're doing
prodDef.addPromoteMap('from@blah:1', 'to@blah:1')
prodDef.addPromoteMap('from@bar:2', 'to@blip:2')

prodDef.serialize(sys.stdout)
sys.stdout.flush()
sys.exit(0)
