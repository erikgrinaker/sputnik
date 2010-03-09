## Process this file with automake to produce Makefile.in
#
# src/lib/Makefile.am
#
# $Id: Makefile.am 89 2006-05-10 07:55:32Z erikg $
#

libsputnikdir			= $(pyexecdir)/sputnik
libsputnik_PYTHON		= __init__.py \
				  dialog.py \
				  io.py \
				  media.py \
				  ui.py \
				  util.py

nodist_libsputnik_PYTHON	= config.py
CLEANFILES			= config.py
EXTRA_DIST			= config.py.in


config.py: config.py.in
	sed \
		-e "s|\@GCONFTOOL\@|$(GCONFTOOL)|" \
		-e "s|\@VERSION\@|$(VERSION)|" \
		-e "s|\@pkgdatadir\@|$(pkgdatadir)|" \
		-e "s|\@pkgschemadir\@|@GCONF_SCHEMA_FILE_DIR@|" \
		config.py.in > config.py

