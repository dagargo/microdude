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

"""MicroDude connector"""

import mido
import time
import logging

logger = logging.getLogger(__name__)

mido.set_backend('mido.backends.portmidi')
logger.debug('Mido backend: {:s}'.format(str(mido.backend)))

INIT_MSG = [0x7E, 0x7F, 0x6, 0x1]
MICROBRUTE_MSG_WO_VERSION = [0x7E, 0x1, 0x6,
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

RECEIVE_RETRIES = 50
RETRY_SLEEP_TIME = 0.1

SEQ_FILE_ERROR = 'Error in sequences file'
HANDSHAKE_MSG = 'Handshake ok. Version {:s}.'
SENDING_MSG = 'Sending message {:s}...'
RECEIVING_MSG = 'Receiving message {:s}...'


def get_ports():
    return mido.get_ioport_names()


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
        logger.debug('Connecting...')
        try:
            self.port = mido.open_ioport(device)
            logger.debug('Handshaking...')
            self.tx_message(INIT_MSG)
            response = self.rx_message()
            if response[0:11] == MICROBRUTE_MSG_WO_VERSION:
                self.sw_version = '.'.join([str(i) for i in response[11:15]])
                logger.debug(HANDSHAKE_MSG.format(self.sw_version))
            else:
                logger.debug('Bad handshake. Disconnecting...')
                self.disconnect()
        except IOError as e:
            logger.error('IOError while connecting: "{:s}"'.format(str(e)))
            self.disconnect()

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
        """Return an array representing the sysex messages to get the given parameter in Arturia's format."""
        message = []
        message.extend(TX_MSG)
        message.append(self.seq)
        message.append(0)
        message.append(param + 1)
        return message

    def set_parameter(self, param, value):
        msg = self.create_set_parameter_message(param, value)
        self.tx_message(msg)
        self.seq_inc()
        return True

    def create_set_parameter_message(self, param, value):
        """Return an array representing the sysex messages to set the given parameter and value in Arturia's format."""
        msg = []
        msg.extend(TX_MSG)
        msg.append(self.seq)
        msg.append(1)
        msg.append(param)
        msg.append(value)
        return msg

    def tx_message(self, data):
        msg = mido.Message('sysex', data=data)
        logger.debug(SENDING_MSG.format(self.get_hex_data(data)))
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
                        logger.debug('Receiving message {:s}...'.format(
                            self.get_hex_data(msg.data)))
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
        return ', '.join([hex(i) for i in data])

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


class ConnectorError(IOError):
    """Raise when there is a Connector error"""

    def __init__(self):
        super(ConnectorError, self).__init__('Connection error')
