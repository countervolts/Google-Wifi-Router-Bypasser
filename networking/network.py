import subprocess
import re
import winreg
import random

def get_transport_names():
    try:
        output = subprocess.check_output(["getmac", "/fo", "table", "/nh"], universal_newlines=True)
        lines = output.splitlines()

        transport_names = []
        most_probable_transport_name = None

        for line in lines:
            match = re.search(r'(\{[\w-]+\})', line)
            if match:
                transport_name = match.group(1)
                transport_names.append(transport_name)
                if most_probable_transport_name is None and transport_name != '':
                    most_probable_transport_name = transport_name

        return transport_names, most_probable_transport_name

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return [], None

def search_registry_for_netcfg_instance_id(transport_name):
    key_path = r"SYSTEM\ControlSet001\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"
    value_name = 'NetCfgInstanceId'

    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
        subkey_index = 0

        found_instances = []

        while True:
            try:
                subkey_name = winreg.EnumKey(key, subkey_index)
                subkey = winreg.OpenKey(key, subkey_name)
                try:
                    value, _ = winreg.QueryValueEx(subkey, value_name)
                    if value == transport_name:
                        found_instances.append((value, subkey_name))
                except FileNotFoundError:
                    pass
                finally:
                    winreg.CloseKey(subkey)
                subkey_index += 1
            except OSError:
                break

        winreg.CloseKey(key)

        return found_instances

    except FileNotFoundError:
        print("Registry key not found.")
        return []

def search_registry_for_network_address(subkey):
    value_name = 'NetworkAddress'
    try:
        value_data, _ = winreg.QueryValueEx(subkey, value_name)
        return value_data
    except FileNotFoundError:
        return None

def create_random_network_address():
    random_hex = ''.join(random.choices('0123456789ABCDEF', k=10))
    return 'DE' + random_hex

def get_selected_transport():
    _, most_probable_transport_name = get_transport_names()
    return most_probable_transport_name

def get_transport_dir(subkey_name):
    return "SYSTEM\\ControlSet001\\Control\\Class\\{4d36e972-e325-11ce-bfc1-08002be10318}\\" + subkey_name

def get_previous_mac_address():

    _, most_probable_transport_name = get_transport_names()
    instances = search_registry_for_netcfg_instance_id(most_probable_transport_name)
    
    if instances:
        _, subkey_name = instances[0]
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, get_transport_dir(subkey_name), 0, winreg.KEY_READ)
        old_mac = winreg.QueryValueEx(key, 'NetworkAddress')[0]
        winreg.CloseKey(key)
        return old_mac
    return None

def create_network_address(subkey_name):
    value_name = 'NetworkAddress'
    attempts = 3 
    key_path = "SYSTEM\\ControlSet001\\Control\\Class\\{4d36e972-e325-11ce-bfc1-08002be10318}\\" + subkey_name
    while attempts > 0:
        value_data = create_random_network_address()
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value_data)
            print(f"NetworkAddress created - Value Data: {value_data}")
            winreg.CloseKey(key)
            return
        except Exception as e:
            print(f"uh oh: {e}")
            attempts -= 1

    print("failed after multiple attempts")
