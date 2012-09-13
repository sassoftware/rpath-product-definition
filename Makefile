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


all: default-subdirs default-all

.PHONY: clean dist install html docs

export TOPDIR = $(shell pwd)
# DISTDIR is not a typo: "rpath-product-definition" is the name
# of the package that contains the code; "product-definition" is
# the name of packages containing a product definition
export DISTDIR = $(TOPDIR)/rpath-product-definition-$(VERSION)

SUBDIRS=rpath_proddef xsd doc

dist_files = $(extra_files)

.PHONY: clean dist install subdirs

subdirs: default-subdirs

install: install-subdirs install-compat

clean: clean-subdirs default-clean


generate:
	make -C rpath_proddef generate

validate-schema:
	make -C xsd validate-schema



install-compat:
	# Compatibility stubs for old rbuild (RPCL-63)
	mkdir -p $(DESTDIR)$(sitedir)rpath_common/proddef
	echo "from rpath_proddef.api1 import *" >$(DESTDIR)$(sitedir)rpath_common/proddef/__init__.py
	echo "from rpath_proddef.api1 import *" >$(DESTDIR)$(sitedir)rpath_common/proddef/api1.py
	python -c "from compileall import *; compile_dir('$(DESTDIR)$(sitedir)rpath_common/proddef', 10, '$(sitedir)rpath_common/proddef')"
	python -O -c "from compileall import *; compile_dir('$(DESTDIR)$(sitedir)rpath_common/proddef', 10, '$(sitedir)rpath_common/proddef')"

dist:
	if ! grep "^Changes in $(VERSION)" NEWS > /dev/null 2>&1; then \
		echo "no NEWS entry"; \
		exit 1; \
	fi
	$(MAKE) forcedist


archive: checkversion
	hg archive --exclude .hgignore -t tbz2 $(DISTDIR).tar.bz2

forcedist: archive

doc: html
html: default-subdirs
	scripts/generate_docs.sh

checkversion:
	@echo $(VERSION) | grep "^$(schemaversion)" || { echo "version mismatch between latest schema $(schemaversion) and product version $(VERSION)"; exit 1; }

show-version:
	@echo $(VERSION)

forcetag: checkversion
	hg tag -f product-definition-$(VERSION)
tag: checkversion
	hg tag product-definition-$(VERSION)

clean: clean-subdirs default-clean
	@rm -rf $(DISTDIR).tar.bz2

include Make.rules
include Make.defs
 
# vim: set sts=8 sw=8 noexpandtab :
