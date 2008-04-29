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
stages = [dict(name='devel',
               label='product.example.com@exm:product-1-devel'),
          dict(name='qa',
               label='product.example.com@exm:product-1-qa'),
          dict(name='release',
               label='product.example.com@exm:product-1')]


upstreamSources = [dict(troveName='group-rap-standard', 
                        label='rap.rpath.com@rpath:linux-1'),
                   dict(troveName='group-postgres', 
                        label='products.rpath.com@rpath:postgres-8.2')]

buildDefinition = [dict(baseFlavor='is: x86',
                        installableIsoImage=dict()),
                   dict(baseFlavor='is: x86_64',
                        installableIsoImage=dict()),
                   dict(baseFlavor='~xen, ~domU is: x86',
                        rawFsImage=dict()),
                   dict(baseFlavor='~xen, ~domU is: x86 x86_64',
                        rawHdImage=dict(autoResolve=True,
                                        baseFileName='/proc/foo/moo')
                       ),
                   dict(baseFlavor='~vmware is: x86 x86_64',
                        vmwareImage=dict(baseFileName='foobar',
                                         autoResolve=True)
                       )
                  ]

prodDef = ProductDefinition(dict(baseFlavor=baseFlavor,
                                 stages=stages,
                                 upstreamSources=upstreamSources,
                                 buildDefinition=buildDefinition))

print prodDef.toXml()
