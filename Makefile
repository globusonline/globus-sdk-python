VIRTUALENV=.venv

.PHONY: docs build upload test test/opts test/no-opts clean help


help:
	@echo "These are our make targets and what they do."
	@echo "All unlisted targets are internal."
	@echo ""
	@echo "  help:         Show this helptext"
	@echo "  localdev:     Setup local development env with a 'setup.py develop'"
	@echo "  build:        Create the distributions which we like to upload to pypi"
	@echo "  test:         Run the full suite of tests"
	@echo "  test/opts:    Run the full suite of tests with optional dependencies installed"
	@echo "  test/no-opts: Run the full suite of tests with optional dependencies explicitly uninstalled"
	@echo "  docs:         Clean old HTML docs and rebuild them with sphinx"
	@echo "  upload:       [build], but also upload to pypi using twine"
	@echo "  clean:        Remove typically unwanted files, mostly from [build]"
	@echo "  all:          Wrapper for [localdev] + [docs] + [test]"


all: localdev docs test
localdev: $(VIRTUALENV)


$(VIRTUALENV): setup.py
	virtualenv $(VIRTUALENV)
	$(VIRTUALENV)/bin/python setup.py develop
	# explicit touch to ensure good update time relative to setup.py
	touch $(VIRTUALENV)


build: $(VIRTUALENV)
	$(VIRTUALENV)/bin/python setup.py sdist bdist_egg

$(VIRTUALENV)/bin/twine: $(VIRTUALENV)
	$(VIRTUALENV)/bin/pip install twine==1.6.5
upload: $(VIRTUALENV)/bin/twine build
	$(VIRTUALENV)/bin/twine upload dist/*

$(VIRTUALENV)/bin/flake8 $(VIRTUALENV)/bin/nose2: test-requirements.txt $(VIRTUALENV)
	$(VIRTUALENV)/bin/pip install -r test-requirements.txt
	# explicitly touch these files, otherwise we can have a weird thing happen
	# where test-requirements is newer than the binaries, but the pip install
	# command sees that they exist and does not update their mtime
	touch $(VIRTUALENV)/bin/flake8
	touch $(VIRTUALENV)/bin/nose2
opt-dependencies: $(VIRTUALENV)
	# don't specify version -- grab the latest!
	$(VIRTUALENV)/bin/pip install python-jose
remove-opt-dependencies: $(VIRTUALENV)
	-$(VIRTUALENV)/bin/pip uninstall -y python-jose

test: $(VIRTUALENV)/bin/flake8 $(VIRTUALENV)/bin/nose2
	$(VIRTUALENV)/bin/flake8
	$(VIRTUALENV)/bin/nose2 --verbose
test/opts: opt-dependencies
	$(MAKE) test
test/no-opts: remove-opt-dependencies
	$(MAKE) test



$(VIRTUALENV)/bin/sphinx-build: $(VIRTUALENV)
	$(VIRTUALENV)/bin/pip install sphinx==1.4.1
# docs needs full install because sphinx will actually try to do
# imports! Otherwise, we'll be missing dependencies like `requests`
docs: $(VIRTUALENV) $(VIRTUALENV)/bin/sphinx-build
	-rm -r docs
	mkdir docs
	touch docs/.nojekyll
	. $(VIRTUALENV)/bin/activate && $(MAKE) -C docs-source/ html


clean:
	-rm -r $(VIRTUALENV)
	-rm -r dist
	-rm -r build
	-rm -r *.egg-info
