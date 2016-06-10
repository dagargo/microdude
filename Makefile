TARGET = microdude

PREFIX = $(DESTDIR)/usr/local
BINDIR = $(PREFIX)/bin

all: build

build: test
	python3 setup.py bdist_egg

install:
	python3 setup.py install
	install -D res/$(TARGET) $(BINDIR)/$(TARGET)
	install -D res/$(TARGET).svg /usr/share/icons/Humanity/apps/64
	gtk-update-icon-cache /usr/share/icons/Humanity
	install -D res/$(TARGET).desktop /usr/share/applications

uninstall:
	rm $(BINDIR)/$(TARGET)
	rm /usr/share/icons/Humanity/apps/64/$(TARGET).svg
	gtk-update-icon-cache /usr/share/icons/Humanity
	rm /usr/share/applications/$(TARGET).desktop

test:
	python3 setup.py test

clean:
	python3 setup.py clean --all
	py3clean .
	rm -rf dist $(shell python3 setup.py --name).egg-info
	rm -rf .eggs
	find . -name '*~' | xargs rm -f
