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
from gi.repository import Gtk
from gi.repository import Gst
from gi.repository import GLib


def clamp(x, min, max):
        if x < min:
            return min
        elif x > max:
            return max
        return x

class VUMeter (Gtk.DrawingArea):

    def __init__ (self):
        Gtk.DrawingArea.__init__ (self)

        self.connect ("draw", self.draw);
        self.set_size_request (270, 14)

        pipeline = "alsasrc ! level message=true ! fakesink sync=true"

        self.element = Gst.parse_launch (pipeline)

        pipebus = self.element.get_bus ()
        pipebus.add_signal_watch ()
        pipebus.connect ("message", self.pipe_message)

        self.peak = 0

    def pipe_message (self, bus, message):

        if message.structure and message.structure.get_name () == 'level':
            level = message.structure
            i = 0
            channels = len (level['peak'])

            for i in range (0, channels):
                self.peak = self.peak + level['peak'][i]

            # Take the mean of all the peak values in the channels to get a
            # "volume"
            self.peak = clamp (self.peak / channels, -90, 0)
            self.queue_draw ()

    def draw (self, widget, cr):
             cr.rectangle (0, 0, (self.peak + 90)*3, 14)
             #green
             cr.set_source_rgb (0.214, 0.8878, 0.39)

             #yellow and red
             if (self.peak > -30 and self.peak < -10):
                 cr.set_source_rgb (0.925, 0.882, 0.183)
             elif (self.peak > -10):
                 cr.set_source_rgb (1, 0, 0)

             cr.fill ()

             # rectangle border
             cr.set_source_rgb (0, 0, 0)
             cr.set_line_width (1)
             cr.rectangle (0, 0, 270, 14)
             cr.stroke ()
             return True

    def set_active (self, state):

        if (state):
            self.element.set_state (Gst.State.PLAYING)
        else:
            self.element.set_state (Gst.State.NULL)

