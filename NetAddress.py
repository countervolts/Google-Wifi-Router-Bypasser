import subprocess
import re
import winreg
import random
import socket
import ctypes
import os
import sys

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        return False

def run_as_admin():
    """Run the current script as administrator."""
    try:
        script_path = os.path.abspath(sys.argv[0])  # Get the path of the current script
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}"', None, 1)
    except Exception as e:
        print(f"Error running as admin: {e}")

## ignore please

#def create_restore_point(description='NetAddress Restore Point', #restore_point_type=0, event_type=100):
#    SRP = ctypes.windll.srpapi
#    restore_point = ctypes.windll.srpapi._RESTOREPTINFOA()
#    restore_point.dwEventType = event_type
#    restore_point.dwRestorePtType = restore_point_type
#    restore_point.llSequenceNumber = 0
#    restore_point.szDescription = description
#    status = SRP.SRSetRestorePointA(ctypes.byref(restore_point), None)
#    if status == 0:
#        print('Restore point created successfully.')
#    else:
#        print('Failed to create restore point.')
#
#create_restore_point()

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
            print(f"Error creating NetworkAddress: {e}")
            attempts -= 1

    print("Failed to create NetworkAddress after multiple attempts.")

if __name__ == "__main__":
    if not is_admin():
        print("not running with administrative privileges. attempting to run as admin now.")
        run_as_admin()
        sys.exit()
    else:
        print("running with administrative privileges.")

    transport_names, most_probable_transport_name = get_transport_names()

    if transport_names:
        print("Available transport names (the first one is usually the correct one):")
        for idx, name in enumerate(transport_names):
            if name == most_probable_transport_name:
                print(f"{idx + 1}. {name} <-- the code detects this is the most likely one")
            else:
                print(f"{idx + 1}. {name}")

        selected_index = int(input("Enter the index of the transport name you want to search: ")) - 1

        if 0 <= selected_index < len(transport_names):
            selected_transport_name = transport_names[selected_index]
            print(f"\nSelected transport name: {selected_transport_name}\n")
            
            instances = search_registry_for_netcfg_instance_id(selected_transport_name)

            if instances:
                for instance in instances:
                    print(f"NetCfgInstanceId found - value data: {instance[0]} - found within ..\\{instance[1]}")
                    key_path = "SYSTEM\\ControlSet001\\Control\\Class\\{4d36e972-e325-11ce-bfc1-08002be10318}\\" + instance[1]
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
                    network_address = search_registry_for_network_address(key)

                    if network_address is None:
                        create_option = input("NetworkAddress not found. do you want to create one? (THIS IS THE BYPASS DO Y IF YOU WANT IT TO WORK) (y/n): ").lower()
                        if create_option == 'y':
                            create_network_address(instance[1]) 
                    else:
                        change_option = input("NetworkAddress found. do you want to change it? (y/n): ").lower()
                        if change_option == 'y':
                            create_network_address(instance[1])
                        else:
                            print(f"NetworkAddress: {network_address}\n")

                    winreg.CloseKey(key)
            else:
                print("no instances found for the selected transport name.")
        else:
            print("invalid index selected.")
    else:
        print("no transport names found.")

    create_vnet_option = input("would you like to hide your identity, this will create a virtual network masking your true identity (y/n): ").lower()
    if create_vnet_option == 'y':
        vnet_name = socket.gethostname() 
        script_path = os.path.join(os.path.expanduser('~'), 'create_vnet.ps1')
        with open(script_path, 'w') as f:
            f.write(f'New-VMSwitch -Name "{vnet_name}" -SwitchType Internal\n')
        cmd = f'powershell.exe -ExecutionPolicy Bypass -File "{script_path}"'
        subprocess.run(cmd, shell=True)
        cmd = f'schtasks /Create /SC ONSTART /TN "CreateVNet" /TR "powershell.exe -ExecutionPolicy Bypass -File \'{script_path}\'" /RU SYSTEM'
        subprocess.run(cmd, shell=True)

        cmd = f'powershell.exe Get-VMSwitch -Name "{vnet_name}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(f"Virtual network '{vnet_name}' was created successfully.")
        else:
            print(f"Failed to create virtual network '{vnet_name}'.")

        cmd = 'powershell.exe Get-VMSwitch | Where-Object {$_.SwitchType -eq "Internal"}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            shutdown_option = input("virtual network is already running, would you like to destroy it? (y/n): ").lower()
            if shutdown_option == 'y':
                cmd = 'powershell.exe Get-VMSwitch | Where-Object {$_.SwitchType -eq "Internal"} | Remove-VMSwitch -Force'
                subprocess.run(cmd, shell=True)

    input("restart your computer if you made a new netaddress (enter to close)")
