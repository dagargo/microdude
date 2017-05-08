# -*- coding: utf-8 -*-
#
# Copyright 2017 David García Goñi
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
# along with MicroDude. If not, see <http://www.gnu.org/licenses/>.

"""MicroDude user interface"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GLib
import logging
import pkg_resources
from microdude import connector
from microdude.connector import ConnectorError
from microdude import utils
import sys
import getopt

PKG_NAME = 'microdude'

glade_file = pkg_resources.resource_filename(__name__, 'resources/gui.glade')
version = pkg_resources.get_distribution(PKG_NAME).version

EXTENSION = 'mbseq'
DEF_FILENAME = 'sequences.' + EXTENSION
CONN_MSG = 'Connected (firmware version {:s})'
ERROR_IN_SEQ = 'Error in sequence "{:s}"'

log_level = logging.ERROR


def print_help():
    print('Usage: {:s} [-v]'.format(PKG_NAME))

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

builder = Gtk.Builder()
builder.add_from_file(glade_file)

utils.create_config()


class SettingsDialog(object):

    def __init__(self, microdude):
        self.microdude = microdude
        self.dialog = builder.get_object('settings_dialog')
        self.accept = builder.get_object('settings_accept_button')
        self.cancel = builder.get_object('settings_cancel_button')
        self.devices = builder.get_object('device_combo')
        self.device_liststore = builder.get_object('device_liststore')
        self.dialog.set_transient_for(microdude.main_window)
        self.dialog.connect('delete-event', lambda widget,
                            event: widget.hide() or True)
        self.cancel.connect('clicked', lambda widget: self.dialog.hide())
        self.accept.connect('clicked', lambda widget: self.save())

    def show(self):
        self.device_liststore.clear()
        i = 0
        for port in connector.get_ports():
            logger.debug('Adding port {:s}...'.format(port))
            self.device_liststore.append([port])
            if self.microdude.config[utils.DEVICE] == port:
                logger.debug('Port {:s} is active'.format(port))
                self.devices.set_active(i)
            i += 1
        self.dialog.show()

    def save(self):
        active = self.devices.get_active()
        device = self.device_liststore[active][0]
        self.microdude.config[utils.DEVICE] = device
        logger.debug('Configuration: {:s}'.format(str(self.microdude.config)))
        utils.write_config(self.microdude.config)
        self.microdude.ui_reconnect()
        self.dialog.hide()


class Editor(object):
    """MicroDude user interface"""

    def __init__(self):
        self.connector = connector.Connector()
        self.main_window = None
        self.config = utils.read_config()

    def init_ui(self):
        self.main_window = builder.get_object('main_window')
        self.main_window.connect(
            'delete-event', lambda widget, event: self.quit())
        self.main_window.set_position(Gtk.WindowPosition.CENTER)
        self.about_dialog = builder.get_object('about_dialog')
        self.about_dialog.set_position(Gtk.WindowPosition.CENTER)
        self.about_dialog.set_transient_for(self.main_window)
        self.about_dialog.set_version(version)
        self.connect_button = builder.get_object('connect_button')
        self.connect_button.connect(
            'clicked', lambda widget: self.ui_reconnect())
        self.save_button = builder.get_object('save_button')
        self.save_button.connect('clicked', lambda widget: self.show_save())
        self.open_button = builder.get_object('open_button')
        self.open_button.connect('clicked', lambda widget: self.show_open())
        self.about_button = builder.get_object('about_button')
        self.about_button.connect('clicked', lambda widget: self.show_about())
        self.settings_button = builder.get_object('settings_button')
        self.settings_button.connect(
            'clicked', lambda widget: self.settings_dialog.show())
        self.main_container = builder.get_object('main_container')
        self.note_priority = builder.get_object('note_priority')
        self.vel_response = builder.get_object('vel_response')
        self.tx_channel = builder.get_object('tx_channel')
        self.rx_channel = builder.get_object('rx_channel')
        self.play = builder.get_object('play')
        self.retriggering = builder.get_object('retriggering')
        self.next_sequence = builder.get_object('next_sequence')
        self.step_on = builder.get_object('step_on')
        self.step_length = builder.get_object('step_length')
        self.lfo_key_retrigger = builder.get_object('lfo_key_retrigger')
        self.envelope_legato = builder.get_object('envelope_legato')
        self.bend_range = builder.get_object('bend_range')
        self.gate_length = builder.get_object('gate_length')
        self.sync = builder.get_object('sync')
        self.note_priority.connect('changed', lambda widget: self.set_parameter_from_combo(
            connector.NOTE_PRIORITY, widget))
        self.vel_response.connect('changed', lambda widget: self.set_parameter_from_combo(
            connector.VEL_RESPONSE, widget))
        self.tx_channel.connect('changed', lambda widget: self.set_parameter_from_combo(
            connector.TX_CHANNEL, widget))
        self.rx_channel.connect('changed', lambda widget: self.set_parameter_from_combo(
            connector.RX_CHANNEL, widget))
        self.play.connect('changed', lambda widget: self.set_parameter_from_combo(
            connector.PLAY_ON, widget))
        self.retriggering.connect('changed', lambda widget: self.set_parameter_from_combo(
            connector.RETRIGGERING, widget))
        self.next_sequence.connect('changed', lambda widget: self.set_parameter_from_combo(
            connector.NEXT_SEQUENCE, widget))
        self.step_on.connect('changed', lambda widget: self.set_parameter_from_combo(
            connector.STEP_ON, widget))
        self.step_length.connect('changed', lambda widget: self.set_parameter_from_combo(
            connector.STEP_LENGTH, widget))
        self.lfo_key_retrigger.connect(
            'state-set', lambda widget, state: self.set_parameter_from_switch(connector.LFO_KEY_RETRIGGER, state, widget))
        self.envelope_legato.connect(
            'state-set', lambda widget, state: self.set_parameter_from_switch(connector.ENVELOPE_LEGATO, state, widget))
        self.bend_range.connect(
            'value-changed', lambda widget: self.set_parameter_from_spin(connector.BEND_RANGE, widget))
        self.gate_length.connect('changed', lambda widget: self.set_parameter_from_combo(
            connector.GATE_LENGTH, widget))
        self.sync.connect('changed', lambda widget: self.set_parameter_from_combo(
            connector.SYNC, widget))
        self.statusbar = builder.get_object('statusbar')
        self.context_id = self.statusbar.get_context_id(PKG_NAME)
        self.settings_dialog = SettingsDialog(self)

        self.filter_mbseq = Gtk.FileFilter()
        self.filter_mbseq.set_name('MicroBrute sequence files')
        self.filter_mbseq.add_pattern('*.' + EXTENSION)

        self.filter_any = Gtk.FileFilter()
        self.filter_any.set_name('Any files')
        self.filter_any.add_pattern('*')

        self.main_window.present()

    def connect(self):
        device = self.config[utils.DEVICE]
        self.connector.connect(device)
        if self.connector.connected():
            conn_msg = CONN_MSG.format(self.connector.sw_version)
            self.set_status_msg(conn_msg)
        else:
            self.set_status_msg('Not connected')

    def ui_reconnect(self):
        self.connector.disconnect()
        self.connect()
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

    def update_sensitivity(self):
        self.main_container.set_sensitive(self.connector.connected())
        self.save_button.set_sensitive(self.connector.connected())
        self.open_button.set_sensitive(self.connector.connected())

    def show_open(self):
        dialog = Gtk.FileChooserDialog('Open', self.main_window,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.add_filter(self.filter_mbseq)
        dialog.add_filter(self.filter_any)

        response = dialog.run()
        filename = dialog.get_filename()
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            logger.debug('Opening sequences from {:s}...'.format(filename))
            self.open_sequence_file(filename)

    def open_sequence_file(self, filename):
        with open(filename, 'r') as input_file:
            try:
                for line in input_file:
                    seq = line.rstrip('\n')
                    logger.debug('Processing sequence "{:s}"'.format(seq))
                    try:
                        self.connector.set_sequence(seq)
                    except ValueError as e:
                        desc = ERROR_IN_SEQ.format(seq)
                        self.show_error(e, desc=desc)
            except ConnectorError as e:
                self.show_error(e)
                self.ui_reconnect()

    def show_save(self):
        dialog = Gtk.FileChooserDialog('Save as', self.main_window,
                                       Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        Gtk.FileChooser.set_do_overwrite_confirmation(dialog, True)
        dialog.add_filter(self.filter_mbseq)
        dialog.add_filter(self.filter_any)
        dialog.set_current_name(DEF_FILENAME)

        response = dialog.run()
        filename = dialog.get_filename()
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            logger.debug('Saving sequences to {:s}...'.format(filename))
            self.save_sequence_file(filename)

    def save_sequence_file(self, filename):
        try:
            sequences = []
            for i in range(8):
                sequences.append(self.connector.get_sequence(i))
            with open(filename, 'w') as output_file:
                output_file.write('\r\n'.join(sequences))
        except ConnectorError as e:
            self.show_error(e)
            self.ui_reconnect()

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
        self.set_parameter_from_interface(param, value)

    def set_parameter_from_combo(self, param, combo):
        value = combo.get_model()[combo.get_active()][1]
        self.set_parameter_from_interface(param, value)

    def set_parameter_from_switch(self, param, value, switch):
        switch.set_state(value)
        switch.set_active(value)
        self.set_parameter_from_interface(param, value)

    def set_parameter_from_interface(self, param, value):
        if not self.configuring:
            try:
                value = self.connector.set_parameter(param, value)
            except ConnectorError as e:
                value = False
                self.show_error(e)
                self.ui_reconnect()

    def show_error(self, exception, desc=None):
        msg = str(exception)
        dialog = Gtk.MessageDialog(self.main_window,
                                   flags=Gtk.DialogFlags.MODAL,
                                   type=Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.OK,
                                   message_format=msg)
        dialog.connect(
            'response', lambda widget, response: widget.destroy())
        if desc != None:
            dialog.format_secondary_text(desc)
        dialog.run()

    def show_about(self):
        self.about_dialog.run()
        self.about_dialog.hide()

    def quit(self):
        logger.debug('Quitting...')
        self.connector.disconnect()
        self.main_window.hide()
        Gtk.main_quit()

    def main(self):
        self.init_ui()
        self.connect()
        self.set_ui()
        Gtk.main()
