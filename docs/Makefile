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
	@find "$(BUILDDIR)" \
		-type f \
		-not -path '.' \
		-not -path "./$(SOURCEDIR)" \
		-not -path './$(SOURCEDIR)/*' \
	        -not -path "./Makefile" \
		-execdir /bin/rm '{}' + >/dev/null 2>&1 || true
	@find "$(BUILDDIR)" \
		-type d \
		-not -path '.' \
		-not -path "./$(SOURCEDIR)" \
		-not -path './$(SOURCEDIR)/*' \
	        -not -path "./Makefile" \
		-execdir /bin/rm -r '{}' + >/dev/null 2>&1 || true
	@echo "Removed files."

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
