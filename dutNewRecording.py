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

import gst
import time

from datetime import datetime

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkX11
from gi.repository import GUdev
Gdk.threads_init ()

class mode:
    TWOCAM, SCREENCAST = range (2)

class NewRecording:
    def __init__(self, mainWindow):

        self.player = None
        self.busSig1 = None
        self.busSig2 = None
        self.recordingTitle = None

        self.secondarySource = "/dev/video0" #Default recording device
        self.primarySource = "Screen"

        self.primarySourceHeight = 0
        self.primarySourceWidth = 0
        self.secondarySourceHeight = 0
        self.secondarySourceWidth = 0

        self.dialog = Gtk.Dialog ("Create recoding",
                                  mainWindow,
                                  2)

        cancel = self.dialog.add_button ("Cancel", Gtk.ResponseType.CANCEL)
        accept = self.dialog.add_button ("Start recording", Gtk.ResponseType.ACCEPT)

        # UI Elements for create recording dialog
        label = Gtk.Label (label="Recording name:", halign=Gtk.Align.START)
        entry = Gtk.Entry ()
        self.primaryCombo = Gtk.ComboBoxText ()
        self.primaryCombo.connect ("changed", self.primary_capture_changed)
        self.primaryCombo.set_title ("Primary Combo")
        self.primaryCombo.append_text ("Screen")
        primaryComboLabel = Gtk.Label ("Primary capture:")

        self.secondaryCombo = Gtk.ComboBoxText ()
        self.secondaryCombo.connect ("changed", self.secondary_capture_changed)
        self.secondaryCombo.set_title ("Secondary Combo")

        #Add available video4linux devices
        devices = GUdev.Client ().query_by_subsystem ("video4linux")


        for device in devices:
            self.secondaryCombo.append_text (device.get_name ())
            self.primaryCombo.append_text (device.get_name ())

        secondaryComboLabel = Gtk.Label ("Secondary capture:")

        devicesBox = Gtk.HBox ()
        devicesBox.pack_start (primaryComboLabel, False, False, 3)
        devicesBox.pack_start (self.primaryCombo, False, False, 3)
        self.samePrimaryAlert = Gtk.Image.new_from_icon_name ("dialog-warning",
                                                Gtk.IconSize.SMALL_TOOLBAR)
        devicesBox.pack_start (self.samePrimaryAlert, False, False, 3)

        devicesBox.pack_start (secondaryComboLabel, False, False, 3)
        devicesBox.pack_start (self.secondaryCombo, False, False, 3)

        self.sameSecondaryAlert = Gtk.Image.new_from_icon_name ("dialog-warning",
                                                Gtk.IconSize.SMALL_TOOLBAR)
        devicesBox.pack_start (self.sameSecondaryAlert, False, False, 3)

        self.playerWindow = Gtk.DrawingArea ()
        self.playerWindow.set_double_buffered (False)
        self.playerWindow.set_size_request (600, 300)
        self.playerWindow.connect ("realize", self.window_real)

        # TODO
        audioToggle = Gtk.Switch ()
        audioSource = Gtk.ComboBoxText ()

        audioBox = Gtk.HBox ()

        contentArea = self.dialog.get_content_area ()
        contentArea.set_spacing (8)
        contentArea.add (label)
        contentArea.add (entry)
        contentArea.add (devicesBox)
        contentArea.add (self.playerWindow)
        contentArea.add (audioBox)

        contentArea.show_all ()

        self.samePrimaryAlert.hide ()
        self.sameSecondaryAlert.hide ()

        self.recordingTitle = entry.get_text ()

    def secondary_capture_changed (self, combo):
        print ("secondary changed")
        deviceName = combo.get_active_text ()

        if (deviceName == None):
            return

        self.sameSecondaryAlert.hide ()

        self.secondarySource = "/dev/"+deviceName

        self.player.set_state (gst.STATE_READY)

        if (self.mode == mode.TWOCAM):
            cam1 = self.player.get_by_name ("cam1")
            cam1.set_locked_state (False)
            cam1.set_state (gst.STATE_NULL)
            # Avoid both being set by locking the other source in a null state
            if (self.secondarySource == self.primarySource):
                cam1.set_locked_state (True)
                self.primaryCombo.set_active (-1)
                self.samePrimaryAlert.show ()

        cam2 = self.player.get_by_name ("cam2")
        cam2.set_locked_state (False)
        cam2.set_state (gst.STATE_NULL)

        cam2.set_property ("device", self.secondarySource)

        self.player.set_state (gst.STATE_PLAYING)


    def primary_capture_changed (self, combo):
        deviceName = combo.get_active_text ()

        if (deviceName == None):
            return

        self.samePrimaryAlert.hide ()

        self.primarySource = "/dev/"+deviceName

        if (deviceName == "Screen"):
            self.video_preview_screencast_webcam ()
            return
        #If we're not running in two cam mode already set it up
        elif (self.mode != mode.TWOCAM):
            self.video_preview_webcam_webcam ()

        self.player.set_state (gst.STATE_READY)

        cam2 = self.player.get_by_name ("cam2")
        cam1 = self.player.get_by_name ("cam1")

        cam2.set_locked_state (False)
        cam1.set_locked_state (False)

        cam2.set_state (gst.STATE_NULL)
        cam1.set_state (gst.STATE_NULL)

        # Avoid both being set by locking the other source in a null state
        if (self.secondarySource == self.primarySource):
            cam2.set_locked_state (True)
            self.secondaryCombo.set_active (-1)
            self.sameSecondaryAlert.show ()

        cam1.set_property ("device", self.primarySource)

        self.player.set_state (gst.STATE_PLAYING)

    def window_real (self,wef2):
        print ("drawable realised")
        self.video_preview_screencast_webcam ()

    def video_preview_screencast_webcam (self):

        if (self.player):
            self.player.set_state(gst.STATE_NULL)

        self.mode = mode.SCREENCAST

        screen = Gdk.get_default_root_window ().get_display ().get_screen (0)

        self.primarySourceHeight = screen.get_height ()
        self.primarySourceWidth = screen.get_width ()
        self.secondarySourceHeight = 240
        self.secondarySourceWidth = 320

        posY = str (self.primarySourceHeight - self.secondarySourceHeight)
        posX = str (self.primarySourceWidth - self.secondarySourceWidth)

        self.player = gst.parse_launch ("""v4l2src device=/dev/video0 name="cam2" !
                                       videoscale ! queue ! videoflip
                                       method=horizontal-flip !
                                       video/x-raw-yuv,height=240,framerate=15/1
                                       ! videomixer name=mix sink_0::xpos=0
                                       sink_0::ypos=0 sink_1::xpos="""+posX+"""
                                       sink_1::ypos="""+posY+""" !
                                       xvimagesink  sync=false       ximagesrc
                                       use-damage=false show-pointer=true  !
                                       videoscale ! video/x-raw-rgb,framerate=15/1 ! ffmpegcolorspace ! video/x-raw-yuv ! mix.""")


        self.player.set_state(gst.STATE_PLAYING)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        self.busSig1 = bus.connect("message", self.on_message)
        self.busSig2 = bus.connect("sync-message::element",
                                   self.on_sync_message)

    def video_preview_webcam_webcam (self):

        self.mode = mode.TWOCAM

        if (self.player):
            self.player.set_state(gst.STATE_NULL)


        self.primarySourceHeight = 768
        self.primarySourceWidth = 1024
        self.secondarySourceHeight = 240
        self.secondarySourceWidth = 320

        self.player = gst.parse_launch ("""
                        v4l2src device=/dev/video0 name="cam2" ! queue !
                        videoflip method=horizontal-flip !
                        videoscale  add-borders=1 !
                        video/x-raw-yuv,width=320,height=240,framerate=15/1,pixel-aspect-ratio=1/1 !                           videomixer name=mix sink_0::xpos=0
                                   sink_0::ypos=0 sink_1::xpos=704
                                   sink_1::ypos=528 !
                        xvimagesink  sync=false
                        v4l2src device=/dev/video1 name="cam1" !
                        queue ! videoflip method=horizontal-flip !
                        videoscale add-borders=1 !
                        video/x-raw-yuv,width=1024,height=768,pixel-aspect-ratio=1/1 !
                        mix.
                                        """)

        self.player.set_state(gst.STATE_PLAYING)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        self.busSig1 = bus.connect("message", self.on_message)
        self.busSig2 = bus.connect("sync-message::element",
                                   self.on_sync_message)


    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
        elif t == gst.MESSAGE_ERROR:
            self.player.set_state(gst.STATE_NULL)
            err, debug = message.parse_error()
            print "Error: %s" % err, debug

    def on_sync_message(self, bus, message):
        if message.structure is None:
            return
        message_name = message.structure.get_name()
        if message_name == "prepare-xwindow-id":
            imagesink = message.src

            Gdk.threads_enter()

            # Sync with the X server before giving the X-id to the sink
            Gdk.get_default_root_window ().get_display ().sync ()
            xid = self.playerWindow.get_window ().get_xid()
            imagesink.set_property("force-aspect-ratio", True)
            imagesink.set_xwindow_id (xid)

            Gdk.threads_leave ()

    def get_new_recording_info (self):
        if self.response == Gtk.ResponseType.ACCEPT:
            #TODO DONT USE timedate in folder structure
            timeStamp = datetime.today().strftime("%d-%m-%H%M%S")
            print (self.recordingTitle)
            info = ([self.recordingTitle, timeStamp, self.secondaryDevice])
            return info
        else:
            return None
