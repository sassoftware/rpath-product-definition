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


dist_files = Makefile $(SCHEMA_FILES)
SCHEMA_FILES = $(wildcard *.xsd)

all: default-all

include ../Make.rules
include ../Make.defs

install: all default-install $(DESTDIR)$(datadir)/rpath_proddef
	install -m644 $(SCHEMA_FILES) $(DESTDIR)$(datadir)/rpath_proddef/

$(DESTDIR)$(datadir)/rpath_proddef:
	install -d -m755 $@

validate-schema:
	xmllint -schema http://www.w3.org/2001/XMLSchema.xsd $(SCHEMA_FILES) > /dev/null

dist: default-dist

clean: default-clean
