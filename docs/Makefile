# Minimal makefile for Sphinx documentation

.DEFAULT_TARGET: help

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXAPIDOC  = sphinx-apidoc
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = FeatureFactory
SOURCEDIR     = src
BUILDDIR      = .
PROJDIR       = ../src/featurefactory

.PHONY: help
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: clean
clean:
	@echo Not implemented
	@find "$(BUILDDIR)" \
		-not -path "./$(SOURCEDIR)" \
		-not -path './$(SOURCEDIR)/*' \
	        -not -path "./Makefile" \
		-execdir echo /bin/rm -r '{}' +
		#-print

.PHONY: html
html:
	@$(SPHINXAPIDOC) -o "$(SOURCEDIR)" "$(PROJDIR)"
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@rsync -a html/ ./
	@rm -r html
	@echo "Html files built to $(BUILDDIR)"

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
.PHONY: Makefile
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
