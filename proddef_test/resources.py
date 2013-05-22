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


import os


def get_path(*subpath):
    return os.path.join(_test_root, *subpath)


def get_archive(*subpath):
    return get_path('proddef_test', 'archive', *subpath)


def get_xsd(*subpath):
    if os.path.exists(get_path('xsd')):
        return get_path('xsd', *subpath)
    else:
        assert os.path.isdir('/usr/share/rpath_proddef')
        return os.path.join('/usr/share/rpath_proddef', *subpath)


def _get_test_root():
    modname = __name__.split('.')
    modroot = os.path.abspath(__file__)
    while modname:
        modroot = os.path.dirname(modroot)
        modname.pop()
    return modroot
_test_root = _get_test_root()
