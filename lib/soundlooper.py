# -*- coding: utf-8 -*-
# #!/usr/bin/python3
import codecs
import io
import os
import random
import string
import struct
from io import BytesIO
from math import ceil, floor

from eudplib import *

import customText4 as ct

# tinytag - an audio meta info reader
# Copyright (c) 2014-2018 Tom Wallroth
#
# Sources on github:
# http://github.com/devsnd/tinytag/

# MIT License

# Copyright (c) 2014-2018 Tom Wallroth

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


class TinyTagException(LookupError):  # inherit LookupError for backwards compat
	pass

	
class TinyTag(object):
	def __init__(self, filehandler, filesize):
		self._filehandler = filehandler
		self.filesize = filesize
		self.album = None
		self.albumartist = None
		self.artist = None
		self.audio_offset = None
		self.bitrate = None
		self.channels = None
		self.comment = None
		self.disc = None
		self.duration = None
		self.genre = None
		self.samplerate = None
		self.title = None
		self.track = None
		self.year = None

	@classmethod
	def get(cls, filename, tags=True, duration=True):
		size = os.path.getsize(filename)
		if not size > 0:
			return TinyTag(None, 0)
		parser_class = Ogg
		with io.open(filename, "rb") as af:
			tag = parser_class(af, size)
			tag.load(tags=tags, duration=duration)
			return tag

	def __repr__(self):
		return str(self)

	def load(self, tags, duration):
		if tags:
			self._parse_tag(self._filehandler)
		if duration:
			if tags:  # rewind file if the tags were already parsed
				self._filehandler.seek(0)
			self._determine_duration(self._filehandler)

	def _set_field(self, fieldname, bytestring, transfunc=None):
		"""convienience function to set fields of the tinytag by name.
		the payload (bytestring) can be changed using the transfunc"""
		if getattr(self, fieldname):  # do not overwrite existing data
			return
		value = bytestring if transfunc is None else transfunc(bytestring)
		if fieldname in ("track", "disc"):
			if type(value).__name__ in ("str", "unicode") and "/" in value:
				current, total = value.split("/")[:2]
				setattr(self, "%s_total" % fieldname, total)
			else:
				current = value
			setattr(self, fieldname, current)
		else:
			setattr(self, fieldname, value)

	def _determine_duration(self, fh):
		raise NotImplementedError()

	def _parse_tag(self, fh):
		raise NotImplementedError()


class Ogg(TinyTag):
	def __init__(self, filehandler, filesize):
		TinyTag.__init__(self, filehandler, filesize)
		self._tags_parsed = False
		self._max_samplenum = 0  # maximum sample position ever read

	def _determine_duration(self, fh):
		MAX_PAGE_SIZE = 65536  # https://xiph.org/ogg/doc/libogg/ogg_page.html
		if not self._tags_parsed:
			self._parse_tag(fh)  # determine sample rate
			fh.seek(0)  # and rewind to start
		if self.filesize > MAX_PAGE_SIZE:
			fh.seek(-MAX_PAGE_SIZE, 2)  # go to last possible page position
		while True:
			b = fh.peek(4)
			if len(b) == 0:
				return  # EOF
			if b[:4] == b"OggS":  # look for an ogg header
				for packet in self._parse_pages(fh):
					pass  # parse all remaining pages
				self.duration = self._max_samplenum / float(self.samplerate)
			else:
				idx = b.find(b"OggS")  # try to find header in peeked data
				seekpos = idx if idx != -1 else len(b) - 3
				fh.seek(max(seekpos, 1), os.SEEK_CUR)

	def _parse_tag(self, fh):
		page_start_pos = fh.tell()  # set audio_offest later if its audio data
		for packet in self._parse_pages(fh):
			walker = BytesIO(packet)
			if packet[0:7] == b"\x01vorbis":
				(
					channels,
					self.samplerate,
					max_bitrate,
					bitrate,
					min_bitrate,
				) = struct.unpack("<B4i", packet[11:28])
				if not self.audio_offset:
					self.bitrate = bitrate / 1024.0
					self.audio_offset = page_start_pos
			elif packet[0:7] == b"\x03vorbis":
				walker.seek(7, os.SEEK_CUR)  # jump over header name
				self._parse_vorbis_comment(walker)
			elif packet[0:8] == b"OpusHead":  # parse opus header
				# https://www.videolan.org/developers/vlc/modules/codec/opus_header.c
				# https://mf4.xiph.org/jenkins/view/opus/job/opusfile-unix/ws/doc/html/structOpusHead.html
				walker.seek(8, os.SEEK_CUR)  # jump over header name
				(version, ch, _, sr, _, _) = struct.unpack("<BBHIHB", walker.read(11))
				if (version & 0xF0) == 0:  # only major version 0 supported
					self.channels = ch
					self.samplerate = sr
			elif packet[0:8] == b"OpusTags":  # parse opus metadata:
				walker.seek(8, os.SEEK_CUR)  # jump over header name
				self._parse_vorbis_comment(walker)
			else:
				break
			page_start_pos = fh.tell()

	def _parse_vorbis_comment(self, fh):
		# for the spec, see: http://xiph.org/vorbis/doc/v-comment.html
		# discnumber tag based on: https://en.wikipedia.org/wiki/Vorbis_comment
		comment_type_to_attr_mapping = {
			"album": "album",
			"albumartist": "albumartist",
			"title": "title",
			"artist": "artist",
			"date": "year",
			"tracknumber": "track",
			"discnumber": "disc",
			"genre": "genre",
			"description": "comment",
		}
		vendor_length = struct.unpack("I", fh.read(4))[0]
		fh.seek(vendor_length, os.SEEK_CUR)  # jump over vendor
		elements = struct.unpack("I", fh.read(4))[0]
		for i in range(elements):
			length = struct.unpack("I", fh.read(4))[0]
			try:
				keyvalpair = codecs.decode(fh.read(length), "UTF-8")
			except UnicodeDecodeError:
				continue
			if "=" in keyvalpair:
				key, value = keyvalpair.split("=", 1)
				fieldname = comment_type_to_attr_mapping.get(key.lower())
				if fieldname:
					self._set_field(fieldname, value)

	def _parse_pages(self, fh):
		# for the spec, see: https://wiki.xiph.org/Ogg
		previous_page = b""  # contains data from previous (continuing) pages
		header_data = fh.read(27)  # read ogg page header
		while len(header_data) != 0:
			header = struct.unpack("<4sBBqIIiB", header_data)
			oggs, version, flags, pos, serial, pageseq, crc, segments = header
			self._max_samplenum = max(self._max_samplenum, pos)
			if oggs != b"OggS" or version != 0:
				raise TinyTagException("Not a valid ogg file!")
			segsizes = struct.unpack("B" * segments, fh.read(segments))
			total = 0
			for segsize in segsizes:  # read all segments
				total += segsize
				if total < 255:  # less than 255 bytes means end of page
					yield previous_page + fh.read(total)
					previous_page = b""
					total = 0
			if total != 0:
				if total % 255 == 0:
					previous_page += fh.read(total)
				else:
					yield previous_page + fh.read(total)
					previous_page = b""
			header_data = fh.read(27)


# soundlooper - manage loop sounds for SC:R

path = ""
loop_dict = dict()
INV_SYS_TIME = 0x51CE8C
CP = 0x6509B0


def id_generator():
	# generate unique random string of length 5
	chars = string.ascii_letters + string.digits
	return "".join(random.sample(chars * 5, 5))


class Loop:
	def __init__(self, index, identifier, count, intro, length, bridge, goto):
		self.index = index
		self.identifier = identifier
		self.bar_count = count
		self.intro_length = intro
		self.bar_length = length
		self.bridge_length = bridge
		self.goto = goto


def SetPath(new_path):
	global path
	path = new_path


def AddLoop(filename, goto=1):
	intro_length, bar_length, bridge_length = 0, 0, 0
	identifier = id_generator()
	if not hasattr(AddLoop, "index"):
		AddLoop.index = 0
	for i in range(101):
		file_path = path + "/{0}/{0}{1:02d}.ogg".format(filename, i)
		try:
			content = open(file_path, "rb").read()
		except FileNotFoundError:
			if i == 0:
				continue
			loop_dict[filename] = Loop(
				AddLoop.index,
				identifier,
				i - 1,
				intro_length,
				bar_length,
				bridge_length,
				goto,
			)
			AddLoop.index += 1
			print(
				u"{}{:02d}.ogg: {} ||: {} | {} :||".format(
					filename, i - 1, intro_length, bar_length, bridge_length
				)
			)
			return
		else:
			tag = Ogg.get(file_path)
			if i == 0:
				intro_length = round(tag.duration, 3)
			elif bar_length == 0:
				bar_length = round(tag.duration, 3)
			bridge_length = round(tag.duration, 3)
			MPQAddFile("{}{:02d}".format(identifier, i), content)


def u2i4(s):
	return b2i4(u2b(s))


def T2i(title):
	try:
		return loop_dict[title].index
	except (KeyError):
		return title


@EUDFunc
def calculate_error():
	x = EUDVariable()
	DoActions(x.SetNumber(-41))
	_next = Forward()
	EUDJumpIfNot(Memory(0x5124F0, Exactly, 42), _next)
	x << f_dwread_epd(EPD(0x5124F0))
	_next << NextTrigger()
	speed_map = {
		(2047, 2047): 29,
		(4095, 4095): 18,
		(65535, 65535): 1,
		(1157, 1157): 36,
		(1437, 1437): 29,
		(1984, 1984): 29,
		(3472, 3472): 18,
		(41667, 41667): 1,
		(1736, 1736): 36,
		(2155, 2155): 29,
		(2976, 2976): 21,
		(5208, 5208): 18,
		(62500, 62500): 1,
		(2463, 2463): 29,
		(3401, 3401): 21,
		(5952, 5952): 18,
		(71429, 71429): 1,
	}
	for point, speed in speed_map.items():
		V84, V88 = point
		RawTrigger(
			conditions=[Memory(0x51CE84, Exactly, V84), Memory(0x51CE88, Exactly, V88)],
			actions=x.SetNumber(speed),
		)
	EUDReturn((493 - 7 * x) // 41)


class SoundLooper:
	bars = EUDArray(len(loop_dict))

	def __init__(self):
		self.current_loop = EUDVariable(-1)
		self.previous_loop = EUDVariable(-1)
		self.current_bar = EUDLightVariable()
		self.bar_carry = EUDLightVariable()
		self._check_time = Forward()
		self._set_bar_length = Forward()
		self._set_loop = [Forward() for _ in range(2)]
		self._set_bar = Forward()
		self._set_localcp = Forward()
		self._check_last_bar = Forward()
		self._add1_bar = Forward()
		self._set_intro_length = Forward()
		self._set_bridge_length = Forward()
		self._set1_bar = Forward()
		self._set_goto = [Forward() for _ in range(3)]

	def initialize(self):
		ct.f_reset()
		DoActions(
			[
				SetMemory(self._set_loop[0] + 16, SetTo, ct.epd),
				SetMemory(self._set_loop[1] + 16, SetTo, ct.epd + 1),
				SetMemory(self._set_bar + 16, SetTo, ct.epd + 1),
				SetMemory(self._set_localcp + 20, SetTo, ct.cp),
			]
		)

	def player(self):
		_end = Forward()
		EUDJumpIf(self.current_loop.Exactly(-1), _end)
		EUDJumpIf([self._check_time << Memory(INV_SYS_TIME, AtLeast, ~0)], _end)
		DoActions(
			[
				SetMemory(self._check_time + 8, SetTo, f_dwread_epd(EPD(INV_SYS_TIME))),
				self._set_bar_length << SetMemory(self._check_time + 8, Add, 0),
				self._set_loop[0] << SetMemory(0, SetTo, 0),
				self._set_loop[1] << SetMemory(0, SetTo, 0),
				self._set_bar << SetMemory(0, Add, 0),
				self._set_localcp << SetMemory(CP, SetTo, 0),
				PlayWAV(ct.strBuffer),
				self.current_bar.AddNumber(1),
				SetMemory(self._set_bar + 20, Add, 0x10000),
				self.bar_carry.AddNumber(1),
				self._add1_bar << SetMemory(0, Add, 1),
			]
		)
		RawTrigger(
			conditions=self.bar_carry.AtLeast(10),
			actions=[
				self.bar_carry.SubtractNumber(10),
				SetMemory(self._set_bar + 20, Subtract, 0xA0000 - 0x100),
			],
		)
		RawTrigger(  # if intro was played, modify playtime
			conditions=self.current_bar.Exactly(1),
			actions=[self._set_intro_length << SetMemory(self._check_time + 8, Add, 0)],
		)
		RawTrigger(  # if last bar was played, go to start
			conditions=[self._check_last_bar << self.current_bar.AtLeast(0)],
			actions=[
				self._set_bridge_length << SetMemory(self._check_time + 8, Add, 0),
				self._set_goto[0] << self.current_bar.SetNumber(1),
				self._set_goto[1] << SetMemory(self._set_bar + 20, SetTo, 0x10000),
				self._set_goto[2] << self.bar_carry.SetNumber(1),
				self._set1_bar << SetMemory(0, SetTo, 1),
			],
		)
		ct.f_setcachedcp()
		_end << NextTrigger()

	@EUDMethod
	def setbar(self, bar):
		q, r = f_div(bar, 10)
		DoActions(
			[
				self.current_bar.SetNumber(bar),
				SetMemory(self._set_bar + 20, SetTo, r * 0x10000 + q * 0x100),
				self.bar_carry.SetNumber(r),
				SetMemoryEPD(EPD(SoundLooper.bars) + self.current_loop, SetTo, bar),
			]
		)

	def play(self, title, bar=None):
		if title is None:
			self.setloop(self.current_loop)
		else:
			index = T2i(title)
			self.setloop(index)
		if bar is None:
			self.setbar(SoundLooper.bars[index])
		else:
			self.setbar(bar)

	@EUDMethod
	def setloop(self, index):
		DoActions(
			[
				self.previous_loop.SetNumber(self.current_loop),
				self.current_loop.SetNumber(index),
				SetMemory(self._set_bar_length + 20, SetTo, calculate_error()),
				SetMemory(self._set_goto[0] + 20, SetTo, 1),
				SetMemory(self._set_goto[1] + 20, SetTo, 0x10000),
				SetMemory(self._set_goto[2] + 20, SetTo, 1),
				SetMemory(self._set1_bar + 20, SetTo, 1),
			]
		)
		EUDSwitch(index)
		for filename, loop in loop_dict.items():
			EUDSwitchCase()(loop.index)
			DoActions([
					SetMemory(self._set_loop[0] + 20, SetTo, u2i4(loop.identifier[:4])),
					SetMemory(
						self._set_loop[1] + 20, SetTo, u2i4(loop.identifier[4] + "00\0")
					),
					SetMemory(self._check_last_bar + 8, SetTo, loop.bar_count + 1),
					SetMemory(
						self._set_intro_length + 20,
						SetTo,
						ceil((loop.bar_length - loop.intro_length) * 1000),
					),
					SetMemory(
						self._set_bar_length + 20, Add, ceil(-loop.bar_length * 1000)
					),
					SetMemory(
						self._set_bridge_length + 20,
						SetTo,
						ceil((loop.bar_length - loop.bridge_length) * 1000),
					),
					SetMemory(
						self._add1_bar + 16, SetTo, EPD(SoundLooper.bars) + loop.index
					),
					SetMemory(
						self._set1_bar + 16, SetTo, EPD(SoundLooper.bars) + loop.index
					),
					[
						SetMemory(self._set_goto[0] + 20, SetTo, loop.goto),
						SetMemory(
							self._set_goto[1] + 20,
							SetTo,
							(loop.goto % 10) * 0x10000 + (loop.goto // 10) * 0x100,
						),
						SetMemory(self._set_goto[2] + 20, SetTo, loop.goto % 10),
						SetMemory(self._set1_bar + 20, SetTo, loop.goto),
					]
					if loop.goto != 1
					else [],
				]
			)
			EUDBreak()
		EUDEndSwitch()

	def pause(self):
		DoActions(
			[
				self.previous_loop.SetNumber(self.current_loop),
				self.current_loop.SetNumber(-1),
			]
		)

	def resume(self):
		self.setloop(self.previous_loop)

	@EUDMethod
	def toggle(self):
		if EUDIf()(self.current_loop.Exactly(-1)):
			self.resume()
		if EUDElse()():
			self.pause()
		EUDEndIf()

	@classmethod
	def sendbar(cls, dst, src, _fdict={}):
		dst, src = T2i(dst), T2i(src)

		if SoundLooper.bars in _fdict:
			_f = _fdict[SoundLooper.bars]
		else:
			@EUDFunc
			def _f(dst, src):
				SoundLooper.bars[dst] = SoundLooper.bars[src]
			
			_fdict[SoundLooper.bars] = _f

		_f(dst, src)

	@classmethod
	def setloopbar(cls, loop, bar):
		loop = T2i(loop)
		return SetMemory(SoundLooper.bars + 4 * loop, SetTo, bar)
