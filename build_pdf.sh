#!/bin/bash
python setup.py build_sphinx_latex
# Fix option double dashes in latex output
perl -i -pe 's/\\bfcode\{--(.*)\}/\\bfcode\{-\{\}-\1\}/g' build/sphinx/latex/*.tex
perl -i -pe 's/\\index\{(.*?)--(.*?)\}/\\index\{\1-\{\}-\2\}/g' build/sphinx/latex/*.tex
make -C build/sphinx/latex all-pdf
