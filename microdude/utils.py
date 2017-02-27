# -*- coding: utf-8 -*-
#
# Copyright 2016 David García Goñi
#
# This file is part of Phatty.
#
# Phatty is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Phatty is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Phatty. If not, see <http://www.gnu.org/licenses/>.

"""MicroDude utils"""

from microdude import connector
import json
from os import makedirs
from os.path import expanduser
from os.path import exists
import logging

logger = logging.getLogger(__name__)

APP_NAME = 'microdude'
READ_ERROR_MSG = 'Config file could not be read: {:s}. Using default configuration...'
OPEN_ERROR_MSG = 'Config file could not be opened: {:s}.'
CREATE_ERROR_MSG = 'Config file could not be created {:s}.'
DEVICE = 'device'
DEFAULT_CONFIG = {DEVICE: ''}

CONFIG_DIR = expanduser('~') + '/.' + APP_NAME
CONFIG_FILE = CONFIG_DIR + '/config'


def create_config():
    if not exists(CONFIG_DIR):
        logger.debug('Writing config dir...')
        try:
            makedirs(CONFIG_DIR)
        except IOError as e:
            logger.error(CREATE_ERROR_MSG.format(e))

    if not exists(CONFIG_FILE):
        logger.debug('Writing config file...')
        with open(CONFIG_FILE, 'w') as file:
            try:
                file.write(json.dumps(DEFAULT_CONFIG))
            except IOError as e:
                logger.error(CREATE_ERROR_MSG.format(e))


def read_config():
    logger.debug('Reading config file...')
    try:
        file = open(CONFIG_FILE, 'r')
    except IOError as e:
        logger.error(OPEN_ERROR_MSG.format(str(e)))
        return DEFAULT_CONFIG
    else:
        try:
            config = json.loads(file.read())
        except (IOError, ValueError) as e:
            logger.error(READ_ERROR_MSG.format(str(e)))
        else:
            logger.debug('Config file read.')
        file.close()
        return config


def write_config(config):
    logger.debug('Writing config file...')
    with open(CONFIG_FILE, 'w') as file:
        try:
            file.write(json.dumps(config))
            logger.debug('Config file written.')
        except IOError as e:
            logger.error(
                'File could not be written: {:s}. Skipping...'.format(str(e)))
