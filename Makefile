TARGET = microdude

PREFIX = $(DESTDIR)/usr/local
BINDIR = $(PREFIX)/bin
ICON_THEME_DIR = /usr/share/icons/hicolor
ICON_DIR = $(ICON_THEME_DIR)/scalable/apps
DESKTOP_FILES_DIR = /usr/share/applications

all: build

build: test
	python3 setup.py bdist_egg

install:
	python3 setup.py install
	install -D res/$(TARGET) $(BINDIR)/$(TARGET)
	install -D res/$(TARGET).svg $(ICON_DIR)
	gtk-update-icon-cache $(ICON_THEME_DIR)
	install -D res/$(TARGET).desktop $(DESKTOP_FILES_DIR)

uninstall:
	rm $(BINDIR)/$(TARGET)
	rm $(ICON_DIR)/$(TARGET).svg
	gtk-update-icon-cache $(ICON_THEME_DIR)
	rm $(DESKTOP_FILES_DIR)/$(TARGET).desktop

test:
	python3 setup.py test

clean:
	python3 setup.py clean --all
	py3clean .
	rm -rf dist $(shell python3 setup.py --name).egg-info
	rm -rf .eggs
	find . -name '*~' | xargs rm -f
