# Netbox OTP Plugin

Two-factor authentication for [NetBox](https://github.com/netbox-community/netbox). The plugin provides user OTP token verification and OTP device management is provided and bases on [django-otp](https://github.com/django-otp/django-otp) with Time-based One-time Password algorithm.

![alt text](assets/login.png "Login page")

## Compatibility

| NetBox Version| Plugin Version|
|---------------|---------------|
| 4.7           | >= 1.5.0      |
| 4.6           | >= 1.4.0      |
| 4.5.10        | >= 1.4.0      |
| >= 4.1        | >= 1.3.6      |
| 4.0           | >= 1.1.0      |
| 3.X           | 1.0.7         |

NetBox 4.5 and later require Python 3.12 or newer. Plugin releases starting with 1.4.0 target NetBox 4.5.10 and NetBox 4.6.2 or later in the NetBox 4.6 release series. Plugin release 1.5.0 adds support for the NetBox 4.7 release series.


## Installation

The plugin is available as a [Python package](https://pypi.org/project/netbox-otp-plugin/) in pypi and can be installed with pip
```
source /opt/netbox/venv/bin/activate
python -m pip install 'netbox-otp-plugin>=1.5.0'
# or
# python -m pip install netbox-otp-plugin==<version>
```

Enable the plugin in /opt/netbox/netbox/netbox/configuration.py:
```
PLUGINS = ['netbox_otp_plugin']
```

Run migration:
```
./manage.py migrate netbox_otp_plugin
```

To ensure the plugin is automatically re-installed during future upgrades, create a file named `local_requirements.txt` (if not already existing) in the NetBox root directory (alongside `requirements.txt`) and append the `netbox-otp-plugin` package:

```no-highlight
echo netbox-otp-plugin >> local_requirements.txt
```

## Configuration

An OTP device can be attached to a user on your NetBox site or using the command:
```
./manage.py addtotp <username>
```
Then you will see a QR code that you can add to an TOTP authenticator.

To reset user OTP device use the site or the command:
```
./manage.py resettotp <username>
```

The plugin has additional options:
* `otp_required` - if set to True then two-factor authentication will be always required even if a user doesn't have an OTP device yet. False value required to authenticate users only with an OTP device attached only. Default: `True`.
* `issuer` - the issuer parameter for the otpauth URL (see more https://github.com/google/google-authenticator/wiki/Key-Uri-Format). Default: `'Netbox'`.
* `top_level_menu` - if set to True then the plugin menu will be placed at the top level of the menu.

### Example

```
PLUGINS_CONFIG = {
    'netbox_otp_plugin': {
        'otp_required': False,
        'issuer': 'MyOrgNetbox'
    }
}
```

## OTP Self-registration

To allow users to register their devices themselves, you need to grant them the following permissions:

| Objects                   | Actions   | Constraints       |
|---------------------------|-----------|-------------------|
| Otp_Totp > TOTP Device    | view, add | {"user": "$user"} |
| Users > User              | view      | {"pk": "$user"}   |

Note: `otp_required` the plugin options should be set to `False`.

## Known limitations

### Maintenance mode

When `MAINTENANCE_MODE` is enabled, NetBox sets the database session to read-only for every request path that does not start with an entry in `MAINTENANCE_EXEMPT_PATHS`. The login view of this plugin (`/plugins/otp/login/`) must write to the database. NetBox does not give plugins a supported way to add paths to `MAINTENANCE_EXEMPT_PATHS`, and this plugin does not change NetBox settings to do it.

In NetBox 4.7.4 the list contains `LOGIN_REDIRECT_URL` (`/` plus `BASE_PATH`), which matches every request path, so the plugin login works in maintenance mode. If a later NetBox release removes that entry, logins through this plugin can fail while maintenance mode is enabled.

## Screenshots

![alt text](assets/device_list.png "Device list")

![alt text](assets/device_add.png "Add a device")

![alt text](assets/device_edit.png "Edit a device")

## Development

To run the plugin tests from a configured NetBox checkout, install the plugin in editable mode into the NetBox virtual environment, enable it in NetBox configuration, and run:

```shell
cd /path/to/netbox
PYTHONPATH=/path/to/netbox-otp-plugin ./netbox/manage.py check
PYTHONPATH=/path/to/netbox-otp-plugin ./netbox/manage.py test netbox_otp_plugin
```

For compatibility work, run the same checks against NetBox 4.5.10, the latest NetBox 4.6.x release and the latest NetBox 4.7.x release. The local development mirror used for this project is expected at `~/projects/mirror/netbox/netbox`.
