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

dist_files = Makefile $(SCHEMA_FILES)
SCHEMA_FILES = rpd-1.0.xsd rpd-1.1.xsd

all: default-all

install: all default-install $(DESTDIR)$(datadir)/rpath_common
	install $(SCHEMA_FILES) $(DESTDIR)$(datadir)/rpath_common/

$(DESTDIR)$(datadir)/rpath_common:
	install -d -m755 $@

dist: default-dist

clean: default-clean

include ../Make.rules
include ../Make.defs
