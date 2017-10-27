#!/usr/bin/env python
# encoding: utf-8

# ================================================================================
# check-1013-high-sierra-compatibility.py
#
# This script checks if the current system is compatible with macOS 10.13 High Sierra.
# These checks are based on the installCheckScript and volCheckScript in
# distribution file of OSInstall.mpkg installer package. The OSInstall.mpkg can be
# found in the root of InstallESD disk image.
#
# The checks done by this script are (in order):
# - Machine is a virtual machine or has a specific supported board-id
# - Machine model is not in a list of unsupported models
# - Current system version is less than 10.13 and at least 10.8.0
#
# Exit codes:
# 0 = High Sierra is supported
# 1 = High Sierra is not supported
#
# Orginal script from :
# Hannes Juutilainen <hjuutilainen@mac.com>
# https://github.com/hjuutilainen/adminscripts
#
# ================================================================================

import sys
import subprocess
import os
import re
import plistlib
from distutils.version import StrictVersion


# ================================================================================
# Start configuration
# ================================================================================

# Set this to False if you don't want any output, just the exit codes
verbose = True

# Set this to True if you want to add "sierra_supported" custom conditional to
# /Library/Managed Installs/ConditionalItems.plist
update_munki_conditional_items = False

# ================================================================================
# End configuration
# ================================================================================


def logger(message, status, info):
    if verbose:
        print "%14s: %-40s [%s]" % (message, status, info)
    pass


def conditional_items_path():
    # <https://github.com/munki/munki/wiki/Conditional-Items>
    # Read the location of the ManagedInstallDir from ManagedInstall.plist
    
    cmd = [
        "/usr/bin/defaults",
        "read",
        "/Library/Preferences/ManagedInstalls",
        "ManagedInstallDir"
    ]
    p = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    managed_installs_dir = results.strip()
    
    # Make sure we're outputting our information to "ConditionalItems.plist"
    if managed_installs_dir:
        return os.path.join(managed_installs_dir, 'ConditionalItems.plist')
    else:
        # Munki default
        return "/Library/Managed Installs/ConditionalItems.plist"


def munki_installed():
    cmd = ["pkgutil", "--pkg-info", "com.googlecode.munki.core"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.communicate()[0]
    if p.returncode == 0:
        return True
    else:
        return False


def is_system_version_supported():
    system_version_plist = plistlib.readPlist("/System/Library/CoreServices/SystemVersion.plist")
    product_name = system_version_plist['ProductName']
    product_version = system_version_plist['ProductVersion']
    if StrictVersion(product_version) >= StrictVersion('10.13'):
        logger("System",
               "%s %s" % (product_name, product_version),
               "Failed")
        return False
    elif StrictVersion(product_version) >= StrictVersion('10.8'):
        logger("System",
               "%s %s" % (product_name, product_version),
               "OK")
        return True
    else:
        logger("System",
               "%s %s" % (product_name, product_version),
               "Failed")
        return False


def get_board_id():
    cmd = ["/usr/sbin/ioreg",
           "-p", "IODeviceTree",
           "-r",
           "-n", "/",
           "-d", "1"]
    p1 = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p2 = subprocess.Popen(["/usr/bin/grep", "board-id"], stdin=p1.stdout, stdout=subprocess.PIPE)
    (results, err) = p2.communicate()
    board_id = re.sub(r"^\s*\"board-id\" = <\"(.*)\">$", r"\1", results)
    board_id = board_id.strip()
    if board_id.startswith('Mac'):
        return board_id
    else:
        return None


def is_virtual_machine():
    cmd = ["/usr/sbin/sysctl", "-n", "machdep.cpu.features"]
    p = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    for feature in results.split():
        if feature == "VMM":
            logger("Board ID",
                   "Virtual machine",
                   "OK")
            return True
    return False


def get_current_model():
    cmd = ["/usr/sbin/sysctl", "-n", "hw.model"]
    p = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    return results.strip()


def is_supported_model():
    not_supported_models = [
        'iMac4,1',
        'iMac4,2',
        'iMac5,1',
        'iMac5,2',
        'iMac6,1',
        'iMac7,1',
        'iMac8,1',
        'iMac9,1',
        'MacBook1,1',
        'MacBook2,1',
        'MacBook3,1',
        'MacBook4,1',
        'MacBook5,1',
        'MacBook5,2',
        'MacBookAir1,1',
        'MacBookAir2,1',
        'MacBookPro1,1',
        'MacBookPro1,2',
        'MacBookPro2,1',
        'MacBookPro2,2',
        'MacBookPro3,1',
        'MacBookPro4,1',
        'MacBookPro5,1',
        'MacBookPro5,2',
        'MacBookPro5,3',
        'MacBookPro5,4',
        'MacBookPro5,5',
        'Macmini1,1',
        'Macmini2,1',
        'Macmini3,1',
        'MacPro1,1',
        'MacPro2,1',
        'MacPro3,1',
        'MacPro4,1',
        'Xserve1,1',
        'Xserve2,1',
        'Xserve3,1']
    current_model = get_current_model()
    if current_model in not_supported_models:
        logger("Model",
               "\"%s\" is not supported" % current_model,
               "Failed")
        return False
    else:
        logger("Model",
               current_model,
               "OK")
        return True

def is_supported_board_id():
    platform_support_values = [
        'Mac-06F11F11946D27C5',
		'Mac-031B6874CF7F642A',
		'Mac-A5C67F76ED83108C',
		'Mac-CAD6701F7CEA0921',
		'Mac-50619A408DB004DA',
		'Mac-F22C8AC8',
		'Mac-B809C3757DA9BB8D',
		'Mac-AFD8A9D944EA4843',
		'Mac-F2268DC8',
		'Mac-942B59F58194171B',
		'Mac-27ADBB7B4CEE8E61',
		'Mac-F305150B0C7DEEEF',
		'Mac-35C1E88140C3E6CF',
		'Mac-77EB7D7DAF985301',
		'Mac-2E6FAB96566FE58C',
		'Mac-473D31EABEB93F9B',
		'Mac-7BA5B2794B2CDB12',
		'Mac-66E35819EE2D0D05',
		'Mac-BE0E8AC46FE800CC',
		'Mac-00BE6ED71E35EB86',
		'Mac-4B7AC7E43945597E',
		'Mac-F22C89C8',
		'Mac-937CB26E2E02BB01',
		'Mac-942459F5819B171B',
		'Mac-FFE5EF870D7BA81A',
		'Mac-2BD1B31983FE1663',
		'Mac-F222BEC8',
		'Mac-4BC72D62AD45599E',
		'Mac-4B682C642B45593E',
		'Mac-90BE64C3CB5A9AEB',
		'Mac-3CBD00234E554E41',
		'Mac-031AEE4D24BFF0B1',
		'Mac-66F35F19FE2A0D05',
		'Mac-F221BEC8',
		'Mac-B4831CEBD52A0C4C',
		'Mac-C08A6BB70A942AC2',
		'Mac-8ED6AF5B48C039E1',
		'Mac-FA842E06C61E91C5',
		'Mac-FC02E91DDD3FA6A4',
		'Mac-65CE76090165799A',
		'Mac-9AE82516C7C6B903',
		'Mac-6F01561E16C75D06',
		'Mac-F60DEB81FF30ACF6',
		'Mac-81E3E92DD6088272',
		'Mac-F2208EC8',
		'Mac-F22586C8',
		'Mac-189A3D4F975D5FFC',
		'Mac-942C5DF58193131B',
		'Mac-F2238BAE',
		'Mac-9F18E312C5C2BF0B',
		'Mac-C3EC7CD22292981F',
		'Mac-F221DCC8',
		'Mac-742912EFDBEE19B3',
		'Mac-CF21D135A7D34AA6',
		'Mac-942452F5819B1C1B',
		'Mac-112B0A653D3AAB9C',
		'Mac-DB15BD556843C820',
		'Mac-F22589C8',
		'Mac-77F17D7DA9285301',
		'Mac-F2238AC8',
		'Mac-BE088AF8C5EB4FA2',
		'Mac-551B86E5744E2388',
		'Mac-35C5E08120C7EEAF',
		'Mac-F65AE981FFA204ED',
		'Mac-94245B3640C91C81',
		'Mac-EE2EBD4B90B839A8',
		'Mac-42FD25EABCABB274',
		'Mac-7DF2A3B5E5D671ED',
		'Mac-F2268DAE',
		'Mac-06F11FD93F0323C5',
		'Mac-7DF21CB3ED6977E5',
		'Mac-A369DDC4E67F1C45',
		'Mac-F2268CC8',
		'Mac-94245A3940C91C80',
		'Mac-E43C1C25D4880AD6',
		'Mac-942B5BF58194151B']
    board_id = get_board_id()
    if board_id in platform_support_values:
        logger("Board ID",
               board_id,
               "OK")
        return True
    else:
        logger("Board ID",
               "\"%s\" is not supported" % board_id,
               "Failed")
        return False


def append_conditional_items(dictionary):
    current_conditional_items_path = conditional_items_path()
    if os.path.exists(current_conditional_items_path):
        existing_dict = plistlib.readPlist(current_conditional_items_path)
        output_dict = dict(existing_dict.items() + dictionary.items())
    else:
        output_dict = dictionary
    plistlib.writePlist(output_dict, current_conditional_items_path)
    pass


def main(argv=None):
    sierra_supported_dict = {}

    # Run the checks
    model_passed = is_supported_model()
    board_id_passed = is_supported_board_id()
    system_version_passed = is_system_version_supported()

    if is_virtual_machine():
        sierra_supported = 0
        sierra_supported_dict = {'sierra_supported': True}
    elif model_passed and board_id_passed and system_version_passed:
        sierra_supported = 0
        sierra_supported_dict = {'sierra_supported': True}
    else:
        sierra_supported = 1
        sierra_supported_dict = {'sierra_supported': False}

    # Update "ConditionalItems.plist" if munki is installed
    if munki_installed() and update_munki_conditional_items:
        append_conditional_items(sierra_supported_dict)

    # Exit codes:
    # 0 = High Sierra is supported
    # 1 = High Sierra is not supported
    return sierra_supported


if __name__ == '__main__':
    sys.exit(main())