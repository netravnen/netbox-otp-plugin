clean:
	rm -rf build
	rm -rf dist

NETBOX_DIR ?= $(HOME)/projects/mirror/netbox/netbox
NETBOX_PYTHON ?= python

check:
	cd $(NETBOX_DIR) && PYTHONPATH=$(CURDIR) $(NETBOX_PYTHON) netbox/manage.py check

test:
	cd $(NETBOX_DIR) && PYTHONPATH=$(CURDIR) $(NETBOX_PYTHON) netbox/manage.py test netbox_otp_plugin

wheel:
	python3 -m build -w

build: clean wheel

upload:
	twine upload --skip-existing dist/*