#
# Sputnik - an internet radio player
# http://oss.codepoet.no/sputnik/
# $Id: media.py 93 2006-05-10 15:02:04Z erikg $
#
# media.py - module with media functionality
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

import util
import gobject, gst, gtk, math, re, xml.dom.minidom
from xml.parsers.expat import ExpatError


STATE_ERROR		= "error"
STATE_STOPPED		= "stopped"
STATE_CONNECTING	= "connecting"
STATE_BUFFERING		= "buffering"
STATE_PLAYING		= "playing"
STATE_RECORDING		= "recording"


class DataError(Exception):
	"Exception for data errors"
	pass

class PlayError(Exception):
	"Exception for playback errors"
	pass

class PluginError(Exception):
	"Exception for plugin errors"
	pass



class Pipeline(gst.Pipeline):
	"A media pipeline"

	def __init__(self):
		gst.Pipeline.__init__(self)

		self.bufferprobe	= None
		self.bus		= self.get_bus()
		self.uri		= None

		# set up pipeline elements
		self.converter		= self.__init_converter()
		self.decoder		= self.__init_decoder()
		self.queue		= self.__init_queue()
		self.sink		= self.__init_sink()
		self.source		= self.__init_source()
		self.volume		= self.__init_volume()

		# add elements to pipeline
		self.add(self.source)
		self.add(self.queue)
		self.add(self.decoder)
		self.add(self.converter)
		self.add(self.volume)
		self.add(self.sink)

		# link pipeline elements (decoder/converter will be linked later)
		self.source.link(self.queue)
		self.queue.link(self.decoder)

		self.converter.link(self.volume)
		self.volume.link(self.sink)


	def __init_converter(self):
		"Sets up the audio converter"

		converter = gst.element_factory_make("audioconvert", "converter")

		return converter


	def __init_decoder(self):
		"Sets up the decoder"

		decoder = gst.element_factory_make("decodebin", "decoder")
		decoder.connect("new-decoded-pad", self.__cb_decoder_newpad)
		decoder.connect("unknown-type", self.__cb_decoder_unknowntype)

		return decoder


	def __init_queue(self):
		"Sets up the queue"

		queue = gst.element_factory_make("queue", "queue")

		queue.set_property("max-size-buffers", 0)
		queue.set_property("max-size-time", 0)
		queue.set_property("max-size-bytes", 64 * 1024)
		queue.set_property("min-threshold-bytes", 32 * 1024)

		queue.connect("running", self.__cb_queue_running)
		self.bufferprobe = queue.get_pad("sink").add_buffer_probe(self.__cb_queue_buffer)

		return queue


	def __init_sink(self):
		"Sets up the sink"

		for plugin in "gconfaudiosink", "alsasink", "osssink":
			try:
				sink = gst.element_factory_make(plugin, "sink")
				break

			except gst.PluginNotFoundError:
				pass

		if sink == None:
			raise PluginError("Couldn't find gconfaudiosink, alsasink, or osssink gstreamer plugins")

		return sink


	def __init_source(self):
		"Sets up the source"

		for plugin in "gnomevfssrc", "neonhttpsrc":
			try:
				source = gst.element_factory_make(plugin, "source")
				break

			except gst.PluginNotFoundError:
				pass

		if source == None:
			raise PluginError("Couldn't find neonhttpsrc or gnomevfs gstreamer plugins")

		source.set_property("iradio-mode", True)
		source.connect("notify::iradio-name", self.__cb_source_iradio)
		source.connect("notify::iradio-genre", self.__cb_source_iradio)
		source.connect("notify::iradio-title", self.__cb_source_iradio)
		source.connect("notify::iradio-url", self.__cb_source_iradio)

		return source


	def __init_volume(self):
		"Sets up the volume controller"

		volume = gst.element_factory_make("volume", "volume")

		return volume


	def __cb_decoder_newpad(self, decodebin, pad, last, data = None):
		"Handles new pads on the decoder"

		try:
			sinkpad = self.converter.get_pad("sink")

			if sinkpad.is_linked() == True:
				return

			pad.link(sinkpad)

		except gst.LinkError, (error,):
			if error == gst.PAD_LINK_NOFORMAT:
				self.__bus_post_error("Unknown stream format")

			else:
				self.__bus_post_error("Unknown error while decoding stream")


	def __cb_decoder_unknowntype(self, pad, caps, data = None):
		"Handles unknown stream type"

		self.__bus_post_error("Unknown stream format")


	def __cb_queue_buffer(self, pad, buffer):
		"Callback for queue buffer changes"

		try:
			threshold	= self.queue.get_property("min-threshold-bytes")
			level		= self.queue.get_property("current-level-bytes")
			progress	= min(float(level) / threshold, 1)

		except ZeroDivisionError:
			progress	= 0

		self.__bus_post_custom(gst.MESSAGE_BUFFERING, { "buffer-fill" : progress })

		return True


	def __cb_queue_running(self, queue, data = None):
		"Callback for queue overruns"

		if self.bufferprobe == None:
			return

		probeid			= self.bufferprobe
		self.bufferprobe	= None

		queue.get_pad("sink").remove_buffer_probe(probeid)


	def __cb_source_iradio(self, source, property):
		"Callback for iradio metadata"

		taglist = {
			"iradio-name"	: source.get_property("iradio-name"),
			"iradio-genre"	: source.get_property("iradio-genre"),
			"iradio-title"	: source.get_property("iradio-title"),
			"iradio-url"	: source.get_property("iradio-url"),
		}

		self.__bus_post_taglist(taglist)


	def __bus_post_custom(self, messagetype, data):
		"Posts a custom message on the bus"

		struct = gst.Structure("custom")

		if data != None:
			for key, value in data.items():
				if value == None:
					value = ""

				struct[key] = value

		self.bus.post(gst.message_new_custom(messagetype, self, struct))


	def __bus_post_error(self, error):
		"Posts an error message on the bus"

		# create custom error message, as gst-python won't let us
		# make one with gst.message_new_error()
		self.__bus_post_custom(gst.MESSAGE_ERROR, { "error" : error })


	def __bus_post_taglist(self, tags):
		"Posts a taglist message on the bus"

		# create custom taglist, as gst-python has double-free issues
		# with gst.message_new_taglist()
		self.__bus_post_custom(gst.MESSAGE_TAG, tags)


	def get_duration(self):
		"Returns the current duration as seconds"

		try:
			duration, format = self.query_duration(gst.FORMAT_TIME)

			return int(duration / 1000000000)

		except gst.QueryError:
			return 0


	def get_position(self):
		"Returns the current position as seconds"

		try:
			position, format = self.query_position(gst.FORMAT_TIME)

			return int(position / 1000000000)

		except gst.QueryError:
			return 0


	def get_volume(self):
		"Returns the current volume"

		return self.volume.get_property("volume")


	def play(self, uri):
		"Plays an URI"

		self.uri = uri

		# set up bufferprobe
		if self.bufferprobe == None:
			self.bufferprobe = self.queue.get_pad("sink").add_buffer_probe(self.__cb_queue_buffer)

		# remove source pad from decoder, to avoid
		# possible decodebin bug (src0 name crash)
		pad = self.decoder.get_pad("src0")

		if pad != None:
			self.decoder.remove_pad(pad)

		# we need to set up the source again, due to bugs
		# in plugin iradio-handling
		self.source.set_state(gst.STATE_NULL)
		self.remove(self.source)
		del self.source

		self.source = self.__init_source()
		self.add(self.source)
		self.source.link(self.queue)

		try:
			self.source.set_property("location", uri)

		except TypeError:
			self.source.set_property("uri", uri)

		if self.set_state(gst.STATE_PLAYING) == gst.STATE_CHANGE_FAILURE:
			raise PlayError


	def set_volume(self, volume):
		"Sets the volume"

		volume = min(volume, 1)
		volume = max(volume, 0)

		self.volume.set_property("volume", volume)


	def stop(self):
		"Stops playback"

		self.set_state(gst.STATE_NULL)



class Player(gobject.GObject):
	"Player for radio streams"

	__gsignals__ = {
		"meta-changed"	: ( gobject.SIGNAL_ACTION, gobject.TYPE_NONE, ( gobject.TYPE_PYOBJECT, )),
		"state-changed"	: ( gobject.SIGNAL_ACTION, gobject.TYPE_NONE, ( gobject.TYPE_STRING, gobject.TYPE_PYOBJECT )),
	}

	def __init__(self):
		gobject.GObject.__init__(self)

		self.state		= STATE_STOPPED

		self.meta		= {
			"name"			: None,
			"description"		: None,
			"website"		: None,
			"playing"		: None,
			"format"		: None,
			"bitrate"		: None,
			"codec"			: None,
		}

		self.pipeline = Pipeline()
		self.pipeline.bus.add_watch(self.__cb_bus)


	def __cb_bus(self, bus, message, data = None):
		"Callback for bus messages"

		# handle tag lists from any source
		if message.type == gst.MESSAGE_TAG:
			return self.__cb_bus_taglist(message)

		# skip messages not from pipeline
		elif message.src != self.pipeline:
			return True

		# skip clock messages
		elif message.type in ( gst.MESSAGE_CLOCK_PROVIDE, gst.MESSAGE_CLOCK_LOST, gst.MESSAGE_NEW_CLOCK ):
			return True

		# handle state changes
		elif message.type == gst.MESSAGE_STATE_CHANGED:
			return self.__cb_bus_state_changed(message)

		# handle buffering
		elif message.type == gst.MESSAGE_BUFFERING:
			return self.__cb_bus_buffering(message)

		# handle end-of-stream
		elif message.type == gst.MESSAGE_EOS:
			return self.__cb_bus_eos(message)

		# handle errors
		elif message.type == gst.MESSAGE_ERROR:
			return self.__cb_bus_error(message)

		# warn about unhandled messages
		else:
			print "Unhandled gst message:", message, "of type", message.type

		return True


	def __cb_bus_buffering(self, message):
		"Callback for bus buffering messages"

		bufferfill = message.structure["buffer-fill"]

		if bufferfill == 1 or self.state == STATE_PLAYING:
			return True

		self.__set_state(STATE_BUFFERING, bufferfill)

		return True


	def __cb_bus_eos(self, message):
		"Callback for bus end-of-stream messages"

		self.pipeline.set_state(gst.STATE_NULL)
		self.__set_state(STATE_STOPPED)

		return True


	def __cb_bus_error(self, message):
		"Callback for error messages"

		self.__set_error(message.structure["error"])

		return True


	def __cb_bus_state_changed(self, message):
		"Callback for bus state changed messages"

		newstate = message.structure["new-state"]
		oldstate = message.structure["old-state"]
		state	= self.state

		if newstate == gst.STATE_NULL:
			if self.state not in ( STATE_STOPPED, STATE_ERROR ):
				state = STATE_STOPPED

		elif newstate in ( gst.STATE_READY, gst.STATE_PAUSED ):
			pass

		elif newstate == gst.STATE_PLAYING:
			state = STATE_PLAYING

		else:
			print "Uncaught state change:", oldstate, newstate

		self.__set_state(state)

		return True


	def __cb_bus_taglist(self, message):
		"Callback for tag lists"

		taglist = dict(message.structure)

		meta = {}

		# name
		if taglist.has_key("iradio-name"):
			meta["name"] = taglist["iradio-name"]

		# description
		if taglist.has_key("iradio-genre"):
			meta["description"] = taglist["iradio-genre"]

		# website
		if taglist.has_key("iradio-url"):
			meta["website"] = taglist["iradio-url"]

		# playing
		if taglist.has_key("iradio-title"):
			meta["playing"] = taglist["iradio-title"]

		elif taglist.has_key("artist") and taglist.has_key("title"):
			meta["playing"] = taglist["artist"] + " - " + taglist["title"]

			if taglist["title"] == "" and meta["playing"][-3:] == " - ":
				meta["playing"] = meta["playing"][:-3]

		# format
		if taglist.has_key("audio-codec"):
			meta["format"] = taglist["audio-codec"]

		if meta.get("format") == "MPEG" and taglist.has_key("layer"):
			meta["format"] += " layer " + str(taglist["layer"])

		# bitrate
		if taglist.has_key("nominal-bitrate"):
			meta["bitrate"] = int(taglist["nominal-bitrate"] / 1000)

		elif taglist.has_key("bitrate"):
			meta["bitrate"] = int(taglist["bitrate"] / 1000)

		# codec data
		meta["codec"]	= taglist

		self.__set_meta(meta)

		return True


	def __clear_meta(self):
		"Clears the metadata"

		for key in self.meta.keys():
			self.meta[key] = None

		self.emit("meta-changed", self.meta)


	def __set_error(self, error):
		"Sets an error state"

		self.stop()
		self.__set_state(STATE_ERROR, error)


	def __set_meta(self, meta):
		"Sets meta data"

		changed = False

		for key, value in meta.items():
			if self.meta.has_key(key) == False:
				continue

			elif self.meta[key] == value:
				continue

			self.meta[key] = value
			changed = True

		if changed == True:
			self.emit("meta-changed", self.meta)
			pass


	def __set_state(self, state, data = None):
		"Sets the current state"

		if self.state == state and data == None:
			return

		self.state = state
		self.emit("state-changed", state, data)


	def get_duration(self):
		"Gets the current pipeline duration"

		return self.pipeline.get_duration()


	def get_position(self):
		"Gets the current pipeline position"

		return self.pipeline.get_position()


	def get_volume(self):
		"Gets the current pipeline volume"

		return self.pipeline.get_volume()


	def play(self, uris):
		"Plays a list of uris"

		self.stop()
		self.__clear_meta()

		if uris == None or len(uris) == 0:
			self.__set_error("No streams found")

		for uri in uris:
			try:
				self.__set_state(STATE_CONNECTING, uri)
				self.pipeline.play(uri)

				return True

			except PlayError:
				continue

		else:
			self.__set_error("Unable to play stream")

		return False


	def set_volume(self, volume):
		"Sets the pipeline volume"

		return self.pipeline.set_volume(volume)


	def stop(self):
		"Stops the player"

		if self.state == STATE_STOPPED:
			return

		self.pipeline.stop()

		self.__set_state(STATE_STOPPED)



class Playlist(gobject.GObject):
	"A playlist"

	def __init__(self, data = None):
		gobject.GObject.__init__(self)

		self.list	= []

		if data != None:
			self.import_data(data)


	def add_files(self, files):
		"Adds a list of files to the playlist"

		for file in files:
			self.list.append(file)


	def clear(self):
		"Clears the playlist"

		self.list = []


	def export_pls(self):
		"Saves the playlist to a file"

		data = "[playlist]\n"
		data += "NumberOfEntries=%i\n" % len(self.list)

		for index, item in zip(range(len(self.list)), self.list):
			data += "File%i=%s\n" % (index + 1, item)

		return data


	def get_files(self):
		"Returns a list of the files in the playlist"

		return self.list


	def import_asx(self, data):
		"Reads data from an ASX playlist"

		try:
			dom = xml.dom.minidom.parseString(data.strip())

			if dom.documentElement.nodeName.lower() != "asx":
				raise DataError

			refnodes = [ node for node in dom.documentElement.getElementsByTagName("*") if node.nodeName.lower() == "ref" ]

			for node in refnodes:
				for i in range(node.attributes.length):
					attr = node.attributes.item(i)

					if attr.name.lower() == "href" and attr.value.strip() != "":
						self.list.append(attr.value.strip())

		except ExpatError:
			raise DataError


	def import_data(self, data):
		"Reads data from a playlist"

		if data.strip()[:10] == "[playlist]":
			self.import_pls(data)

		elif "<asx" in data.lower():
			self.import_asx(data)

		else:
			self.import_m3u(data)

		if len(self.get_files()) == 0:
			raise DataError


	def import_m3u(self, data):
		"Reads data from an M3U playlist"

		for item in data.splitlines():
			item = item.strip()

			if item == "":
				continue

			elif item[0] == "#":
				continue

			elif not re.match("^[a-z]+://\S+$", item, re.IGNORECASE):
				continue

			self.list.append(item)


	def import_pls(self, data):
		"Reads data from a PLS playlist"

		items = {}

		for item in data.splitlines():

			if "=" not in item:
				continue

			key, value = item.split("=", 1)
			key = key.strip().lower()
			value = value.strip()

			m = re.match("file(\d+)", key)

			if m == None:
				continue

			items[int(m.group(1))] = value


		# handle items
		keys = items.keys()
		keys.sort()

		for index in keys:
			self.list.append(items[index])



class Station(gobject.GObject):
	"Info about a station"

	def __init__(self):
		gobject.GObject.__init__(self)

		self.name		= ""
		self.description	= ""
		self.website		= ""
		self.streams		= []
		self.metaupdate		= True



class StationList(gobject.GObject):
	"A station list"

	__gsignals__ = {
		"changed"	: ( gobject.SIGNAL_ACTION, None, () ),
	}

	def __init__(self):
		gobject.GObject.__init__(self)

		self.stations = []


	def add_station(self, station):
		"Adds a station to the list"

		station.metaupdate = False
		self.stations.append(station)

		self.emit("changed")


	def export_xml(self):
		"Saves the station list as XML"

		data = ""
		data += "<?xml version=\"1.0\" encoding=\"utf-8\" ?>\n"
		data += "<stations>\n"

		for station in self.stations:
			data += "	<station>\n"
			data += "		<name>%s</name>\n" % util.escape_markup(station.name)
			data += "		<description>%s</description>\n" % util.escape_markup(station.description)
			data += "		<website>%s</website>\n" % util.escape_markup(station.website)

			for stream in station.streams:
				data += "		<stream>%s</stream>\n" % util.escape_markup(stream)

			data += "	</station>\n"

		data += "</stations>\n"

		return data


	def get_station(self, index):
		"Fetches a station from the list"

		try:
			return self.stations[index]

		except IndexError:
			return None


	def get_stations(self):
		"Returns a list of all stations"

		return self.stations


	def import_xml(self, data):
		"Loads stationlist from XML"

		try:
			dom = xml.dom.minidom.parseString(data.strip())

			if dom.documentElement.nodeName != "stations":
				raise DataError


			for node in dom.documentElement.childNodes:

				# check node type
				if node.nodeType == node.TEXT_NODE:
					continue

				if node.nodeType != node.ELEMENT_NODE or node.nodeName != "station":
					raise DataError

				# import station
				station = Station()

				for child in node.childNodes:

					if child.nodeType != child.ELEMENT_NODE:
						continue

					elif child.nodeName == "name":
						station.name = util.dom_text(child)

					elif child.nodeName == "description":
						station.description = util.dom_text(child)

					elif child.nodeName == "website":
						station.website = util.dom_text(child)

					elif child.nodeName == "stream":
						station.streams.append(util.dom_text(child))

					else:
						continue

				self.add_station(station)


		except ExpatError:
			raise DataError


	def remove_station(self, index):
		"Removes a station from the list"

		try:
			del self.stations[index]

			self.emit("changed")

		except IndexError:
			return None


	def update_station(self, index, station):
		"Updates a station"

		try:
			station.metaupdate	= False
			self.stations[index]	= station

			self.emit("changed")

		except IndexError:
			return None

