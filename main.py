import subprocess
import re
import winreg
import socket
import ctypes
import os
import sys

from networking.network import get_transport_names, search_registry_for_netcfg_instance_id, search_registry_for_network_address, create_network_address

from beta_features.features import run_batch_commands, create_vnet, create_restore_point, create_hotspot

from debug.debugger import write_debug_info

from utils.utils import set_window_title, is_admin, run_as_admin, clear_console, check_for_updates

set_window_title()

if __name__ == "__main__":
    clear_console()
    try:
        socket.create_connection(("1.1.1.1", 80))
        print("Status: Online")
    except OSError:
        print("Status: Offline")
    transport_names, most_probable_transport_name = get_transport_names()
    if "Wi-Fi" in most_probable_transport_name:
        print("Connection: WiFi")
    else:
        print("Connection: Ethernet")
    if not subprocess.call("netsh advfirewall firewall show rule name=\"BlockAllOutbound\"", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT):
        print("Outbound connections: Blocked")
    else:
        print("Outbound connections: Not blocked (BETA FEATURE)")
    bypass_running = False
    for instance in search_registry_for_netcfg_instance_id(most_probable_transport_name):
        key_path = "SYSTEM\\ControlSet001\\Control\\Class\\{4d36e972-e325-11ce-bfc1-08002be10318}\\" + instance[1]
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
        network_address = search_registry_for_network_address(key)
        if network_address is not None:
            bypass_running = True
            break
    if bypass_running:
        print("bypass: active (very possible)")
    else:
        print("bypass: not running")
    if not is_admin():
        print("???? (failsafe)")
        run_as_admin()
        sys.exit()
    else:
        check_for_updates('2.0.1')

        hosted_network_info = subprocess.check_output('netsh wlan show hostednetwork', shell=True).decode()
        status = re.search(r'Status\s+:\s+(\w+)', hosted_network_info)
        if status:
            print(f"Hotspot status: {status.group(1)}")
        else:
            print("error")
        hosted_network_info = subprocess.check_output('netsh wlan show hostednetwork', shell=True).decode()
        status = re.search(r'Status\s+:\s+(\w+)', hosted_network_info)
        if status:
            print(f"Hotspot status: {status.group(1)}")
        else:
            print("error")
    transport_names, most_probable_transport_name = get_transport_names()
    if transport_names:
        print("\nAvailable transport names (the first one is usually the correct one):")
        for idx, name in enumerate(transport_names[:5]):
            if name == most_probable_transport_name:
                print(f"{idx + 1}. {name} <-- the code detects this is the most likely one")
            else:
                print(f"{idx + 1}. {name}")
        selected_index = int(input("\nEnter the index of the transport name you want to search: ")) - 1
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

    write_debug_option = input("\nDo you want to write the debug information? (y/n): ").lower()
    if write_debug_option == 'y':
        print("writing debug information now :)")
        write_debug_info()
    
    input("you have been blessed by ayo/countervolts, please restart your computer")