#
# Sputnik - an internet radio player
# http://oss.codepoet.no/sputnik/
# $Id: util.py 91 2006-05-10 08:16:32Z erikg $
#
# util.py - utility functions
#
#
# Copyright (c) 2006 Erik Grinaker
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#

import math, os, re, StringIO, traceback


def dom_text(node):
	"Returns text content of a DOM node"

	text = ""

	for child in node.childNodes:
		if child.nodeType == node.TEXT_NODE:
			text += child.nodeValue.encode("utf-8")

	return text


def escape_markup(string):
	"Escapes a string so it can be placed in a markup string"

	if string == None:
		return None

	string = string.replace("&", "&amp;")
	string = string.replace("<", "&lt;")
	string = string.replace(">", "&gt;")

	return string


def execute(command):
	"Runs a command, returns its status code and output"

	p = os.popen(command, "r")
	output = p.read()
	status = p.close()

	if status is None:
		status = 0

	status = status >> 8

	return output, status


def format_time(secs):
	"Format a number of seconds as a time"

	hours	= math.floor(secs / 3600.0)
	mins	= math.floor(secs % 3600 / 60.0)
	secs	= secs % 60

	if hours > 0:
		return "%i:%02i:%02i" % ( hours, mins, secs )

	else:
		return "%i:%02i" % ( mins, secs )


def trace_exception(type, value, tb):
	"Returns an exception traceback as a string"

	trace = StringIO.StringIO()
	traceback.print_exception(type, value, tb, None, trace)

	return trace.getvalue()

