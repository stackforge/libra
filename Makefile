PYTHON=`which python`
DESTDIR=/
BUILDIR=$(CURDIR)/debian/libra
PROJECT=libra
VERSION=1.0

all:
	@echo "make docs - Create documentation"
	@echo "make pdf_docs - Create PDF documentation"
	@echo "make builddeb - Generate a deb package"
	@echo "make clean - Get rid of scratch and byte files"

docs:
	$(PYTHON) setup.py build_sphinx $(COMPILE)

pdf_docs:
	$(PYTHON) setup.py build_sphinx_latex $(COMPILE)
	# Fix option double dashes in latex output
	sed -i -r 's/\\bfcode\{--(.*)\}/\\bfcode\{-{-\1\}/' build/sphinx/latex/*.tex
	sed -i -r 's/\\index\{(.*)--(.*)\}/\\index\{\1-{-\2\}/' build/sphinx/latex/*.tex
	make -C build/sphinx/latex all-pdf
	

builddeb:
	# build the package
	dpkg-buildpackage -i -I -rfakeroot

clean:
	$(PYTHON) setup.py clean
	rm -rf build/ MANIFEST
	find . -name '*.pyc' -delete
