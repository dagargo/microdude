# -*- coding: utf-8 -*-
#
# Copyright 2018 David García Goñi
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

"""MicroDude connector"""

import mido
import time
import logging
import importlib.util
from mido import Message

logger = logging.getLogger(__name__)

spec = importlib.util.find_spec('rtmidi')
if spec:
    backend = 'mido.backends.rtmidi'
else:
    backend = 'mido.backends.portmidi'

mido.set_backend(backend)

INQUIRY_REQ = [0x7E, 0x7F, 0x6, 0x1]
INQUIRY_RES_WO_VERSION = [0x7E, 0x1, 0x6,
                             0x2, 0x0, 0x20, 0x6B, 0x4, 0x0, 0x2, 0x1]
TX_MSG = [0x0, 0x20, 0x6B, 0x5, 0x1]

RX_CHANNEL = 0x5
TX_CHANNEL = 0x7
NOTE_PRIORITY = 0xB
ENVELOPE_LEGATO = 0xD
LFO_KEY_RETRIGGER = 0xF
VEL_RESPONSE = 0x11
STEP_ON = 0x2A
BEND_RANGE = 0x2C
PLAY_ON = 0x2E
NEXT_SEQUENCE = 0x32
RETRIGGERING = 0x34
GATE_LENGTH = 0x36
STEP_LENGTH = 0x38
SYNC = 0x3C
CALIB_PB_CENTER = 0x21
CALIB_BOTH_BOTTOM = 0x22
CALIB_BOTH_TOP = 0x23
CALIB_END = 0x24

CTL_RX_CHANNEL = 102
CTL_TX_CHANNEL = 103
CTL_NOTE_PRIORITY = 111
CTL_ENVELOPE_LEGATO = 109
CTL_LFO_KEY_RETRIGGER = 110
CTL_VEL_RESPONSE = 112
CTL_STEP_ON = 114
CTL_PLAY_ON = 105
CTL_NEXT_SEQUENCE = 106
CTL_RETRIGGERING = 104
CTL_GATE_LENGTH = 113
CTL_STEP_LENGTH = 107
CTL_SYNC = 108

def map_plus_one(value):
    return value + 1

def map_proportional_3(value):
    return value * 42

def map_proportional_2(value):
    return value * 64

def map_plus_1_proportional_4(value):
    return (value - 1) * 30

def map_step_length(value):
    if value == 4:
        return 0
    elif value == 8:
        return 30
    elif value == 16:
        return 60
    elif value == 32:
        return 90

def map_special(value):
    if value == 0:
        return 0
    elif value == 1:
        return 43
    elif value == 2:
        return 87

PARAM_CTL_MAPPING = {
    RX_CHANNEL: {
        'ctl': CTL_RX_CHANNEL,
        'map': map_plus_one
    },
    TX_CHANNEL: {
        'ctl': CTL_TX_CHANNEL,
        'map': map_plus_one
    },
    NOTE_PRIORITY: {
        'ctl': CTL_NOTE_PRIORITY,
        'map': map_special
    },
    ENVELOPE_LEGATO: {
        'ctl': CTL_ENVELOPE_LEGATO,
        'map': map_proportional_2
    },
    LFO_KEY_RETRIGGER: {
        'ctl': CTL_LFO_KEY_RETRIGGER,
        'map': map_proportional_2
    },
    VEL_RESPONSE: {
        'ctl': CTL_VEL_RESPONSE,
        'map': map_special
    },
    STEP_ON: {
        'ctl': CTL_STEP_ON,
        'map': map_proportional_2
    },
    PLAY_ON: {
        'ctl': CTL_PLAY_ON,
        'map': map_proportional_2
    },
    NEXT_SEQUENCE: {
        'ctl': CTL_NEXT_SEQUENCE,
        'map': map_special
    },
    RETRIGGERING: {
        'ctl': CTL_RETRIGGERING,
        'map': map_special
    },
    GATE_LENGTH: {
        'ctl': CTL_GATE_LENGTH,
        'map': map_proportional_3
    },
    STEP_LENGTH: {
        'ctl': CTL_STEP_LENGTH,
        'map': map_step_length
    },
    SYNC: {
        'ctl': CTL_SYNC,
        'map': map_special
    }
}

RECEIVE_RETRIES = 50
RETRY_SLEEP_TIME = 0.1

SEQ_FILE_ERROR = 'Error in sequences file'


def get_ports():
    filtered = []
    for p in mido.get_ioport_names():
        if 'MicroBrute' in p:
            filtered.append(p)
    return filtered

class Connector(object):
    """MicroDude connector"""

    def __init__(self):
        logger.debug('Initializing...')
        self.port = None
        self.seq = 0
        self.sw_version = None

    def seq_inc(self):
        self.seq += 1
        if self.seq == 0x80:
            self.seq = 0

    def connected(self):
        return self.port != None

    def disconnect(self):
        """Disconnect from the MicroBrute."""
        if self.port:
            logger.debug('Disconnecting...')
            try:
                self.port.close()
            except IOError:
                logger.error('IOError while disconnecting')
            self.port = None

    def connect(self, device):
        """Connect to the MicroBrute."""
        logger.debug('Connecting to %s...', device)
        try:
            self.port = mido.open_ioport(device)
            logger.debug('Mido backend: %s', str(mido.backend))
            logger.debug('Handshaking...')
            self.tx_message(INQUIRY_REQ)
            response = self.rx_message()
            if response[0:11] == INQUIRY_RES_WO_VERSION:
                self.sw_version = '.'.join([str(i) for i in response[11:15]])
                logger.debug('Handshake ok. Version %s.', self.sw_version)
                self.set_channel(self.get_parameter(RX_CHANNEL))
            else:
                logger.debug('Bad handshake. Disconnecting...')
                self.disconnect()
        except IOError as e:
            logger.error('IOError while connecting: "%s"', str(e))
            self.disconnect()

    def set_channel(self, channel):
        self.channel = channel if channel < 16 else 0

    def set_sequence(self, sequence):
        """Set the sequence in Arturia's format in the MicroBrute."""
        msgs = self.create_set_sequence_messages(sequence)
        for msg in msgs:
            self.tx_message(msg)

    def get_sequence(self, seq_id):
        """Return the sequence in Arturia's format set in the MicroBrute for the given seq_id."""
        sequence = []
        sequence.extend(self.get_sequence_fragment(seq_id, 0))
        sequence.extend(self.get_sequence_fragment(seq_id, 0x20))
        return self.get_sequence_string(seq_id, sequence)

    def get_sequence_string(self, seq_id, sequence):
        notes = []
        for note in sequence:
            if note == 0:
                break
            notes.append('x' if note == 0x7F else str(note))
        return '{:d}:{:s}'.format(seq_id + 1, ' '.join(notes))

    def get_sequence_fragment(self, seq_id, offset):
        request = self.create_get_sequence_message(seq_id, offset)
        self.tx_message(request)
        response = self.rx_message()

        # Checking some bytes and getting the value
        if response[5] != self.seq:
            logger.warn('Bad sequence number byte')
        if response[6] != 0x23:
            logger.warn('Bad client byte')
        if response[7] != 0x3A:
            logger.warn('Bad client byte')
        if response[8] != seq_id:
            logger.warn('Bad sequence id byte')
        if response[9] != offset:
            logger.warn('Bad offset byte')
        if response[10] != 0x20:
            logger.warn('Bad length byte')

        self.seq_inc()
        return response[11:43]

    def get_parameter(self, param):
        request = self.create_get_parameter_message(param)
        self.tx_message(request)
        response = self.rx_message()

        # Checking some bytes and getting the value
        if response[5] != self.seq:
            logger.warn('Bad sequence number byte')
        if response[6] != 1:
            logger.warn('Bad client byte')
        if response[7] != param:
            logger.warn('Bad parameter byte')

        self.seq_inc()

        return response[8]

    def create_get_parameter_message(self, param):
        """Return an array representing the SysEx message to get the given parameter in Arturia's format."""
        message = []
        message.extend(TX_MSG)
        message.append(self.seq)
        message.append(0)
        message.append(param + 1)
        return message

    def set_parameter(self, param, value, persistent=True):
        if persistent:
            msg = self.create_set_parameter_message(param, value)
            self.tx_message(msg)
            self.seq_inc()
        else:
            msgs = self.get_ctl_msgs(param, value)
            try:
                for m in msgs:
                    logger.debug('Sending message %s', str(m))
                    self.port.send(m)
            except IOError:
                self.disconnect()
                raise ConnectorError()
        if param == RX_CHANNEL:
            self.set_channel(value)
        return True

    def create_set_parameter_message(self, param, value):
        """Return an array representing the SysEx message to set the given parameter and value in Arturia's format."""
        msg = []
        msg.extend(TX_MSG)
        msg.append(self.seq)
        msg.append(1)
        msg.append(param)
        msg.append(value)
        return msg

    def tx_message(self, data):
        msg = mido.Message('sysex', data=data)
        logger.debug('Sending message %s...', self.get_hex_data(data))
        try:
            self.port.send(msg)
        except IOError:
            self.disconnect()
            raise ConnectorError()

    def rx_message(self):
        try:
            for i in range(0, RECEIVE_RETRIES):
                for msg in self.port.iter_pending():
                    if msg.type == 'sysex':
                        logger.debug('Receiving message %s...',
                            self.get_hex_data(msg.data))
                        data_array = []
                        data_array.extend(msg.data)
                        return data_array
                time.sleep(RETRY_SLEEP_TIME)
        except IOError:
            self.disconnect()
            raise ConnectorError()
        self.disconnect()
        raise ConnectorError()

    def get_hex_data(self, data):
        return ' '.join([f'{i:02x}' for i in data])

    def create_set_sequence_messages(self, sequence):
        """Return an array representing the sysex messages for the given sequence in Arturia's format."""
        msgs = []
        aux = sequence.split(':')
        if not len(aux[0]) or not len(aux[1]):
            raise ValueError(SEQ_FILE_ERROR)
        try:
            seq_id = int(aux[0][0]) - 1
            steps = aux[1].split(' ')
            msgs.append(self.create_set_sequence_message(
                seq_id, 0, steps[0:0x20]))
            if len(steps) > 32:
                msgs.append(self.create_set_sequence_message(
                    seq_id, 0x20, steps[0x20:0x40]))
            return msgs
        except ValueError:
            raise ValueError(SEQ_FILE_ERROR)

    def create_set_sequence_message(self, seq_id, offset, steps):
        msg = []
        msg.extend(TX_MSG)
        msg.append(self.seq)
        msg.append(0x23)
        msg.append(0x3A)
        msg.append(seq_id)
        msg.append(offset)
        msg.append(len(steps))
        for step in steps:
            msg.append(0x7F if step == 'x' else int(step))
        for step in range(len(steps), 0x20):
            msg.append(0x00)
        self.seq_inc()
        return msg

    def create_get_sequence_message(self, seq_id, offset):
        """Return the sysex messages to request a sequence for the given seq_id from the given offset."""
        msg = []
        msg.extend(TX_MSG)
        msg.append(self.seq)
        msg.append(0x03)
        msg.append(0x3B)
        msg.append(seq_id)
        msg.append(offset)
        msg.append(0x20)
        return msg

    def get_ctl_msgs(self, param, value):
        if param == BEND_RANGE:
            return [
                Message('control_change', channel=self.channel,
                        control=101, value=0),
                Message('control_change', channel=self.channel,
                        control=100, value=0),
                Message('control_change', channel=self.channel,
                        control=6, value=value),
                Message('control_change', channel=self.channel,
                        control=38, value=0)
            ]
        else:
            ctl = PARAM_CTL_MAPPING[param]['ctl']
            val = PARAM_CTL_MAPPING[param]['map'](value)
            return [Message('control_change', channel=self.channel,
                          control=ctl, value=val)]

class ConnectorError(IOError):
    """Raise when there is a Connector error"""

    def __init__(self):
        super(ConnectorError, self).__init__('Connection error')
