#
# Sputnik - an internet radio player
# http://oss.codepoet.no/sputnik/
# $Id: dialog.py 95 2006-05-11 15:56:30Z erikg $
#
# dialog.py - module with dialogs
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

import io, media, ui, util
import gobject, gtk, pango, urllib

gtk.rc_parse_string("""
	style "hig" { 
		GtkDialog::content-area-border	= 0
		GtkDialog::action-area-border	= 0
	}
	
	class "GtkDialog" style "hig"
""")



##### EXCEPTIONS #####

class CancelError(Exception):
	"Exception for dialog cancellations"
	pass



##### BASE DIALOGS #####

class Dialog(gtk.Dialog):
	"Base class for dialogs"

	def __init__(self, parent, title, buttons = (), default = None):
		gtk.Dialog.__init__(
			self, title, parent,
			gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR
		)

		self.set_border_width(12)
		self.vbox.set_spacing(12)
		self.set_resizable(False)
		self.set_modal(True)

		self.connect("key_press_event", self.__cb_keypress)
		self.connect("realize", self.__cb_realize)

		for stock, response in buttons:
			self.add_button(stock, response)

		if default != None:
			self.set_default_response(default)

		elif len(buttons) > 0:
			self.set_default_response(buttons[-1][1])


	def __cb_keypress(self, widget, data):
		"Callback for handling key presses"

		# close the dialog on escape
		if data.keyval == 65307:
			self.response(gtk.RESPONSE_CLOSE)


	def __cb_realize(self, widget, data = None):
		"Callback for widget realizations"

		self.action_area.set_spacing(6)


	def get_button(self, index):
		"Get one of the dialog buttons"

		buttons = self.action_area.get_children()

		if index < len(buttons):
			return buttons[index]


	def run(self):
		"Runs the dialog"

		self.show_all()

		while 1:
			response = gtk.Dialog.run(self)

			if response == gtk.RESPONSE_NONE:
				continue

			return response



class Message(Dialog):
	"A message dialog"

	def __init__(self, parent, title, text, stockimage, buttons = (), default = None):
		Dialog.__init__(self, parent, "", buttons, default)

		# hbox with image and contents
		hbox = ui.HBox()
		hbox.set_spacing(12)
		self.vbox.pack_start(hbox)
		self.vbox.set_spacing(24)

		# set up image
		if stockimage != None:
			image = ui.Image(stockimage, ui.ICON_SIZE_DIALOG)
			image.set_alignment(0.5, 0)
			hbox.pack_start(image, False, False)

		# set up message
		self.contents = ui.VBox()
		self.contents.set_spacing(10)
		hbox.pack_start(self.contents)

		label = ui.Label("<span size=\"larger\" weight=\"bold\">%s</span>\n\n%s" % ( util.escape_markup(title), text))
		label.set_alignment(0, 0)
		label.set_selectable(True)
		self.contents.pack_start(label)


	def run(self):
		"Displays the dialog"

		self.show_all()
		response = Dialog.run(self)
		self.destroy()

		return response



class Error(Message):
	"Displays an error message"

	def __init__(self, parent, title, text, buttons = ( ( gtk.STOCK_OK, gtk.RESPONSE_OK), ), default = None):
		Message.__init__(self, parent, title, text, gtk.STOCK_DIALOG_ERROR, buttons, default)



class Info(Message):
	"Displays an info message"

	def __init__(self, parent, title, text, buttons = ( ( gtk.STOCK_OK, gtk.RESPONSE_OK ), ), default = None):
		Message.__init__(self, parent, title, text, gtk.STOCK_DIALOG_INFO, buttons, default)



class Question(Message):
	"Displays a question"

	def __init__(self, parent, title, text, buttons = ( ( gtk.STOCK_OK, gtk.RESPONSE_OK ), ), default = None):
		Message.__init__(self, parent, title, text, gtk.STOCK_DIALOG_QUESTION, buttons, default)



class Warning(Message):
	"Displays a warning message"

	def __init__(self, parent, title, text, buttons = ( ( gtk.STOCK_OK, gtk.RESPONSE_OK ), ), default = None):
		Message.__init__(self, parent, title, text, ui.STOCK_WARNING, buttons, default)



class Utility(Dialog):
	"A utility dialog"

	def __init__(self, parent, title, buttons = ( ( gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE ), ), default = None):
		Dialog.__init__(self, parent, title, buttons, default)

		self.sectionvbox = ui.VBox()
		self.sectionvbox.set_spacing(18)
		self.vbox.pack_start(self.sectionvbox)

		self.sizegroup	= gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
		self.tooltips	= gtk.Tooltips()


	def add_section(self, title = None, description = None, expand = True):
		"Adds an input section to the dialog"

		section = ui.InputSection(title, description, self.sizegroup)
		self.sectionvbox.pack_start(section, expand, expand)

		return section



##### FILE SELECTORS #####

class FileSelector(gtk.FileChooserDialog):
	"A normal file selector"

	def __init__(self, parent, title = None, action = gtk.FILE_CHOOSER_ACTION_OPEN, stockbutton = None):

		if stockbutton is None:
			if action == gtk.FILE_CHOOSER_ACTION_OPEN:
				stockbutton = gtk.STOCK_OPEN

			elif action == gtk.FILE_CHOOSER_ACTION_SAVE:
				stockbutton = gtk.STOCK_SAVE

		gtk.FileChooserDialog.__init__(
			self, title, parent, action,
			( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, stockbutton, gtk.RESPONSE_OK )
		)

		self.set_local_only(False)
		self.set_default_response(gtk.RESPONSE_OK)
		self.set_do_overwrite_confirmation(True)

		self.inputsection = None


	def add_widget(self, title, widget):
		"Adds a widget to the file selection"

		if self.inputsection == None:
			self.inputsection = ui.InputSection()
			self.set_extra_widget(self.inputsection)

		self.inputsection.append_widget(title, widget)


	def get_filename(self):
		"Returns the file URI"

		uri = self.get_uri()

		if uri == None:
			return None

		else:
			return io.normpath(urllib.unquote(uri))


	def run(self):
		"Displays and runs the file selector, returns the filename"

		self.show_all()

		response = gtk.FileChooserDialog.run(self)
		filename = self.get_filename()
		self.destroy()

		if response == gtk.RESPONSE_OK:
			return filename

		else:
			raise CancelError



class OpenPlaylistFileSelector(FileSelector):
	"A file selector for opening playlists"

	def __init__(self, parent):
		FileSelector.__init__(self, parent, "Select Playlist to Open")

		filter = gtk.FileFilter()
		filter.set_name("Playlists")
		filter.add_mime_type("audio/x-scpls")
		filter.add_mime_type("audio/x-mpegurl")
		filter.add_mime_type("audio/x-ms-asx")
		filter.add_pattern("*.asx")
		self.add_filter(filter)

		filter = gtk.FileFilter()
		filter.set_name("All files")
		filter.add_pattern("*")
		self.add_filter(filter)


class SavePlaylistFileSelector(FileSelector):
	"A file selector for saving playlists"

	def __init__(self, parent, defaultfile = None):
		FileSelector.__init__(self, parent, "Select File to Save Playlist As", gtk.FILE_CHOOSER_ACTION_SAVE)

		if defaultfile != None:
			self.set_current_name(defaultfile)



##### STATION DIALOGS #####

class EditStation(Utility):
	"Dialog for adding a station"

	def __init__(self, parent, station):
		Utility.__init__(
			self, parent, "Edit Station",
			( ( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL ), ( gtk.STOCK_EDIT, gtk.RESPONSE_OK ) )
		)

		# set up meta section
		self.section_meta	= self.add_section("Station Info")

		self.entry_name		= ui.Entry()
		self.entry_name.set_width_chars(40)
		self.section_meta.append_widget(self.entry_name, "Name")

		self.entry_description	= ui.Entry()
		self.section_meta.append_widget(self.entry_description, "Description")

		self.entry_url		= ui.Entry()
		self.section_meta.append_widget(self.entry_url, "Website")


		# set up streams section
		expander = ui.Expander("Streams")
		self.sectionvbox.pack_start(expander)

		vbox = ui.VBox()
		expander.add(vbox)

		self.streamview = ui.StreamList(None)
		self.streamview.connect("key-press-event", self.__cb_stream_keypress)
		self.streamview.connect("popup", self.__cb_stream_popup)
		self.streamview.selection.connect("changed", self.__cb_stream_selection_changed)

		self.scrolledwindow = ui.ScrolledWindow(self.streamview)
		self.scrolledwindow.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		self.scrolledwindow.set_size_request(-1, 100)
		vbox.pack_start(self.scrolledwindow)

		self.button_add = ui.Button(gtk.STOCK_ADD, self.__cb_stream_add)
		self.button_edit = ui.Button(gtk.STOCK_EDIT, self.__cb_stream_edit)
		self.button_remove = ui.Button(gtk.STOCK_REMOVE, self.__cb_stream_remove)
		bb = ui.HButtonBox(self.button_add, self.button_edit, self.button_remove)
		vbox.pack_start(bb, False, False)

		self.streamview.select(None)

		if station != None:
			self.set_station(station)


	def __cb_stream_add(self, widget, data = None):
		"Callback for streamlist add button"

		iter = self.streamview.add_stream("New stream")
		path = self.streamview.liststore.get_path(iter)

		self.streamview.set_cursor_on_cell(path, self.streamview.column, self.streamview.cr, True)


	def __cb_stream_edit(self, widget, data = None):
		"Callback for streamlist edit button"

		iter = self.streamview.get_selected()

		if iter == None:
			return

		path = self.streamview.liststore.get_path(iter)
		self.streamview.set_cursor_on_cell(path, self.streamview.column, self.streamview.cr, True)


	def __cb_stream_keypress(self, widget, event):
		"Handles streamlist keypresses"

		key = gtk.gdk.keyval_name(event.keyval)

		if key == "Delete":
			iter = self.streamview.get_selected()

			if iter != None:
				self.streamview.liststore.remove(iter)


	def __cb_stream_popup(self, widget, event):
		"Displays a popup menu"

		iter = self.streamview.get_selected()

		if iter == None:
			return False

		menu = ui.Menu()
		menu.append(ui.ImageMenuItem(gtk.STOCK_EDIT, None, self.__cb_stream_edit))
		menu.append(ui.ImageMenuItem(gtk.STOCK_REMOVE, None, self.__cb_stream_remove))
		menu.popup(event.button, event.time)


	def __cb_stream_remove(self, widget, data = None):
		"Callback for streamlist remove button"

		self.streamview.remove_stream(self.streamview.get_selected())


	def __cb_stream_selection_changed(self, widget, data = None):
		"Callback for changed stream selection"

		if self.streamview.get_selected() == None:
			self.button_edit.set_sensitive(False)
			self.button_remove.set_sensitive(False)

		else:
			self.button_edit.set_sensitive(True)
			self.button_remove.set_sensitive(True)


	def get_station(self):
		"Fetches a station with the data"

		station			= media.Station()
		station.name		= self.entry_name.get_text()
		station.description	= self.entry_description.get_text()
		station.website		= self.entry_url.get_text()
		station.streams		= self.streamview.get_streams()

		return station


	def set_station(self, station):
		"Sets data from a station"

		if station == None:
			return

		self.entry_name.set_text(station.name)
		self.entry_description.set_text(station.description)
		self.entry_url.set_text(station.website)
		self.streamview.set_streams(station.streams)


	def run(self):
		"Runs the dialog"

		response = Utility.run(self)

		if response == gtk.RESPONSE_OK:
			station = self.get_station()
			self.destroy()

			return station

		else:
			self.destroy()
			raise CancelError



class AddStation(EditStation):
	"Dialog for adding a station"

	def __init__(self, parent, station = None):
		EditStation.__init__(self, parent, station)

		self.set_title("Add Station")
		self.get_button(0).set_label(gtk.STOCK_ADD)



class RemoveStation(Warning):
	"Dialog for removing a station"

	def __init__(self, parent, station):
		Warning.__init__(
			self, parent, "Really remove %s?" % station.name,
			"Are you sure you want to remove the station '%s' from the station list?" % util.escape_markup(station.name),
			( ( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL ), ( gtk.STOCK_REMOVE, gtk.RESPONSE_OK ) ),
			gtk.RESPONSE_CANCEL
		)


	def run(self):
		"Runs the dialog"

		if Warning.run(self) == gtk.RESPONSE_OK:
			return True

		else:
			raise CancelError



class OpenLocation(Utility):
	"Dialog for opening a location (URL)"

	def __init__(self, parent, list = None):
		Utility.__init__(
			self, parent, "Open Location",
			( ( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL ), ( gtk.STOCK_CONNECT, gtk.RESPONSE_OK ) )
		)

		# set up stream section
		self.sect_stream	= self.add_section()

		self.entry_stream	= ui.ComboBoxEntry()
		self.sect_stream.append_widget(self.entry_stream, "Location")

		# populate with config values
		self.entry_stream.set_values(list)


	def run(self):
		"Displays the dialog"

		resp	= Utility.run(self)
		url	= self.entry_stream.get_text()

		self.destroy()

		if resp != gtk.RESPONSE_OK or url in ( "", None ):
			raise CancelError

		return url



class StationList(Utility):
	"A dialog for selecting a station"

	def __init__(self, parent, stationlist, config = None):
		Utility.__init__(
			self, parent, "Play Station",
			( ( gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE ), ( gtk.STOCK_MEDIA_PLAY, gtk.RESPONSE_OK ) ),
		)

		self.config = config

		self.stationlist = stationlist
		self.stationlist.connect("changed", self.__cb_stationlist_changed)

		self.set_resizable(True)

		section = self.add_section()

		self.entry_search = ui.Entry()
		self.entry_search.connect("changed", lambda w: self.treeview.filter(self.entry_search.get_text()))
		section.append_widget(self.entry_search, "Search")

		vbox = ui.VBox()
		section.append_widget(vbox, expand = True)

		self.treeview = ui.StationList(self.stationlist)
		self.treeview.connect("doubleclick", lambda w,d: self.response(gtk.RESPONSE_OK))
		self.treeview.connect("key-press-event", self.__cb_tree_keypress)
		self.treeview.connect("popup", self.__cb_tree_popup)
		self.treeview.selection.connect("changed", self.__cb_tree_selection_changed)

		self.scrolledwindow = ui.ScrolledWindow(self.treeview)
		self.scrolledwindow.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		vbox.pack_start(self.scrolledwindow)


	def __cb_stationlist_changed(self, widget, data = None):
		"Callback for stationlist changes"

		self.treeview.set_stations(self.stationlist)


	def __cb_tree_edit(self, widget, data = None):
		"Callback for edit station"

		try:
			index = self.treeview.get_selected_index()
			station = self.treeview.get_selected_station()

			if station == None:
				return

			station = EditStation(self, station).run()
			self.stationlist.update_station(index, station)

		except CancelError:
			pass


	def __cb_tree_keypress(self, widget, event):
		"Callback for treeview key presses"

		key = gtk.gdk.keyval_name(event.keyval)

		if key in ( "KP_Enter", "ISO_Enter", "Key_3270_Enter", "Return", "space", "KP_SPACE" ):
			self.response(gtk.RESPONSE_OK)

		elif key == "Delete":
			index = self.treeview.get_selected_index()

			if index != None:
				self.stationlist.remove_station(index)


	def __cb_tree_popup(self, widget, event):
		"Displays a popup menu"

		iter = self.treeview.get_selected()

		if iter == None:
			return False

		menu = ui.Menu()
		menu.append(ui.ImageMenuItem(gtk.STOCK_EDIT, None, self.__cb_tree_edit))
		menu.append(ui.ImageMenuItem(gtk.STOCK_REMOVE, None, self.__cb_tree_remove))
		menu.popup(event.button, event.time)


	def __cb_tree_remove(self, widget, data = None):
		"Callback for remove station"

		try:
			index = self.treeview.get_selected_index()
			station = self.stationlist.get_station(index)

			if station == None:
				return

			if RemoveStation(self, station).run() == True:
				self.stationlist.remove_station(index)

		except CancelError:
			return


	def __cb_tree_selection_changed(self, widget, data = None):
		"Callback for treeview selection changes"

		if self.treeview.get_selected_station() == None:
			self.get_button(0).set_sensitive(False)

		else:
			self.get_button(0).set_sensitive(True)


	def run(self):
		"Runs the dialog"

		self.entry_search.grab_focus()

		if self.config != None:
			width = self.config.get("ui/window-stationlist-width")
			height = self.config.get("ui/window-stationlist-height")

			if 0 not in (width, height):
				self.set_default_size(width, height)


		while 1:
			response = Utility.run(self)

			if self.config != None:
				width, height = self.get_size()

				self.config.set("ui/window-stationlist-width", width)
				self.config.set("ui/window-stationlist-height", height)


			if response == gtk.RESPONSE_OK:
				station = self.treeview.get_selected_station()

				if station == None:
					continue

				self.destroy()

				return station

			else:
				self.destroy()
				raise CancelError



##### MISCELLANEOUS DIALOGS #####

class About(gtk.AboutDialog):
	"About dialog"

	def __init__(self, parent):
		gtk.AboutDialog.__init__(self)

		if isinstance(parent, gtk.Window):
			self.set_transient_for(parent)

	def run(self):
		"Runs the dialog"

		self.show_all()



class Exception(Error):
	"Displays a traceback for an unhandled exception"

	def __init__(self, parent, traceback):
		Error.__init__(
			self, parent, "Unknown error",
			"An unknown error occured. Please report the text below to the developers, along with what you were doing that may have caused the error. You may attempt to continue running the application, but it may behave unexpectedly.",
			( ( gtk.STOCK_QUIT, gtk.RESPONSE_CANCEL ), ( ui.STOCK_CONTINUE, gtk.RESPONSE_OK ) )
		)

		textview = ui.TextView(None, traceback)
		scrolledwindow = ui.ScrolledWindow(textview)
		scrolledwindow.set_size_request(-1, 120)

		self.contents.pack_start(scrolledwindow)


	def run(self):
		"Runs the dialog"

		return Error.run(self) == gtk.RESPONSE_OK

