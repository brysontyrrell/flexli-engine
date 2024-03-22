from src.layers.layer.conditions import ConditionEvaluator


def test_single_number_criteria():
    data = {
        "criteria": [
            {
                "attributes": [
                    {
                        "type": "Number",
                        "attribute": "::general.id",
                        "operator": "eq",
                        "value": 1,
                    }
                ]
            }
        ]
    }
    cond = ConditionEvaluator(data)
    assert cond.evaluate(JAMF_COMPUTER_EXAMPLE) is True


def test_nested_multi_string_criteria():
    data = {
        "criteria": [
            {
                "attributes": [
                    {
                        "type": "String",
                        "attribute": "::hardware.storage[].device[].partition[?name=='Macintosh HD'].filevault_status | []",
                        "operator": "eq",
                        "value": "Encrypted",
                    },
                    {
                        "type": "String",
                        "attribute": "::hardware.storage[].device[].partition[?name=='Macintosh HD'].filevault2_status | []",
                        "operator": "eq",
                        "value": "Encrypted",
                    },
                ]
            }
        ]
    }
    cond = ConditionEvaluator(data)
    assert cond.evaluate(JAMF_COMPUTER_EXAMPLE) is True


def test_single_date_criteria_before():
    data = {
        "criteria": [
            {
                "attributes": [
                    {
                        "type": "Date",
                        "attribute": "::general.last_contact_time_utc",
                        "operator": "before",
                        "value": "2018-07-08T00:00:00Z",
                    }
                ]
            }
        ]
    }
    cond = ConditionEvaluator(data)
    assert cond.evaluate(JAMF_COMPUTER_EXAMPLE) is True


def test_single_date_criteria_after():
    data = {
        "criteria": [
            {
                "attributes": [
                    {
                        "type": "Date",
                        "attribute": "::general.last_contact_time_utc",
                        "operator": "after",
                        "value": "2016-07-07T00:00:00Z",
                    }
                ]
            }
        ]
    }
    cond = ConditionEvaluator(data)
    assert cond.evaluate(JAMF_COMPUTER_EXAMPLE) is True


def test_value_expression():
    source = {"foo": 1, "bar": {"baz": 1}}
    data = {
        "criteria": [
            {
                "attributes": [
                    {
                        "type": "Number",
                        "attribute": "::foo",
                        "operator": "eq",
                        "value": "::bar.baz",
                    }
                ]
            }
        ]
    }
    cond = ConditionEvaluator(data)
    assert cond.evaluate(source) is True


JAMF_COMPUTER_EXAMPLE = {
    "general": {
        "id": 1,
        "name": "Admins iMac",
        "mac_address": "E0:AC:CB:97:36:G4",
        "network_adapter_type": "Ethernet",
        "alt_mac_address": "E0:AC:CB:97:36:G4",
        "alt_network_adapter_type": "IEEE80211",
        "ip_address": "10.1.1.1",
        "last_reported_ip": "192.0.0.1",
        "serial_number": "C02Q7KHTGFWF",
        "udid": "55900BDC-347C-58B1-D249-F32244B11D30",
        "jamf_version": "9.99.0-t1494340586",
        "platform": "Mac",
        "barcode_1": "string",
        "barcode_2": "string",
        "asset_tag": "string",
        "remote_management": {"managed": True, "management_username": "casperadmin"},
        "mdm_capable": True,
        "mdm_capable_users": {"mdm_capable_user": "string"},
        "management_status": {
            "enrolled_via_dep": True,
            "user_approved_enrollment": True,
            "user_approved_mdm": True,
        },
        "report_date": {},
        "report_date_epoch": 1499470624555,
        "report_date_utc": "2017-07-07T18:37:04.555-0500",
        "last_contact_time": {},
        "last_contact_time_epoch": 1499470624555,
        "last_contact_time_utc": "2017-07-07T18:37:04.555-0500",
        "initial_entry_date": {},
        "initial_entry_date_epoch": 1499470624555,
        "initial_entry_date_utc": "2017-07-07T18:37:04.555-0500",
        "last_cloud_backup_date_epoch": 1499470624555,
        "last_cloud_backup_date_utc": "2017-07-07T18:37:04.555-0500",
        "last_enrolled_date_epoch": 1499470624555,
        "last_enrolled_date_utc": "2017-07-07T18:37:04.555-0500",
        "distribution_point": "string",
        "sus": "string",
        "netboot_server": "string",
        "site": {"id": 0, "name": "None"},
        "itunes_store_account_is_active": True,
    },
    "location": {
        "username": "JBetty",
        "realname": "Betty Jackson",
        "real_name": "Betty Jackson",
        "email_address": "jbetty@company.com",
        "position": "Systems Engineer",
        "phone": "123-555-6789",
        "phone_number": "123-555-6789",
        "department": "Sales Staff",
        "building": "New York Office",
        "room": 1159,
    },
    "purchasing": {
        "is_purchased": True,
        "is_leased": True,
        "po_number": "string",
        "vendor": "string",
        "applecare_id": "string",
        "purchase_price": "string",
        "purchasing_account": "string",
        "po_date": "string",
        "po_date_epoch": 0,
        "po_date_utc": "string",
        "warranty_expires": "string",
        "warranty_expires_epoch": 0,
        "warranty_expires_utc": "string",
        "lease_expires": "string",
        "lease_expires_epoch": 0,
        "lease_expires_utc": "string",
        "life_expectancy": 0,
        "purchasing_contact": "string",
    },
    "hardware": {
        "make": "Apple",
        "model": "13-inch Retina MacBook Pro (Late 2013)",
        "model_identifier": "MacBookPro11,1",
        "os_name": "Mac OS X",
        "os_version": "10.13.2",
        "os_build": "17C88",
        "master_password_set": True,
        "active_directory_status": "AD.company.com",
        "service_pack": "string",
        "processor_type": "Intel Core i5",
        "processor_architechture": "x86_64",
        "processor_speed": 2600,
        "processor_speed_mhz": 2600,
        "number_processors": 1,
        "number_cores": 2,
        "total_ram": 16384,
        "total_ram_mb": 16384,
        "boot_rom": "MBP111.0142.B00",
        "bus_speed": 0,
        "bus_speed_mhz": 0,
        "battery_capacity": 90,
        "cache_size": 3072,
        "cache_size_kb": 3072,
        "available_ram_slots": 0,
        "optical_drive": "string",
        "nic_speed": "n/a",
        "smc_version": "2.16f68",
        "ble_capable": True,
        "sip_status": "Enabled",
        "gatekeeper_status": "App Store and identified developers",
        "xprotect_version": 2098,
        "institutional_recovery_key": "Not Present",
        "disk_encryption_configuration": "Individual and Institutional Encryption",
        "filevault_2_users": [{"user": "admin"}],
        "storage": [
            {
                "device": {
                    "disk": "disk0",
                    "model": "Apple SSD SM0512F",
                    "revision": "UXM2JA1Q",
                    "serial_number": "S1K5NYADC12934",
                    "size": 512287,
                    "drive_capacity_mb": 512287,
                    "connection_type": "NO",
                    "smart_status": "Verified",
                    "partition": [
                        {
                            "name": "Macintosh HD",
                            "size": 94128,
                            "type": "boot",
                            "partition_capacity_mb": 94128,
                            "percentage_full": 17,
                            "filevault_status": "Encrypted",
                            "filevault_percent": 100,
                            "filevault2_status": "Encrypted",
                            "filevault2_percent": 100,
                            "boot_drive_available_mb": 425198,
                            "lvgUUID": "string",
                            "lvUUID": "string",
                            "pvUUID": "string",
                        }
                    ],
                }
            }
        ],
        "mapped_printers": [
            {
                "printer": {
                    "name": "2nd Floor HP",
                    "uri": "lpd://10.11.182.21/",
                    "type": "HP LaserJet 500 color MFP M575",
                    "location": "2nd Floor / Stairwell",
                }
            }
        ],
    },
    "certificates": [
        {
            "certificate": {
                "common_name": "JSS Built-in Certificate Authority",
                "identify": False,
                "expires_utc": "2024-03-02T02:12:49.000+0000",
                "expires": 1709345569000,
                "name": "string",
            }
        }
    ],
    "software": {
        "unix_executables": "string",
        "licensed_software": [{"name": "Adobe CS5"}],
        "installed_by_casper": [{"package": "FireFox.pkg"}],
        "installed_by_installer_swu": [{"package": "com.apple.pkg.iTunesX"}],
        "cached_by_casper": [{"package": "GoogleChrome.pkg"}],
        "available_software_updates": [{"name": "iTunesXPatch-12.7.3"}],
        "available_updates": [
            {
                "update": {
                    "name": "iTunes",
                    "package_name": "iTunesXPatch-12.7.3",
                    "version": "12.7.3",
                }
            }
        ],
        "running_services": [{"name": "com.apple.airportd"}],
        "applications": [
            {
                "size": 1,
                "application": {
                    "name": "Activity Monitor.app",
                    "path": "/Applications/Utilities/Activity Monitor.app",
                    "version": 10.13,
                },
            }
        ],
        "fonts": [
            {
                "size": 1,
                "font": {
                    "name": "Al Nile.ttc",
                    "path": "/Library/Fonts/Al Nile.ttc",
                    "version": "n/a",
                },
            }
        ],
        "plugins": [
            {
                "size": 1,
                "plugin": {
                    "name": "QuickTime Plugin.plugin",
                    "path": "/Library/Internet Plug-Ins/Disabled Plug-Ins/QuickTime Plugin.plugin",
                    "version": "7.7.3",
                },
            }
        ],
    },
    "extension_attributes": [
        {
            "extension_attribute": {
                "id": 1,
                "name": "Battery Cycle Count",
                "type": "String",
                "value": 191,
            }
        }
    ],
    "groups_accounts": {
        "computer_group_memberships": [{"group": "All Managed Clients"}],
        "local_accounts": [
            {
                "user": {
                    "name": "_amavisd",
                    "realname": "AMaViS Daemon",
                    "uid": 83,
                    "home": "/var/virusmails",
                    "home_size": "-1MB",
                    "home_size_mb": -1,
                    "administrator": False,
                    "filevault_enabled": False,
                }
            }
        ],
    },
    "configuration_profiles": [
        {
            "size": 1,
            "configuration_profile": {
                "id": 1,
                "name": "string",
                "uuid": "string",
                "is_removable": False,
            },
        }
    ],
}
