#!/usr/bin/python
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


import sys
import os
import pwd
from testrunner import suite


class Suite(suite.TestSuite):
    testsuite_module = sys.modules[__name__]


    def getCoverageExclusions(self, environ):
        return [r'generatedssuper\.py',
                r'gends_user_methods\.py',
                r'xml_.*/.*\.py']

    def sortTests(self, tests):
        order = {'smoketest': 0, 
                 'unit_test' :1,
                 'functionaltest':2}
        maxNum = len(order)
        tests = [ (test,test.index('test')) for test in tests]
        tests = sorted((order.get(test[:index+4], maxNum), test)
                       for (test, index) in tests)
        tests = [ x[1] for x in tests ]
        return tests


if __name__ == '__main__':
    Suite().run()
