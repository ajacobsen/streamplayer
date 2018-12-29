#!/usr/bin/env python3

import sys
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GLib, Gst, GObject, GdkPixbuf

from playlist import Playlist
from config import Config

class Colors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

class Player:

	def __init__(self, loop, playlist):
		self.playlist = playlist
		self.loop = loop
		self.counter = 0
		self.create_pipeline(self.playlist.get_next())
		self.prev_msg = None

	def create_pipeline(self, entry):
		self.counter += 1

		mixer = Gst.ElementFactory.make("videomixer", "mixer")
		main_filesrc = Gst.ElementFactory.make("filesrc", "main_filesrc")
		main_filesrc.set_property("location", entry.get_video())
		main_decodebin = Gst.ElementFactory.make("decodebin", "main_decodebin")
		main_videoconvert = Gst.ElementFactory.make("videoconvert", "main_videoconvert")
		main_videoscale = Gst.ElementFactory.make("videoscale", "main_videoscale")
		main_capsfilter = Gst.ElementFactory.make("capsfilter", "main_capsfilter")
		main_capsfilter.set_property("caps", Gst.Caps.from_string("video/x-raw,width={}".format(entry.get_video_size_x())))
		if entry.has_logo():
			logo = Gst.ElementFactory.make("gdkpixbufoverlay", "logo")
			logo.set_property("location", entry.get_logo())
		if entry.has_overlay():
			overlay_filesrcs = []
			overlay_decodebins = []
			overlay_videoconverts = []
			i = 0
			for overlay in entry.get_overlays():
				tmp_fsrc = Gst.ElementFactory.make("filesrc", "overlay_filesrc_{}".format(i))
				tmp_fsrc.set_property("location", overlay["file"])
				overlay_filesrcs.append(tmp_fsrc)

				tmp_decodebin = Gst.ElementFactory.make("decodebin", "overlay_decodebin_{}".format(i))
				overlay_decodebins.append(tmp_decodebin)

				tmp_videoconvert = Gst.ElementFactory.make("videoconvert", "overlay_videoconvert_{}".format(i))
				overlay_videoconverts.append(tmp_videoconvert)
				i += 1

		x264enc = Gst.ElementFactory.make("x264enc")
		x264_videoconvert = Gst.ElementFactory.make("videoconvert", "x264_videoconvert")
		queue_vid = Gst.ElementFactory.make("queue", "queue_vid")
		main_audioconvert = Gst.ElementFactory.make("audioconvert", "main_audioconvert")
		voaacenc = Gst.ElementFactory.make("voaacenc")
		queue_audio = Gst.ElementFactory.make("queue", "queue_audio")
		flvmux = Gst.ElementFactory.make("flvmux")
		# sink = Gst.ElementFactory.make("filesink", "sink")
		# sink.set_property("location", "test{}.flv".format(self.counter))
		sink = Gst.ElementFactory.make("rtmpsink")
		sink.set_property("location", Config.RTMPSINKLOCATION)

		self.pipeline = Gst.Pipeline.new()

		self.pipeline.add(mixer)
		self.pipeline.add(main_filesrc)
		self.pipeline.add(main_decodebin)
		self.pipeline.add(main_videoconvert)
		self.pipeline.add(main_videoscale)
		self.pipeline.add(main_capsfilter)

		if entry.has_logo():
			self.pipeline.add(logo)

		if entry.has_overlay():
			for fsrc in overlay_filesrcs:
				self.pipeline.add(fsrc)
			for decodebin in overlay_decodebins:
				self.pipeline.add(decodebin)
			for videoconvert in overlay_videoconverts:
				self.pipeline.add(videoconvert)

		self.pipeline.add(x264enc)
		self.pipeline.add(x264_videoconvert)
		self.pipeline.add(queue_vid)
		self.pipeline.add(main_audioconvert)
		self.pipeline.add(voaacenc)
		self.pipeline.add(queue_audio)
		self.pipeline.add(flvmux)
		self.pipeline.add(sink)

		main_filesrc.link(main_decodebin)
		main_decodebin.connect("pad-added", self.on_decodebin_pad_added, main_videoconvert, main_audioconvert)
		main_videoconvert.link(main_videoscale)
		main_videoscale.link(main_capsfilter)
		if entry.has_logo():
			main_capsfilter.link(logo)
			logo.link(mixer)
			mixer.get_static_pad("sink_0").set_property("ypos", entry.get_video_pos_y())
		else:
			main_capsfilter.link(mixer)

		if entry.has_overlay():
			for i in range(len(overlay_filesrcs)):
				overlay_filesrcs[i].link(overlay_decodebins[i])
				overlay_decodebins[i].connect("pad-added", self.on_decodebin_pad_added, overlay_videoconverts[i], None)
				overlay_videoconverts[i].link(mixer)
				pad = mixer.get_static_pad("sink_{}".format(i+1))
				pad.set_property("offset", entry.get_overlays()[i]["offset"])

		mixer.link(x264_videoconvert)
		x264_videoconvert.link(x264enc)
		x264enc.link(queue_vid)
		queue_vid.link(flvmux)

		main_audioconvert.link(voaacenc)
		voaacenc.link(queue_audio)
		queue_audio.link(flvmux)

		flvmux.link(sink)

		bus = self.pipeline.get_bus()
		bus.add_signal_watch()
		bus.connect("message", self.main_bus_cb)

	def on_decodebin_pad_added(self, element, new_pad, target_vid, target_audio):
		if new_pad.query_caps(None).to_string().startswith("video/x-raw"):
			self.color_print("PAD ADDED: {} {} {}".format(target_vid.get_name(), element.get_name(), new_pad.get_name()))
			new_pad.link(target_vid.get_static_pad("sink"))
		elif target_audio and new_pad.query_caps(None).to_string().startswith("audio"):
			self.color_print("PAD ADDED: {} {} {}".format(target_audio.get_name(), element.get_name(), new_pad.get_name()))
			new_pad.link(target_audio.get_static_pad("sink"))

	def main_bus_cb(self, bus, msg):
		if msg.type == Gst.MessageType.STATE_CHANGED:
			if self.prev_msg != msg.get_structure().get_value("new-state"):
				self.prev_msg = msg.get_structure().get_value("new-state")
				print("{} {} {}".format(Colors.OKGREEN, msg.parse_state_changed(), Colors.ENDC))
		elif msg.type == Gst.MessageType.ERROR:
			print("{} {} {}".format(Colors.FAIL, msg.parse_error(), Colors.ENDC))
		elif msg.type == Gst.MessageType.WARNING:
			print("{} {} {}".format(Colors.WARNING, msg.parse_warning(), Colors.ENDC))
		elif msg.type == Gst.MessageType.EOS:
				print("MAIN_PIPE EOS")
				self.stop()
				next_entry = self.playlist.get_next()
				if next_entry:
					self.create_pipeline(next_entry)
					self.play()
				else:
					self.loop.quit()
		else:
			print("{} {} {}".format(Colors.OKGREEN, msg.type, Colors.ENDC))

		return True

	def color_print(self, msg):
		print("{} {} {}".format(Colors.OKBLUE, msg, Colors.ENDC))

	def play(self):
		self.pipeline.set_state(Gst.State.PLAYING)

	def stop(self):
		self.pipeline.set_state(Gst.State.NULL)

def main(args):
	loop = GLib.MainLoop()
	GLib.threads_init()
	Gst.init(None)
 
	player = Player(loop, Playlist(Config.PLAYLISTFILE))
	player.play()

	try:
		loop.run()
	except:
		pass

	player.stop()

if __name__ == '__main__':
	main(sys.argv)

