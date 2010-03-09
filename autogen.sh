#!/bin/sh
#
# autogen.sh
# $Id: autogen.sh 2 2006-02-19 06:37:40Z erikg $
#
# Generates initial makefiles etc
#

: ${AUTOCONF=autoconf}
: ${AUTOMAKE=automake}
: ${ACLOCAL=aclocal}

srcdir=`dirname $0`
test -z "$srcdir" && srcdir="."

# avoid using caches
rm -rf autom4te.cache
rm -f aclocal.m4

# generates makefiles etc
echo "Running $ACLOCAL..."
WANT_AUTOMAKE="1.9" $ACLOCAL || exit 1
test -f aclocal.m4 || \
	{ echo "aclocal failed to generate aclocal.m4" 2>&1; exit 1; }

echo "Running $AUTOCONF..."
WANT_AUTOMAKE="1.9" $AUTOCONF || exit 1
test -f configure || \
	{ echo "autoconf failed to generate configure" 2>&1; exit 1; }

echo "Running $AUTOMAKE..."
WANT_AUTOMAKE="1.9" $AUTOMAKE || exit 1
test -f Makefile.in || \
	{ echo "automake failed to generate Makefile.in" 2>&1; exit 1; }

# clean up
rm -rf autom4te.cache

