## Process this file with automake to produce Makefile.in
#
# src/Makefile.am
#
# $Id: Makefile.am 89 2006-05-10 07:55:32Z erikg $
#

SUBDIRS			= lib
bin_SCRIPTS		= sputnik
EXTRA_DIST		= sputnik.in
CLEANFILES		= sputnik


sputnik: sputnik.in
	sed \
		-e "s|\@pyexecdir\@|$(pyexecdir)|" \
		sputnik.in > sputnik

