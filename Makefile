CWD    = $(CURDIR)
MODULE = $(notdir $(CWD))

NOW = $(shell date +%d%m%y)
REL = $(shell git rev-parse --short=4 HEAD)

PIP = $(CWD)/bin/pip3
PY  = $(CWD)/bin/python3

WGET = wget -c --no-check-certificate



IP	 ?= 127.0.0.1
PORT ?= 19999

.PHONY: all py rust
all: py

py: $(PY) $(MODULE).py $(MODULE).ini
	IP=$(IP) PORT=$(PORT) $^

rust:
	IP=$(IP) PORT=$(PORT) RUST_LOG=debug cargo run


.PHONY: install
install: debian $(PIP) js
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

.PHONY: js
js: static/jquery.js static/darkly.css \
	static/bootstrap.css static/bootstrap.css.map static/bootstrap.js

JQUERY_VER = 3.4.1
static/jquery.js:
	$(WGET) -O $@ https://code.jquery.com/jquery-$(JQUERY_VER).min.js

BOOTSTRAP_VER = $(JQUERY_VER)
BOOTSTRAP_URL = https://stackpath.bootstrapcdn.com/bootstrap/$(BOOTSTRAP_VER)
static/darkly.css:
	$(WGET) -O $@ https://bootswatch.com/3/darkly/bootstrap.min.css
static/bootstrap.css:
	$(WGET) -O $@ $(BOOTSTRAP_URL)/css/bootstrap.min.css
static/bootstrap.css.map:
	$(WGET) -O $@ $(BOOTSTRAP_URL)/css/bootstrap.min.css.map
static/bootstrap.js:
	$(WGET) -O $@ $(BOOTSTRAP_URL)/js/bootstrap.min.js



.PHONY: master shadow release zip

MERGE  = Makefile README.md LICENSE
MERGE += .gitignore .vscode apt.txt requirements.txt
MERGE += $(MODULE).py $(MODULE).ini static templates
MERGE += Cargo.toml src

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
