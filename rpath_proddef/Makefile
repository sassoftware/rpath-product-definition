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


python_files =	$(wildcard *.py)

dist_files = Makefile proddef_constants.py.in $(python_files)

all: default-all proddef_constants.py

proddef_constants.py: proddef_constants.py.in ../Makefile ../Make.defs Makefile
	sed -e s,@version@,$(VERSION),g \
	$< > $@

install: all pyfiles-install default-install install-generate
	install proddef_constants.py $(DESTDIR)$(pydir)/proddef_constants.py
	$(PYTHON) -c "import compileall; compileall.compile_dir('$(DESTDIR)$(pydir)', ddir='$(pydir)', quiet=1)"
	$(PYTHON) -OO -c "import compileall; compileall.compile_dir('$(DESTDIR)$(pydir)', ddir='$(pydir)', quiet=1)"

dist: default-dist

clean: default-clean
	rm -f proddef_constants.py

GENERATE_DS=~/hg/generateDS/generateDS.py
GENERATE_DS_ROOT=$(shell dirname $(GENERATE_DS))
xmlDir = $(subst .,_,$(patsubst rule-%,xml_%,$(1)))
xmlVer = $(patsubst rule-%,%,$(1))

generate: $(patsubst ../xsd/rpd-%.xsd,rule-%,$(wildcard ../xsd/rpd-*.xsd))

rule-%:
	mkdir -p $(call xmlDir,$@)
	touch $(call xmlDir,$@)/__init__.py
	cp generatedssuper.py $(call xmlDir,$@)/
	$(GENERATE_DS) -f --silence \
                --no-dates \
                --no-versions \
                --member-specs=list \
                --super=supers \
                --external-encoding=utf-8 \
                -o $(call xmlDir,$@)/supers.py \
                -s $(call xmlDir,$@)/subs.py \
                --user-methods=gends_user_methods \
                ../xsd/rpd-$(call xmlVer,$@).xsd
	$(GENERATE_DS) --version > gends_version.txt
	[ -x /usr/bin/hg ] && [ -d "$(GENERATE_DS_ROOT)/.hg" ] \
		&& ( echo -n "HG: "; hg -R "$(GENERATE_DS_ROOT)" parents --template "{node}\n"; ) \
			>> gends_version.txt \
		|| true

install-generate: $(addprefix install-rule-,$(wildcard xml_*))

install-rule-%: %
	install -d $(DESTDIR)$(pydir)$<
	install $</*.py $(DESTDIR)$(pydir)$</

include ../Make.rules
include ../Make.defs
