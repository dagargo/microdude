MicroDude
=========

MicroDude is an editor for Arturia MicroBrute. It offers all the funcionality of Arturia MicroBrute Connection but the firmware upload and the factory patterns reset.

Installation
------------

The package dependencies for Ubuntu are:
- python3
- libportmidi-dev

To install symply run `make && sudo make install`.

Known problems
--------------

The application crashes when sends data to the MicroBrute while the underlying MIDI connection is broken (i.e. the MicroBrute has been switched off or disconnected). This is due to a bug of portmidi in Ubuntu. See https://pypi.python.org/pypi/mido/1.1.14 and https://bugs.launchpad.net/ubuntu/+source/portmidi/+bug/890600 for further reference.
