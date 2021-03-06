AC_DEFUN([SPT_FDO_MIME], [
	AC_ARG_ENABLE(desktop-update, [AC_HELP_STRING(--disable-desktop-update, Disable the MIME desktop database update)], disable_desktop=yes, disable_desktop=no)
	AC_PATH_PROG(UPDATE_DESKTOP_DATABASE, update-desktop-database, no)
	AM_CONDITIONAL(HAVE_FDO_DESKTOP, test "x$UPDATE_DESKTOP_DATABASE" != "xno" -a "x$disable_desktop" = "xno")
])

AC_DEFUN([SPT_GCONF], [
	AC_PATH_PROG(GCONFTOOL, gconftool-2, no)

	if test "x$GCONFTOOL" = "xno"; then
		AC_MSG_ERROR(gconftool-2 not found in your path)
	fi

	AM_GCONF_SOURCE_2
])

AC_DEFUN([SPT_PYGTK], [
	PKG_CHECK_MODULES(PYGTK, [pygtk-2.0 >= 2.8.0])
	PKG_CHECK_MODULES(GNOME_PYTHON, [gnome-python-2.0 >= 2.10.0])
	PKG_CHECK_MODULES(GNOME_PYTHON_EXTRAS, [gnome-python-extras-2.0 >= 2.10.0])
])

AC_DEFUN([SPT_PYTHON_MODULE], [
	AC_MSG_CHECKING(python module $1)

	$PYTHON -c "import imp; imp.find_module('$1')" 2>/dev/null

	if test $? -eq 0; then
		AC_MSG_RESULT(yes)
		eval AS_TR_CPP(HAVE_PYMOD_$1)=yes
	else
		AC_MSG_RESULT(no)
		AC_MSG_ERROR(failed to find module $1)
		exit 1
	fi
])

AC_DEFUN([SPT_PYTHON_PATH], [
	AM_PATH_PYTHON($1)

	AC_MSG_CHECKING(Python include path)
	AC_ARG_WITH(python-include, [AC_HELP_STRING(--with-python-include=PATH, Path to Pyton include dir)], PYTHON_INCLUDE=$withval)

	if test -z "$PYTHON_INCLUDE" ; then
		PYTHON_INCLUDE=$PYTHON
		rvl_py_include_path=`echo $PYTHON_INCLUDE | sed -e "s/bin/include/"`
		rvl_py_version="`$PYTHON -c "import sys; print sys.version[[0:3]]"`";
		PYTHON_INCLUDE="$rvl_py_include_path$rvl_py_version"
	fi

	AC_MSG_RESULT($PYTHON_INCLUDE)
	AC_SUBST(PYTHON_INCLUDE)
])

