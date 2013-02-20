#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


"""
Example code for interacting with rPath product definition xml files.
"""

from rpath_proddef import api1 as proddef
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
# Don't use addPromoteMap unless you know what you're doing; see
# https://issues.rpath.com/browse/RPCL-17 for more information on
# how to use them.  These maps cause packages in devel groups to
# be flattened into the main label on promote to QA and promotes
# from example to be flattened into an alternate label.
prodDef.addStage(name='devel', labelSuffix='-devel',
    promoteMaps = [('contrib', 'contrib.rpath.org@rpl:2'),
                   ('other', 'example.rpath.org@rpl:2')])
prodDef.addStage(name='qa', labelSuffix='-qa',
    promoteMaps = [('contrib', '/product.example.com@exm:group-awesome-dist-1-qa'),
                   ('other', '/product.example.com@exm:other-1-qa') ])
prodDef.addStage(name='release', labelSuffix='',
    promoteMaps = [('other', '/product.example.com@exm:other-1')])

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

prodDef.serialize(sys.stdout)
sys.stdout.flush()
sys.exit(0)
