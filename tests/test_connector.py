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

import unittest
import microdude
from microdude.connector import Connector

SYSEX_SEQUENCE_FRAGMENT1 = [0x00, 0x20, 0x6B, 0x05, 0x01, 0x47, 0x23, 0x3A, 0x01, 0x00, 0x20, 0x28, 0x34, 0x40, 0x4C, 0x40, 0x34, 0x2C, 0x38, 0x44, 0x50, 0x44, 0x38, 0x32, 0x3E, 0x4A, 0x56, 0x4A, 0x3E, 0x34, 0x40, 0x4C, 0x58, 0x4C, 0x40, 0x30, 0x3C, 0x48, 0x54, 0x48, 0x3C, 0x37, 0x43]
SYSEX_SEQUENCE_FRAGMENT2 = [0x00, 0x20, 0x6B, 0x05, 0x01, 0x48, 0x23, 0x3A, 0x01, 0x20, 0x10, 0x4F, 0x5B, 0x4F, 0x43, 0x36, 0x42, 0x4E, 0x5A, 0x4E, 0x42, 0x2D, 0x39, 0x45, 0x51, 0x45, 0x39, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
SYSEX_SEQUENCE_FRAGMENTS = [ SYSEX_SEQUENCE_FRAGMENT1, SYSEX_SEQUENCE_FRAGMENT2]

SYSEX_SEQUENCE = []
SYSEX_SEQUENCE.extend(SYSEX_SEQUENCE_FRAGMENT1[11:43])
SYSEX_SEQUENCE.extend(SYSEX_SEQUENCE_FRAGMENT2[11:43])

STRING_SEQUENCE = '2:40 52 64 76 64 52 44 56 68 80 68 56 50 62 74 86 74 62 52 64 76 88 76 64 48 60 72 84 72 60 55 67 79 91 79 67 54 66 78 90 78 66 45 57 69 81 69 57'

SYSEX_SEQUENCE_FRAGMENT3 = [ 0x0, 0x20, 0x6B, 0x5, 0x1, 7, 0x23, 0x3A, 4, 0x00, 8, 48, 48, 0x7F, 48, 48, 48, 60, 48, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ]

SYSEX_GET_MESSAGE = [0x0, 0x20, 0x6B, 0x5, 0x1, 0x0, 0x0, 0x6 ]
SYSEX_SET_MESSAGE = [0x0, 0x20, 0x6B, 0x5, 0x1, 0x1, 0x1, 0xB, 0x0 ]

class TestUBEditor(unittest.TestCase):

    def setUp(self):
        self.connector = Connector()

    def test_create_set_sequence_message(self):
        self.connector.seq = 7
        actual = self.connector.create_set_sequence_message(4, False, [ 48, 48, 'x', 48, 48, 48, 60, 48 ])
        self.assertTrue(actual == SYSEX_SEQUENCE_FRAGMENT3)

    def test_create_set_sequence_messages(self):
        self.connector.seq = 71
        actual = self.connector.create_set_sequence_messages(STRING_SEQUENCE)
        self.assertTrue(actual == SYSEX_SEQUENCE_FRAGMENTS)

    def test_create_get_sequence_message(self):
        self.connector.seq = 0x2B
        actual = self.connector.create_get_sequence_message(4, 0x20)
        expected = [ 0x00, 0x20, 0x6B, 0x05, 0x01, 0x2B, 0x03, 0x3B, 0x04, 0x20, 0x20]
        self.assertTrue(actual == expected)

    def test_get_sequence_string(self):
        actual = self.connector.get_sequence_string(1, SYSEX_SEQUENCE)
        self.assertTrue(actual == STRING_SEQUENCE)

    def test_seq_inc(self):
        self.connector.seq_inc()
        self.assertTrue(self.connector.seq == 1)
        self.connector.seq = 0x7F
        self.connector.seq_inc()
        self.assertTrue(self.connector.seq == 0)
        
    def test_create_get_parameter_message(self):
        actual = self.connector.create_get_parameter_message(microdude.connector.RX_CHANNEL)
        self.assertTrue(actual == SYSEX_GET_MESSAGE)

    def test_create_set_parameter_message(self):
        self.connector.seq = 0x1
        actual = self.connector.create_set_parameter_message(microdude.connector.NOTE_PRIORITY, 0)
        self.assertTrue(actual == SYSEX_SET_MESSAGE)

if __name__ == '__main__':
    unittest.main()
