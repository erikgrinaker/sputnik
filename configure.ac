dnl
dnl configure.ac
dnl
dnl $Id: configure.ac 99 2006-05-11 16:58:27Z erikg $
dnl

dnl initialize autoconf/automake
AC_PREREQ(2.53)
AC_INIT(src/sputnik.in)
AM_INIT_AUTOMAKE(sputnik, 0.0.3)


dnl check for dependencies
SPT_PYTHON_PATH(2.3)
SPT_PYGTK()
SPT_GCONF()
SPT_FDO_MIME()

SPT_PYTHON_MODULE(gnome)
SPT_PYTHON_MODULE(gtk)
SPT_PYTHON_MODULE(gst)


dnl output files
AC_OUTPUT([
	Makefile
	data/Makefile
	data/gconf/Makefile
	data/icons/Makefile
	data/icons/16x16/Makefile
	data/icons/24x24/Makefile
	data/icons/32x32/Makefile
	data/icons/48x48/Makefile
	data/mime/Makefile
	data/ui/Makefile
	src/Makefile
	src/lib/Makefile
])

