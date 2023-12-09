import subprocess
import re
import winreg
import random
import string
import ctypes
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        return False

def run_as_admin(cmd):
    """Run a command as administrator."""
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", "python", cmd, None, 1)
    except Exception as e:
        print(f"Error running as admin: {e}")

def get_transport_names():
    try:
        output = subprocess.check_output(["getmac", "/fo", "table", "/nh"], universal_newlines=True)
        lines = output.splitlines()

        transport_names = []

        for line in lines:
            match = re.search(r'(\{[\w-]+\})', line)
            if match:
                transport_names.append(match.group(1))

        return transport_names

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return []

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

def create_network_address(subkey_name):
    value_name = 'NetworkAddress'
    attempts = 3  # Number of attempts
    key_path = "SYSTEM\\ControlSet001\\Control\\Class\\{4d36e972-e325-11ce-bfc1-08002be10318}\\" + subkey_name
    while attempts > 0:
        value_data = create_random_network_address()
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value_data)
            print(f"NetworkAddress created - Value Data: {value_data}")
            winreg.CloseKey(key)
            return  # Successfully created, exit the function
        except Exception as e:
            print(f"Error creating NetworkAddress: {e}")
            attempts -= 1

    print("Failed to create NetworkAddress after multiple attempts.")

if __name__ == "__main__":
    if is_admin():
        print("running with administrative privileges.")
    else:
        print("not running with administrative privileges. attempting to run as admin now. (unstable/doesnt work currently)")
        run_as_admin(os.path.abspath(__file__))
        exit()

    transport_names = get_transport_names()
    
    if transport_names:
        print("available transport names (the first one is usually the correct one):")
        for idx, name in enumerate(transport_names):
            print(f"{idx + 1}. {name}")

        selected_index = int(input("enter the index of the transport name you want to search: ")) - 1

        if 0 <= selected_index < len(transport_names):
            selected_transport_name = transport_names[selected_index]
            print(f"\nselected transport name: {selected_transport_name}\n")

            instances = search_registry_for_netcfg_instance_id(selected_transport_name)

            if instances:
                for instance in instances:
                    print(f"NetCfgInstanceId found - value data: {instance[0]} - found within ..\\{instance[1]}")
                    key_path = "SYSTEM\\ControlSet001\\Control\\Class\\{4d36e972-e325-11ce-bfc1-08002be10318}\\" + instance[1]
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
                    network_address = search_registry_for_network_address(key)

                    if network_address is None:
                        create_option = input("NetworkAddress not found. do you want to create one? (y/n): ").lower()
                        if create_option == 'y':
                            create_network_address(instance[1])  # Pass the subkey name instead of the subkey
                    else:
                        change_option = input("NetworkAddress found. do you want to change it? (y/n): ").lower()
                        if change_option == 'y':
                            create_network_address(instance[1])  # Pass the subkey name instead of the subkey
                        else:
                            print(f"NetworkAddress: {network_address}\n")

                    winreg.CloseKey(key)
            else:
                print("no instances found for the selected transport name.")
        else:
            print("invalid index selected.")
    else:
        print("no transport names found.")