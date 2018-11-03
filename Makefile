.PHONY: all
all: build

PYTHON ?= python3

.PHONY: build
build:
	$(PYTHON) setup.py build

.PHONY: install
install:
	$(PYTHON) setup.py install -O1 $(PYTHON_PREFIX_ARG) --root $(DESTDIR)
	install -d $(DESTDIR)/etc/xdg/autostart
	install -m 0644 system-config/qubes-idleness-monitor.desktop $(DESTDIR)/etc/xdg/autostart/
	install -d $(DESTDIR)/etc/qubes/post-install.d
	install system-config/30-qubes-idle.sh \
		$(DESTDIR)/etc/qubes/post-install.d/30-qubes-idle.sh

clean:
	rm -rf qubesidle/__pycache__
