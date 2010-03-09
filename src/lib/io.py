#
# Sputnik - an internet radio player
# http://oss.codepoet.no/sputnik/
# $Id: io.py 93 2006-05-10 15:02:04Z erikg $
#
# Copyright (c) 2006 Erik Grinaker
#
# io.py - module for IO-related operations
#
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

import gnomevfs, os, re


def basename(file):
	"Returns the basename of a file"

	return os.path.basename(file)


def exists(file, fileonly = True):
	"Checks if a file exists"

	if file == None:
		return False

	try:
		info = gnomevfs.get_file_info(file)

		if fileonly == True and info.type != 1:
			return False

		return True

	except gnomevfs.Error:
		return False


def mimetype(file):
	"Detects the mimetype of a file"

	try:
		return gnomevfs.get_mime_type(normpath(file))

	except RuntimeError:
		return None


def normpath(file, filescheme = False):
	"Normalizes a file path"

	if file in ( None, "" ):
		return ""

	file = re.sub("^file:/{,2}", "", file)
	file = os.path.expanduser(file)

	if not url_valid(file) and file[0] != "/":
		file = os.path.abspath(file)

	file = str(gnomevfs.URI(file))

	if filescheme == False:
		file = re.sub("^file:/{,2}", "", file)

	return file


def read(file, bytes = None):
	"Reads data from a file"

	try:
		if file == None:
			raise IOError

		file = normpath(file)

		if bytes == None:
			return gnomevfs.read_entire_file(file)

		else:
			return gnomevfs.Handle(file).read(bytes)

	except gnomevfs.Error, reason:
		raise IOError, (file, reason)


def url_hostname(url):
	"Extracts the hostname from an URL"

	return re.sub("^[a-z]+://([^:/]+).*$", "\\1", url)


def url_valid(url):
	"Checks if an URL is valid"

	return re.match("^[a-z]+://\S+$", url, re.IGNORECASE) != None


def write(file, data):
	"Writes data to file"

	try:
		if file == None:
			raise IOError

		file = normpath(file)

		if data == None:
			data = ""

		if exists(file) == True:
			f = gnomevfs.open(file, gnomevfs.OPEN_WRITE)

		else:
			if os.access(os.path.dirname(file), os.F_OK) == False:
				os.makedirs(os.path.dirname(file))

			f = gnomevfs.create(file, gnomevfs.OPEN_WRITE)

		f.write(data)
		f.close()

	except gnomevfs.Error:
		raise IOError

