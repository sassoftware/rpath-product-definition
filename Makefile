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
 
export schemaversion = $(shell ls -1 xsd/rpd-*xsd | tail -1 | sed 's^xsd/rpd-^^;s^.xsd^^')

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
