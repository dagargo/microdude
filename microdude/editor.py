# -*- coding: utf-8 -*-
#
# Copyright 2015 David García Goñi
#
# This file is part of MicroDude.
#
# MicroDude is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# MicroDude is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with MicroDude.  If not, see <http://www.gnu.org/licenses/>.

"""MicroDude user interface"""

from gi.repository import Gtk
from gi.repository import GLib
import logging
import pkg_resources
from microdude import connector
import sys, getopt

PKG_NAME = 'microdude'

glade_file = pkg_resources.resource_filename(__name__, 'resources/gui.glade')
version = pkg_resources.get_distribution(PKG_NAME).version

EXTENSION = 'mbseq'
DEF_FILENAME = 'sequences.' + EXTENSION

log_level = logging.ERROR

def print_help():
    print ('Usage: {:s} [-v]'.format(PKG_NAME))

try:
    opts, args = getopt.getopt(sys.argv[1:], "hv")
except getopt.GetoptError:
    print_help()
    sys.exit(1)
for opt, arg in opts:
    if opt == '-h':
        print_help()
        sys.exit()
    elif opt == '-v':
        log_level = logging.DEBUG

logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

class Editor(object):
    """MicroDude user interface"""

    def __init__(self):
        self.connector = connector.Connector()
        self.main_window = None

    def init_ui(self):
        file = open(glade_file, 'r')
        glade_contents = file.read()
        file.close()
        self.builder = Gtk.Builder()
        self.builder.add_from_string(glade_contents)
        self.main_window = self.builder.get_object('main_window')
        self.main_window.connect('delete-event', lambda widget, event: self.quit())
        self.main_window.set_position(Gtk.WindowPosition.CENTER)
        self.about_dialog = self.builder.get_object('about_dialog')
        self.about_dialog.set_position(Gtk.WindowPosition.CENTER)
        self.about_dialog.set_transient_for(self.main_window)
        self.about_dialog.set_version(version)
        self.connect_button = self.builder.get_object('connect_button')
        self.connect_button.connect('clicked', lambda widget: self.ui_reconnect())
        self.download_button = self.builder.get_object('download_button')
        self.download_button.connect('clicked', lambda widget: self.show_download())
        self.upload_button = self.builder.get_object('upload_button')
        self.upload_button.connect('clicked', lambda widget: self.show_upload())
        self.about_button = self.builder.get_object('about_button')
        self.about_button.connect('clicked', lambda widget: self.show_about())
        self.main_container = self.builder.get_object('main_container')
        self.note_priority = self.builder.get_object('note_priority')
        self.vel_response = self.builder.get_object('vel_response')
        self.tx_channel = self.builder.get_object('tx_channel')
        self.rx_channel = self.builder.get_object('rx_channel')
        self.play = self.builder.get_object('play')
        self.retriggering = self.builder.get_object('retriggering')
        self.next_sequence = self.builder.get_object('next_sequence')
        self.step_on = self.builder.get_object('step_on')
        self.step_length = self.builder.get_object('step_length')
        self.lfo_key_retrigger = self.builder.get_object('lfo_key_retrigger')
        self.envelope_legato = self.builder.get_object('envelope_legato')
        self.bend_range = self.builder.get_object('bend_range')
        self.gate_length = self.builder.get_object('gate_length')
        self.sync = self.builder.get_object('sync')
        self.note_priority.connect('changed', lambda widget: self.set_parameter_from_combo(connector.NOTE_PRIORITY, widget))
        self.vel_response.connect('changed', lambda widget: self.set_parameter_from_combo(connector.VEL_RESPONSE, widget))
        self.tx_channel.connect('changed', lambda widget: self.set_parameter_from_combo(connector.TX_CHANNEL, widget))
        self.rx_channel.connect('changed', lambda widget: self.set_parameter_from_combo(connector.RX_CHANNEL, widget))
        self.play.connect('changed', lambda widget: self.set_parameter_from_combo(connector.PLAY_ON, widget))
        self.retriggering.connect('changed', lambda widget: self.set_parameter_from_combo(connector.RETRIGGERING, widget))
        self.next_sequence.connect('changed', lambda widget: self.set_parameter_from_combo(connector.NEXT_SEQUENCE, widget))
        self.step_on.connect('changed', lambda widget: self.set_parameter_from_combo(connector.STEP_ON, widget))
        self.step_length.connect('changed', lambda widget: self.set_parameter_from_combo(connector.STEP_LENGTH, widget))
        self.lfo_key_retrigger.connect('state-set', lambda widget, state: self.set_parameter_from_switch(connector.LFO_KEY_RETRIGGER, state, widget))
        self.envelope_legato.connect('state-set', lambda widget, state: self.set_parameter_from_switch(connector.ENVELOPE_LEGATO, state, widget))
        self.bend_range.connect('value-changed', lambda widget: self.set_parameter_from_spin(connector.BEND_RANGE, widget))
        self.gate_length.connect('changed', lambda widget: self.set_parameter_from_combo(connector.GATE_LENGTH, widget))
        self.sync.connect('changed', lambda widget: self.set_parameter_from_combo(connector.SYNC, widget))
        self.statusbar = self.builder.get_object('statusbar')
        self.context_id = self.statusbar.get_context_id(PKG_NAME)

        self.filter_mbseq = Gtk.FileFilter()
        self.filter_mbseq.set_name('MicroBrute sequence files')
        self.filter_mbseq.add_pattern('*.' + EXTENSION)
        
        self.filter_any = Gtk.FileFilter()
        self.filter_any.set_name('Any files')
        self.filter_any.add_pattern('*')

        self.main_window.present()
        self.update_sensitivity()

    def connect(self):
        self.connector.connect()
        if self.connector.connected():
            self.set_status_msg('Connected')
        else:
            self.set_status_msg('Not connected')
        
    def ui_reconnect(self):
        if not self.connector.connected():
            self.connect();
            self.set_ui()

    def set_ui(self):
        """Load the configuration from the MicroBrute and set the values in the interface."""
        if self.connector.connected():
            logger.debug('Loading status...')
            self.configuring = True
            value = self.connector.get_parameter(connector.RX_CHANNEL)
            self.set_combo_value(self.rx_channel, value)
            value = self.connector.get_parameter(connector.TX_CHANNEL)
            self.set_combo_value(self.tx_channel, value)
            value = self.connector.get_parameter(connector.RETRIGGERING)
            self.set_combo_value(self.retriggering, value)
            value = self.connector.get_parameter(connector.LFO_KEY_RETRIGGER)
            self.lfo_key_retrigger.set_state(value)
            self.lfo_key_retrigger.set_active(value)
            value = self.connector.get_parameter(connector.PLAY_ON)
            self.set_combo_value(self.play, value)
            value = self.connector.get_parameter(connector.NOTE_PRIORITY)
            self.set_combo_value(self.note_priority, value)
            value = self.connector.get_parameter(connector.ENVELOPE_LEGATO)
            self.envelope_legato.set_state(value)
            self.envelope_legato.set_active(value)
            value = self.connector.get_parameter(connector.VEL_RESPONSE)
            self.set_combo_value(self.vel_response, value)
            value = self.connector.get_parameter(connector.NEXT_SEQUENCE)
            self.set_combo_value(self.next_sequence, value)
            value = self.connector.get_parameter(connector.BEND_RANGE)
            self.bend_range.set_value(value)
            value = self.connector.get_parameter(connector.STEP_LENGTH)
            self.set_combo_value(self.step_length, value)
            value = self.connector.get_parameter(connector.GATE_LENGTH)
            self.set_combo_value(self.gate_length, value)
            value = self.connector.get_parameter(connector.STEP_ON)
            self.set_combo_value(self.step_on, value)
            value = self.connector.get_parameter(connector.SYNC)
            self.set_combo_value(self.sync, value)
            self.configuring = False
            self.update_sensitivity()
        return True

    def update_sensitivity(self):
        self.main_container.set_sensitive(self.connector.connected())
        self.download_button.set_sensitive(self.connector.connected())
        self.upload_button.set_sensitive(self.connector.connected())

    def show_upload(self):
        dialog = Gtk.FileChooserDialog('Open', self.main_window,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.add_filter(self.filter_mbseq)
        dialog.add_filter(self.filter_any)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            logger.debug('Selected file: ' + dialog.get_filename())
            self.set_sequence_file(dialog.get_filename())
        dialog.destroy()

    def set_sequence_file(self, filename):
        with open(filename, 'r') as input_file:
            for line in input_file:
                self.connector.set_sequence(line.rstrip('\n'))
                
    def show_download(self):
        dialog = Gtk.FileChooserDialog('Save as', self.main_window,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        Gtk.FileChooser.set_do_overwrite_confirmation(dialog, True)
        dialog.add_filter(self.filter_mbseq)
        dialog.add_filter(self.filter_any)
        dialog.set_current_name(DEF_FILENAME)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            logger.debug('New file: ' + dialog.get_filename())
            self.get_sequence_file(dialog.get_filename())
        dialog.destroy()
        
    def get_sequence_file(self, filename):
        with open(filename, 'w') as output_file:
            sequences = []
            for i in range(8):
                sequences.append(self.connector.get_sequence(i))
            output_file.write('\r\n'.join(sequences))

    def set_status_msg(self, msg):
        logger.info(msg)
        if self.main_window:
            self.statusbar.pop(self.context_id)
            self.statusbar.push(self.context_id, msg)

    def set_combo_value(self, combo, value):
        model = combo.get_model()
        active = 0
        found = False
        for item in model:
            if item[1] == value:
                found = True
                break
            active += 1
        if found:
            combo.set_active(active)

    def set_parameter_from_spin(self, param, spin):
        value = spin.get_value_as_int()
        return self.set_parameter_from_interface(param, value)

    def set_parameter_from_combo(self, param, combo):
        value = combo.get_model()[combo.get_active()][1]
        return self.set_parameter_from_interface(param, value)

    def set_parameter_from_switch(self, param, value, switch):
        switch.set_state(value)
        switch.set_active(value)
        return self.set_parameter_from_interface(param, value)

    def set_parameter_from_interface(self, param, value):
        return True if self.configuring else self.connector.set_parameter(param, value)

    def show_about(self):
        self.about_dialog.run()
        self.about_dialog.hide()
        return True

    def quit(self):
        logger.debug('Quitting...')
        self.connector.disconnect()
        self.main_window.hide()
        Gtk.main_quit()
        return True

    def main(self):
        self.init_ui()
        self.connect()
        self.set_ui()
        Gtk.main()

if __name__ == '__main__':
    Editor().main()
