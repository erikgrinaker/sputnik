#
# Sputnik - an internet radio player
# http://oss.codepoet.no/sputnik/
# $Id: ui.py 97 2006-05-11 16:41:40Z erikg $
#
# ui.py - module with UI widgets etc
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

import io, util
import gnome, gnome.ui, gobject, gtk, pango, re, xml.dom.minidom

from xml.parsers.expat import ExpatError


STOCK_CONTINUE		= "sputnik-continue"
STOCK_STATION		= "sputnik-station"
STOCK_PLAYING		= "sputnik-playing"
STOCK_VOLUME_OFF	= "sputnik-volume-off"
STOCK_VOLUME_MIN	= "sputnik-volume-min"
STOCK_VOLUME_MED	= "sputnik-volume-med"
STOCK_VOLUME_MAX	= "sputnik-volume-max"
STOCK_WARNING		= "sputnik-warning"

STOCKITEMS = (
	( STOCK_STATION,	"Play Station",	"stock_channel" ),
	( STOCK_CONTINUE,	"_Continue",	"stock_test-mode" ),
	( STOCK_PLAYING,	"",		"stock_effects-sound" ),
	( STOCK_VOLUME_OFF,	"",		"stock_volume-0" ),
	( STOCK_VOLUME_MIN,	"",		"stock_volume-min" ),
	( STOCK_VOLUME_MED,	"",		"stock_volume-med" ),
	( STOCK_VOLUME_MAX,	"",		"stock_volume-max" ),
	( STOCK_WARNING,	"",		"stock_dialog-warning" ),
)


ICON_SIZE_DIALOG	= gtk.ICON_SIZE_DIALOG
ICON_SIZE_LABEL		= gtk.ICON_SIZE_MENU



##### CONTAINERS #####

class Alignment(gtk.Alignment):
	"An alignment container"

	def __init__(self, widget = None, xalign = 0.5, yalign = 0.5, xscale = 0.0, yscale = 0.0):
		gtk.Alignment.__init__(self, xalign, yalign, xscale, yscale)

		if widget != None:
			self.add(widget)



class AppWindow(gtk.Window):
	"An application window"

	def __init__(self, title = None):
		gtk.Window.__init__(self)
		gtk.Window.set_title(self, title and title or "")

		self.apptitle	= title
		self.menubar	= None
		self.tooltips	= Tooltips()
		self.uimanager	= UIManager()

		self.add_accel_group(self.uimanager.get_accel_group())

		# set up outer box
		self.outerbox = VBox()
		self.outerbox.set_spacing(0)
		self.add(self.outerbox)

		# set up contents
		self.contents = VBox()
		self.contents.set_border_width(6)
		self.contents.set_spacing(12)
		self.outerbox.pack_start(self.contents)


	def set_menubar(self, menubar):
		"Sets up the window menubar"

		if self.menubar != None:
			self.menubar.destroy()
			self.menubar = None

		if menubar == None:
			return

		self.menubar = menubar

		self.outerbox.pack_start(self.menubar, False, False)
		self.outerbox.reorder_child(self.menubar, 0)


	def set_title(self, title):
		"Sets the window title"

		if title and self.apptitle:
			title = "%s - %s" % ( title, self.apptitle )

		elif self.title:
			title = self.apptitle

		if title == None:
			title = ""

		gtk.Window.set_title(self, title)



class EventBox(gtk.EventBox):
	"A container which handles events for a widget (for tooltips etc)"

	def __init__(self, widget = None):
		gtk.EventBox.__init__(self)

		self.widget = widget

		if widget is not None:
			self.add(self.widget)



class Expander(gtk.Expander):
	"A container that hides its child widget"

	def __init__(self, title = None, child = None):
		gtk.Expander.__init__(self, title != None and "<b>%s</b>" % util.escape_markup(title) or None)

		self.set_use_markup(True)

		self.alignment = Alignment(child, 0.5, 0.5, 1, 1)
		self.alignment.set_padding(0, 0, 12, 0)
		gtk.Expander.add(self, self.alignment)

		if child != None:
			self.add(child)


	def add(self, widget):
		"Adds a child to the widget"

		if widget is self.alignment:
			return

		self.alignment.add(widget)



class Frame(gtk.Frame):
	"A frame"

	def __init__(self, widget = None, label = None):
		gtk.Frame.__init__(self, label)

		if widget is not None:
			self.add(widget)



class HBox(gtk.HBox):
	"A horizontal container"

	def __init__(self, *args):
		gtk.HBox.__init__(self)

		self.set_spacing(6)
		self.set_border_width(0)

		for widget in args:
			self.pack_start(widget)


	def add_space(self, expand = False):
		"Adds a space to the box"

		l = Label("")
		l.set_size_request(self.get_spacing(), -1)

		self.pack_start(l, expand, expand)



class VBox(gtk.VBox):
	"A vertical container"

	def __init__(self, *args):
		gtk.VBox.__init__(self)

		self.set_spacing(6)
		self.set_border_width(0)

		for widget in args:
			self.pack_start(widget)



class HButtonBox(HBox):
	"A horizontal button box"

	def __init__(self, *args):
		HBox.__init__(self)

		self.set_homogeneous(True)
		self.set_spacing(6)

		for button in args:
			self.pack_start(button, True, True, 0)



class VButtonBox(gtk.VButtonBox):
	"A horizontal button box"

	def __init__(self, *args):
		gtk.VButtonBox.__init__(self)

		for button in args:
			self.pack_start(button)



class InputSection(VBox):
	"A section of input fields"

	def __init__(self, title = None, description = None, sizegroup = None):
		VBox.__init__(self)

		self.title	= None
		self.desc	= None
		self.sizegroup	= sizegroup

		if title is not None:
			self.title = Label("<span weight=\"bold\">%s</span>" % util.escape_markup(title))
			self.pack_start(self.title, False)

		if description is not None:
			self.desc = Label(util.escape_markup(description))
			self.pack_start(self.desc, False)

		if sizegroup is None:
			self.sizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)


	def append_widget(self, widget, title = None, indent = True, expand = False):
		"Adds a widget to the section"

		row = HBox()
		row.set_spacing(12)
		self.pack_start(row, expand, expand)

		if self.title is not None and indent == True:
			row.pack_start(Label(""), False, False)

		if title is not None:
			label = Label("%s:" % util.escape_markup(title))
			self.sizegroup.add_widget(label)
			row.pack_start(label, False, False)

		row.pack_start(widget)


	def clear(self):
		"Removes all widgets"

		for child in self.get_children():
			if child not in ( self.title, self.desc ):
				child.destroy()



class ScrolledWindow(gtk.ScrolledWindow):
	"A scrolled window for partially displaying a child widget"

	def __init__(self, contents = None):
		gtk.ScrolledWindow.__init__(self)

		self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.set_shadow_type(gtk.SHADOW_IN)

		if contents != None:
			self.add(contents)



class Popup(gtk.Window):
	"A popup window"

	def __init__(self, widget = None):
		gtk.Window.__init__(self, gtk.WINDOW_POPUP)

		self.borderframe = Frame()
		self.borderframe.set_shadow_type(gtk.SHADOW_OUT)
		gtk.Window.add(self, self.borderframe)


	def __cb_grab_buttonpress(self, widget, data = None):
		"Callback for button presses while input is grabbed"

		self.ungrab_input()
		self.destroy()


	def add(self, widget):
		"Adds a widget to the popup"

		self.borderframe.add(widget)


	def grab_input(self):
		"Grabs input from whole screen, destroys popup on click outside"

		self.grab_focus()
		self.grab_add()

		grabbed = gtk.gdk.pointer_grab(self.window, True, gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK, None, None, 0)

		if grabbed == gtk.gdk.GRAB_SUCCESS:
			grabbed = gtk.gdk.keyboard_grab(self.window, True, 0)

			if grabbed == gtk.gdk.GRAB_SUCCESS:
				self.connect("button-press-event", self.__cb_grab_buttonpress)
				return

			self.grab_remove()
			self.destroy()

		self.grab_remove()
		self.destroy()


	def show(self, x = None, y = None, w = None, h = None):
		"Shows the popup"

		if x != None and y != None:
			self.move(x, y)

		if w != None and h != None:
			self.set_size_request(w, h)

		self.show_all()


	def ungrab_input(self):
		"Ungrabs input from screen"

		self.grab_remove()
		gtk.gdk.pointer_ungrab()
		gtk.gdk.keyboard_ungrab()



##### WIDGETS #####

class Image(gtk.Image):
	"A widget for displaying an image"

	def __init__(self, stock = None, size = gtk.ICON_SIZE_BUTTON):
		gtk.Image.__init__(self)

		if stock != None:
			self.set_from_stock(stock, size)


	def set_from_stock(self, stock, size):
		"Sets the stock image"

		if ( stock, size ) == self.get_stock():
			return

		gtk.Image.set_from_stock(self, stock, size)



class ImageLabel(HBox):
	"A label with an image"

	def __init__(self, text = None, stock = None, size = ICON_SIZE_LABEL):
		HBox.__init__(self)

		self.image = Image()
		self.pack_start(self.image, False, False)

		self.label = Label("", gtk.JUSTIFY_LEFT)
		self.pack_start(self.label)

		if text != None:
			self.set_text(text)

		if stock != None:
			self.set_stock(stock, size)


	def get_stock(self):
		"Returns the stock image"

		return self.image.get_stock()[0]


	def get_text(self):
		"Returns the text"

		return self.label.get_text()


	def set_stock(self, stock, size = ICON_SIZE_LABEL):
		"Sets the image"

		if stock == None:
			self.image.clear()

		else:
			self.image.set_from_stock(stock, size)


	def set_text(self, text):
		"Sets the label text"

		self.label.set_text(text)



class ImageMenuItem(gtk.ImageMenuItem):
	"A menuitem with a stock icon"

	def __init__(self, stock, text = None, callback = None):
		gtk.ImageMenuItem.__init__(self, stock)

		self.label = self.get_children()[0]
		self.image = self.get_children()[1]

		if text is not None:
			self.set_text(text)

		if callback is not None:
			self.connect("activate", callback)


	def set_stock(self, stock):
		"Set the stock item to use as icon"

		self.image.set_from_stock(stock, gtk.ICON_SIZE_MENU)


	def set_text(self, text):
		"Set the item text"

		self.label.set_text(text)



class Label(gtk.Label):
	"A text label"

	def __init__(self, text = None, justify = gtk.JUSTIFY_LEFT):
		gtk.Label.__init__(self)

		self.set_text(text)
		self.set_justify(justify)
		self.set_use_markup(True)
		self.set_line_wrap(True)

		if justify == gtk.JUSTIFY_LEFT:
			self.set_alignment(0, 0.5)

		elif justify == gtk.JUSTIFY_CENTER:
			self.set_alignment(0.5, 0.5)

		elif justify == gtk.JUSTIFY_RIGHT:
			self.set_alignment(1, 0.5)


	def set_text(self, text):
		"Sets the text of the label"

		if text == None:
			gtk.Label.set_text(self, "")

		else:
			gtk.Label.set_markup(self, text)


class Menu(gtk.Menu):
	"A menu"

	def __init__(self):
		gtk.Menu.__init__(self)


	def popup(self, button, time):
		"Pops up the menu"

		self.show_all()
		gtk.Menu.popup(self, None, None, None, button, time)



class TextView(gtk.TextView):
	"A text view"

	def __init__(self, buffer = None, text = None):
		gtk.TextView.__init__(self, buffer)

		self.set_editable(False)
		self.set_wrap_mode(gtk.WRAP_NONE)
		self.set_cursor_visible(False)
		self.modify_font(pango.FontDescription("Monospace"))

		if text is not None:
			self.get_buffer().set_text(text)



class TreeView(gtk.TreeView):
	"A tree view"

	def __init__(self, model = None):

		if model == None:
			gtk.TreeView.__init__(self)

		else:
			gtk.TreeView.__init__(self, model)

		self.set_headers_visible(False)
		self.model = model

		self.selection = self.get_selection()
		self.selection.set_mode(gtk.SELECTION_SINGLE)

		self.connect("button_press_event", self.__cb_buttonpress)


	def __cb_buttonpress(self, widget, data):
		"Callback for handling mouse clicks"

		path = self.get_path_at_pos(int(data.x), int(data.y))

		# handle click outside entry
		if path is None:
			self.unselect_all()

		# handle doubleclick
		if data.button == 1 and data.type == gtk.gdk._2BUTTON_PRESS and path != None:
			iter = self.model.get_iter(path[0])
			self.emit("doubleclick", iter)

		# display popup on right-click
		elif data.button == 3:
			if path != None and self.selection.iter_is_selected(self.model.get_iter(path[0])) == False:
				self.set_cursor(path[0], path[1], False)

			self.emit("popup", data)

			return True


	def get_active(self):
		"Get the currently active row"

		if self.model == None:
			return None

		path, focus = self.get_cursor()

		if path == None:
			return None

		iter = self.model.get_iter(path)

		if iter is None or self.selection.iter_is_selected(iter) == False:
			return None

		return iter


	def get_selected(self):
		"Returns the currently selected iter"

		model, iter = self.selection.get_selected()

		return iter


	def select(self, iter):
		"Select a particular row"

		if iter == None:
			self.unselect_all()

		else:
			self.set_cursor(self.model.get_path(iter))


	def set_model(self, model):
		"Change the tree model which is being displayed"

		gtk.TreeView.set_model(self, model)
		self.model = model


	def unselect_all(self):
		"Unselect all rows in the tree"

		self.selection.unselect_all()
		self.selection.emit("changed")
		self.emit("cursor_changed")
		self.emit("unselect_all")


gobject.signal_new("doubleclick", TreeView, gobject.SIGNAL_ACTION, gobject.TYPE_BOOLEAN, (gobject.TYPE_PYOBJECT, ))
gobject.signal_new("popup", TreeView, gobject.SIGNAL_ACTION, gobject.TYPE_BOOLEAN, (gobject.TYPE_PYOBJECT, ))



class VolumeSlider(gtk.VScale):
	"A volume slider"

	def __init__(self, volume = 0):
		gtk.VScale.__init__(self)

		self.set_draw_value(False)
		self.set_inverted(True)
		self.set_size_request(-1, 100)

		self.adjustment = gtk.Adjustment(volume, 0, 1, 0.05, 0.1, 0)
		self.set_adjustment(self.adjustment)



##### ENTRIES #####

class Entry(gtk.Entry):
	"A normal text entry"

	def __init__(self, text = None):
		gtk.Entry.__init__(self)

		self.set_activates_default(True)
		self.set_text(text)


	def set_text(self, text):
		"Sets the entry contents"

		if text is None:
			text = ""

		gtk.Entry.set_text(self, text)



class ComboBoxEntry(gtk.ComboBoxEntry):
	"An entry with a dropdown list"

	def __init__(self, list = []):
		gtk.ComboBoxEntry.__init__(self)

		self.entry = self.child
		self.entry.set_activates_default(True)

		self.model = gtk.ListStore(gobject.TYPE_STRING)
		self.set_model(self.model)
		self.set_text_column(0)

		self.completion = gtk.EntryCompletion()
		self.completion.set_model(self.model)
		self.completion.set_text_column(0)
		self.completion.set_minimum_key_length(1)
		self.entry.set_completion(self.completion)


	def get_text(self):
		"Returns the text of the entry"

		return self.entry.get_text()


	def set_text(self, text):
		"Sets the text of the entry"

		if text is None:
			self.entry.set_text("")

		else:
			self.entry.set_text(text)


	def set_values(self, list):
		"Sets the values for the dropdown"

		self.model.clear()

		if list == None:
			return

		for item in list:
			self.model.append((item,))



##### BUTTONS #####

class Button(gtk.Button):
	"A normal button"

	def __init__(self, label, callback = None):
		gtk.Button.__init__(self, label)

		self.set_use_stock(True)

		if callback != None:
			self.connect("clicked", callback)



class ToggleButton(gtk.ToggleButton):
	"A toggle button"

	def __init__(self, label = None, callback = None):
		gtk.ToggleButton.__init__(self, label)

		self.set_use_stock(True)

		if callback != None:
			self.connect("toggled", callback)



class PlayButton(ToggleButton):
	"A play/stop button"

	def __init__(self):
		ToggleButton.__init__(self)

		self.add(Alignment(HBox(
			Image(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_LARGE_TOOLBAR),
			Image(gtk.STOCK_MEDIA_STOP, gtk.ICON_SIZE_LARGE_TOOLBAR),
		)))


class RecordButton(ToggleButton):
	"A record button"

	def __init__(self):
		ToggleButton.__init__(self)

		self.add(Image(gtk.STOCK_MEDIA_RECORD, gtk.ICON_SIZE_LARGE_TOOLBAR))



class VolumeButton(ToggleButton):
	"A volume button"

	def __init__(self, volume = 0):
		ToggleButton.__init__(self)

		self.volume	= 0
		self.popup	= None
		self.icon	= Image()
		self.add(self.icon)

		self.connect("scroll-event", self.__cb_scroll_event)
		self.connect("toggled", self.__cb_toggled)

		self.set_volume(volume)


	def __cb_slider_keypress(self, widget, event, data = None):
		"Callback for volume slider keypresses"

		key = gtk.gdk.keyval_name(event.keyval)

		if key == "Escape":
			self.popup.destroy()
			self.set_volume(data)

		elif key in ( "KP_Enter", "ISO_Enter", "Key_3270_Enter", "Return", "space", "KP_SPACE" ):
			self.popup.destroy()


	def __cb_scroll_event(self, widget, event, data = None):
		"Callback for scroll events"

		v = self.get_volume()

		if event.direction == gtk.gdk.SCROLL_UP:
			v += 0.1

		elif event.direction == gtk.gdk.SCROLL_DOWN:
			v -= 0.1

		self.set_volume(v)


	def __cb_toggled(self, widget, data = None):
		"Callback for toggle events"

		if self.get_active() == True:
			self.show_slider()

		elif self.popup != None:
			self.popup.destroy()


	def get_volume(self):
		"Gets the volume"

		return round(self.volume, 1)


	def set_volume(self, volume):
		"Sets the volume"

		volume = round(volume, 1)
		volume = min(volume, 1)
		volume = max(volume, 0)

		if volume == self.get_volume():
			return

		self.volume = volume

		# set icon
		if	volume <= 0 / 3.0:	stock = STOCK_VOLUME_OFF
		elif	volume <= 1 / 3.0:	stock = STOCK_VOLUME_MIN
		elif	volume <= 2 / 3.0:	stock = STOCK_VOLUME_MED
		else:				stock = STOCK_VOLUME_MAX

		self.icon.set_from_stock(stock, gtk.ICON_SIZE_LARGE_TOOLBAR)
		self.emit("volume-changed", self.get_volume())


	def show_slider(self):
		"Displays the volume slider"

		self.popup = Popup()
		self.popup.set_screen(self.get_screen())
		self.popup.connect("unrealize", lambda w: setattr(self, "popup", None))
		self.popup.connect("unrealize", lambda w: self.set_active(False))

		slider = VolumeSlider(self.get_volume())
		slider.connect("value-changed", lambda w: self.set_volume(slider.get_value()))
		slider.connect("key-press-event", self.__cb_slider_keypress, self.get_volume())

		vbox = gtk.VBox()
		vbox.pack_start(Label("+", gtk.JUSTIFY_CENTER), False, False)
		vbox.pack_start(slider)
		vbox.pack_start(Label("-", gtk.JUSTIFY_CENTER), False, False)
		self.popup.add(vbox)

		a = self.get_allocation()
		x, y = self.window.get_origin()
		self.popup.show(x + a.x, y + a.y + a.height, a.width, -1)
		self.popup.grab_input()


gobject.signal_new("volume-changed", VolumeButton, gobject.SIGNAL_ACTION, gobject.TYPE_NONE, (gobject.TYPE_FLOAT, ))



##### MISCELLANEOUS #####

class ItemFactory(gtk.IconFactory):
	"A stock item factory"

	def __init__(self, parent):
		gtk.IconFactory.__init__(self)

		self.parent	= parent
		self.theme	= gtk.icon_theme_get_default()

		self.add_default()

		for id, name, iconid in STOCKITEMS:
			self.create_stock_item(id, name, self.load_theme_iconset(iconid))


	def create_stock_item(self, id, name, iconset = None):
		"Creates a stock item"

		gtk.stock_add(((id, name, 0, 0, None), ))

		if iconset != None:
			self.add(id, iconset)


	def load_theme_iconset(self, id, sizes = [ gtk.ICON_SIZE_SMALL_TOOLBAR, gtk.ICON_SIZE_LARGE_TOOLBAR, gtk.ICON_SIZE_MENU, gtk.ICON_SIZE_BUTTON, gtk.ICON_SIZE_DIALOG ]):
		"Loads an iconset from the current theme"

		if self.theme.has_icon(id) == False:
			return None

		iconset = gtk.IconSet()

		for size in dict.fromkeys(sizes).keys():
			pixelsize = gtk.icon_size_lookup(size)[0]

			source = gtk.IconSource()
			source.set_size(size)
			source.set_size_wildcarded(False)

			try:
				pixbuf = self.theme.load_icon(id, pixelsize, 0)
				source.set_pixbuf(pixbuf)
				iconset.add_source(source)

			except gobject.GError:
				pass

		return iconset



class StationInfo(VBox):
	"Info about the current station"

	def __init__(self):
		VBox.__init__(self)
		self.set_spacing(12)

		self.tooltips = Tooltips()

		self._name	= ""
		self.track	= ""
		self.status	= ""
		self.statusicon	= None
		self.statustip	= ""

		self.vbox_top = VBox()
		self.vbox_top.set_spacing(1)
		self.eventbox_top = EventBox(self.vbox_top)
		self.pack_start(self.eventbox_top)

		self.label_name = Label("")
		self.label_name.set_selectable(True)
		self.label_name.set_ellipsize(pango.ELLIPSIZE_END)
		self.vbox_top.pack_start(self.label_name, False, False)

		self.label_status = ImageLabel()
		self.label_status.label.set_ellipsize(pango.ELLIPSIZE_END)
		self.label_status.label.set_line_wrap(False)
		self.eventbox_status = EventBox(self.label_status)
		self.pack_start(self.eventbox_status)

		self.set_name(" ")


	def __update_ui(self):
		"Updates the ui"

		if self._name + "\n" + self.track != self.label_name.get_text():
			self.label_name.set_text("<span size=\"large\"><b>%s</b></span>\n%s" % ( util.escape_markup(self._name), util.escape_markup(self.track) ))

			tip = ("%s\n%s" % ( self._name, self.track )).strip()
			self.tooltips.set_tip(self.eventbox_top, tip or None)

		if self.status != self.label_status.get_text():
			self.label_status.set_text(self.status)

		if self.statusicon != self.label_status.get_stock():
			self.label_status.set_stock(self.statusicon)

		if self.statustip != self.tooltips.get(self.eventbox_status):
			self.tooltips.set_tip(self.eventbox_status, self.statustip)


	def clear(self):
		"Clears the info"

		self._name	= ""
		self.track	= ""
		self.status	= ""
		self.statusicon	= None
		self.statustip	= ""

		self.__update_ui()


	def get_name(self):
		"Returns the name"

		return self._name


	def get_status(self):
		"Returns the status"

		return self.status


	def get_track(self):
		"Returns the track"

		return self.track


	def set_name(self, name):
		"Sets the name"

		if name == None:
			name = ""

		self._name = name
		self.__update_ui()


	def set_track(self, track):
		"Sets the track"

		if track == None:
			track = ""

		self.track = track
		self.__update_ui()


	def set_status(self, icon, text, tooltip = None):
		"Sets state info"

		if text == None:
			text = ""

		self.status	= text
		self.statusicon	= icon
		self.statustip	= tooltip

		self.__update_ui()



class StationList(TreeView):
	"A station list"

	def __init__(self, stationlist):
		TreeView.__init__(self)

		self.set_enable_search(False)
		self.set_rules_hint(True)
		self.set_fixed_height_mode(True)

		# set up list store
		self.liststore = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_PYOBJECT, gobject.TYPE_INT)
		self.liststore.set_sort_func(0, self.__cb_sort)
		self.liststore.set_sort_column_id(0, gtk.SORT_ASCENDING)

		self.set_stations(stationlist)

		# set up filter
		self.filtertext = ""

		self.filtermodel = self.liststore.filter_new()
		self.filtermodel.set_visible_func(self.__cb_filter)

		self.set_model(self.filtermodel)

		# set up column rendering
		self.cr = gtk.CellRendererText()
		self.cr.set_property("ellipsize", pango.ELLIPSIZE_END)
		self.cr.set_property("xpad", 6)
		self.cr.set_property("ypad", 6)
		self.cr.set_fixed_height_from_font(3)

		self.column = gtk.TreeViewColumn("Station", self.cr, markup = 0)
		self.column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		self.append_column(self.column)

		# set up signal handling
		self.connect("realize", self.__cb_realize)


	def __cb_filter(self, model, iter, data = None):
		"Callback for liststore filtering"

		if self.filtertext in ( None, "" ):
			return True

		text = model.get_value(iter, 0)

		if text != None and self.filtertext.lower() in text.lower():
			return True

		else:
			return False


	def __cb_realize(self, widget, data = None):
		"Callback for realize signals"

		if self.filtermodel.iter_n_children(None) > 0:
			self.select(self.filtermodel.iter_children(None))


	def __cb_sort(self, model, iter1, iter2, data = None):
		"Callback for liststore sorting"

		station1 = model.get(iter1, 1)[0]
		station2 = model.get(iter2, 1)[0]

		if station1 == None and station2 == None:
			return 0

		elif station1 == None:
			return 1

		elif station2 == None:
			return -1

		return cmp(station1.name.lower(), station2.name.lower())


	def filter(self, text):
		"Filters the list"

		self.filtertext = text
		self.filtermodel.refilter()

		try:
			self.select(self.filtermodel.get_iter("0"))

		except ValueError:
			self.unselect_all()


	def get_selected_index(self):
		"Returns the index of the currently selected station"

		iter = self.get_selected()

		if iter == None:
			return None

		return self.filtermodel.get_value(iter, 2)


	def get_selected_station(self):
		"Returns the currently selected station"

		iter = self.get_selected()

		if iter == None:
			return None

		return self.filtermodel.get_value(iter, 1)


	def set_stations(self, stationlist):
		"Sets the stations"

		self.liststore.clear()

		stations = stationlist.get_stations()

		for index, station in zip(range(len(stations)), stations):
			text = "<b>%s</b>\n%s\n%s" % ( util.escape_markup(station.name), util.escape_markup(station.description), util.escape_markup(station.website) )
			text = re.sub("\n+", "\n", text).strip()

			self.liststore.append([ text, station, index ])



class StreamList(TreeView):
	"A stream list"

	def __init__(self, streams = None):
		TreeView.__init__(self)

		self.set_enable_search(False)
		self.set_reorderable(True)
		self.set_rules_hint(True)

		self.liststore = gtk.ListStore(gobject.TYPE_STRING)
		self.set_model(self.liststore)

		self.cr = gtk.CellRendererText()
		self.cr.set_property("editable", True)
		self.cr.connect("edited", self.__cb_edited)

		self.column = gtk.TreeViewColumn("Stream", self.cr, markup = 0)
		self.append_column(self.column)

		if streams != None:
			self.set_streams(streams)


	def __cb_edited(self, cr, path, text, data = None):
		"Callback for cell edits"

		iter = self.liststore.get_iter(path)

		if iter == None:
			return

		self.liststore.set_value(iter, 0, text)


	def add_stream(self, stream):
		"Adds a stream to the list"

		return self.liststore.append([ stream ])


	def clear(self):
		"Clears the streamlist"

		self.liststore.clear()


	def get_streams(self):
		"Returns a list of streams"

		streams = []

		for i in range(self.liststore.iter_n_children(None)):
			iter = self.liststore.iter_nth_child(None, i)

			streams.append(self.liststore.get_value(iter, 0))

		return streams


	def remove_stream(self, iter):
		"Removes a stream"

		if iter == None:
			return

		self.liststore.remove(iter)


	def set_streams(self, streams):
		"Sets the stream list"

		self.liststore.clear()

		if type(streams) == list:
			for stream in streams:
				self.add_stream(stream)


class Tooltips(gtk.Tooltips):
	"A tooltip handler"

	def __init__(self):
		gtk.Tooltips.__init__(self)


	def get(self, widget):
		"Returns the tooltip for a widget"

		data = gtk.tooltips_data_get(widget)

		if data == None:
			return None

		return data[2]



class UIManager(gtk.UIManager):
	"UI item manager"

	def __init__(self):
		gtk.UIManager.__init__(self)


	def add_actions_from_file(self, file):
		"Sets up actions from an XML file"

		data = io.read(file)
		self.add_actions_from_string(data)


	def add_actions_from_string(self, string):
		"Sets up actions from an XML string"

		try:
			dom = xml.dom.minidom.parseString(string.strip())

		except ExpatError, reason:
			raise ValueError, reason

		if dom.documentElement.nodeName != "actions":
			raise ValueError


		# load action groups
		for groupnode in dom.documentElement.childNodes:

			if groupnode.nodeType != groupnode.ELEMENT_NODE:
				continue

			if groupnode.nodeName != "actiongroup":
				raise ValueError

			if not groupnode.attributes.has_key("name"):
				raise ValueError

			actiongroup = gtk.ActionGroup(groupnode.attributes["name"].nodeValue)


			# load actions
			for actionnode in groupnode.childNodes:

				if actionnode.nodeType != actionnode.ELEMENT_NODE:
					continue

				actiondata = {
					"name"		: "",
					"type"		: "normal",
					"label"		: "",
					"stock"		: "",
					"accel"		: None,
					"description"	: "",
					"important"	: False
				}

				if actionnode.attributes.has_key("type"):
					actiondata["type"] = actionnode.attributes["type"].nodeValue

				if actionnode.attributes.has_key("important"):
					actiondata["important"] = (actionnode.attributes["important"].nodeValue == "yes")

				for node in actionnode.childNodes:

					if node.nodeType != node.ELEMENT_NODE:
						continue

					elif actiondata.has_key(node.nodeName):
						actiondata[node.nodeName] = util.dom_text(node)

					else:
						raise ValueError

				if actiondata["name"] == "":
					raise ValueError

				if actiondata["type"] == "normal":
					action = gtk.Action(
						actiondata["name"], actiondata["label"],
						actiondata["description"], actiondata["stock"]
					)

				elif actiondata["type"] == "toggle":
					action = gtk.ToggleAction(
						actiondata["name"], actiondata["label"],
						actiondata["description"], actiondata["stock"]
					)

				else:
					raise ValueError

				action.set_property("is-important", actiondata["important"])
				actiongroup.add_action_with_accel(action, actiondata["accel"])


			self.append_action_group(actiongroup)


	def add_ui_from_file(self, file):
		"Loads ui from a file"

		try:
			gtk.UIManager.add_ui_from_file(self, file)

		except gobject.GError, reason:
			raise IOError, reason


	def append_action_group(self, actiongroup):
		"Appends an action group"

		gtk.UIManager.insert_action_group(self, actiongroup, len(self.get_action_groups()))


	def get_action(self, name):
		"Looks up an action in the managers actiongroups"

		for actiongroup in self.get_action_groups():
			action = actiongroup.get_action(name)

			if action != None:
				return action


	def get_action_group(self, name):
		"Returns the named action group"

		for actiongroup in self.get_action_groups():
			if actiongroup.get_name() == name:
				return actiongroup


##### FUNCTIONS #####

def update_ui():
	"Updates the UI"

	while gtk.events_pending() == True:
		gtk.main_iteration()

