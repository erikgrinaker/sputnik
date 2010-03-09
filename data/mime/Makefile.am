## Process this file with automake to produce Makefile.in
#
# data/mime/Makefile.am
#
# $Id$
#

desktopdir		= $(datadir)/applications
desktop_DATA		= sputnik.desktop
EXTRA_DIST		= sputnik.desktop.in
CLEANFILES		= sputnik.desktop


sputnik.desktop: sputnik.desktop.in
	sed \
		-e "s|\@VERSION\@|$(VERSION)|" \
		sputnik.desktop.in > sputnik.desktop


install-data-hook:
if HAVE_FDO_DESKTOP
	$(UPDATE_DESKTOP_DATABASE)
endif

