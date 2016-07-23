# MicroDude

MicroDude is an editor for Arturia MicroBrute. It offers all the funcionality of Arturia MicroBrute Connection but the firmware upload and the factory patterns reset.

## Installation

The package dependencies for Debian based distributions are:
- python3
- python3-setuptools
- libportmidi-dev
- make
You can easily install them by running `sudo apt-get install python3 python3-setuptools libportmidi-dev make`.

To install MicroDude symply run `make && sudo make install`.

## Known problems

In Ubuntu, the application crashes when sends data to the MicroBrute while the underlying MIDI connection is broken (i.e. the MicroBrute has been switched off or disconnected), which is due to a bug in portmidi. See https://pypi.python.org/pypi/mido/1.1.14 and https://bugs.launchpad.net/ubuntu/+source/portmidi/+bug/890600 for further reference.
