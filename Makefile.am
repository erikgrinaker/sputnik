## Process this file with automake to produce Makefile.in
#
# Makefile.am
#
# $Id: Makefile.am 96 2006-05-11 16:19:52Z erikg $
#

AUTOMAKE_OPTIONS	= dist-bzip2 no-dist-gzip
SUBDIRS 		= data src

dist-hook:
	svn2cl.sh \
		--authors=$(top_srcdir)/authors.xml \
		--group-by-day \
		--separate-daylogs \
		--include-rev \
		--file=$(top_distdir)/ChangeLog \
		https://oss.codepoet.no/svn/sputnik/tags/$(PACKAGE)-$(VERSION)

