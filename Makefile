CWD    = $(CURDIR)
MODULE = $(notdir $(CWD))

NOW = $(shell date +%d%m%y)
REL = $(shell git rev-parse --short=4 HEAD)

PIP = $(CWD)/bin/pip3
PY  = $(CWD)/bin/python3



IP	 ?= 127.0.0.1
PORT ?= 19999

.PHONY: all py
all: py

py: $(PY) $(MODULE).py $(MODULE).ini
	IP=$(IP) PORT=$(PORT) $^



.PHONY: install
install: debian $(PIP)
	$(PIP) install    -r requirements.txt
	$(MAKE) requirements.txt

.PHONY: update
update: debian $(PIP)
	$(PIP) install -U    pip
	$(PIP) install -U -r requirements.txt
	$(MAKE) requirements.txt

$(PIP) $(PY):
	python3 -m venv .
	$(PIP) install -U pip pylint autopep8

.PHONY: requirements.txt
requirements.txt: $(PIP)
	$< freeze | grep -v 0.0.0 > $@

.PHONY: debian
debian:
	sudo apt update
	sudo apt install -u `cat apt.txt`



.PHONY: master shadow release zip

MERGE  = Makefile README.md .gitignore .vscode apt.txt requirements.txt
MERGE += $(MODULE).py $(MODULE).ini static templates

master:
	git checkout $@
	git checkout shadow -- $(MERGE)

shadow:
	git checkout $@

release:
	git tag $(NOW)-$(REL)
	git push -v && git push -v --tags
	git checkout shadow

zip:
	git archive --format zip --output $(MODULE)_src_$(NOW)_$(REL).zip HEAD
