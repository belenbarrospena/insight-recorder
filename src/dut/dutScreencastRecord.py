#!/usr/bin/env python
#
# Script to record webcam and screencast
#
# Copyright 2012 Intel Corporation.
#
# Author: Michael Wood <michael.g.wood@intel.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, see <http://www.gnu.org/licenses>
#

from gi.repository import Gst


class Screencast:
    def __init__(self, fileOutputLocation):

      self.element = Gst.parse_launch ("""ximagesrc ! queue ! videorate
                                       force-fps=15/1 !
                                       video/x-raw-rgb,framerate=15/1 !
                                       ffmpegcolorspace !
                                       video/x-raw-yuv,framerate=15/1 ! vp8enc
                                       quality=8 threads=2 speed=2 mode=1 !
                                       queue ! webmmux !
                                       filesink
                                       location="""+fileOutputLocation+"""""")

      pipebus = self.element.get_bus ()

      pipebus.add_signal_watch ()
      pipebus.connect ("message", self.pipe1_changed_cb)

    def pipe1_changed_cb (self, bus, message):
        if message.type == Gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.player.set_state(Gst.State.NULL)
        if message.type == Gst.MESSAGE_EOS:
            # Null/Stop
            self.element.set_state (Gst.State.NULL)

    def record (self, start):
      if start == 1:
        print ("Start screencast record")
        self.element.set_state (Gst.State.PLAYING)
      else:
        print ("stop screencast record")
        self.element.send_event (Gst.event_new_eos ())


    def get_duration (self):
        self.duration, format = self.element.query_position (Gst.Format.TIME,
                                                             None)
        return self.duration

