import socket
import subprocess
import re
import winreg
import os

from networking.network import get_transport_names, get_previous_mac_address, get_selected_transport, get_transport_dir, search_registry_for_netcfg_instance_id, search_registry_for_network_address

from utils.utils import is_admin, run_as_admin

def write_debug_info():
    from beta_features.features import is_using_beta_features, selected_features

    if os.path.exists('DebugBypass.txt'):
        os.remove('DebugBypass.txt')

    with open('DebugBypass.txt', 'w', encoding='utf-8') as f:
        try:
            socket.create_connection(("1.1.1.1", 80))
            f.write("Status: Online\n\n")
        except OSError:
            f.write("Status: Offline\n\n")

        bypass_running = False
        transport_names, most_probable_transport_name = get_transport_names()
        for instance in search_registry_for_netcfg_instance_id(most_probable_transport_name):
            key_path = "SYSTEM\\ControlSet001\\Control\\Class\\{4d36e972-e325-11ce-bfc1-08002be10318}\\" + instance[1]
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
            network_address = search_registry_for_network_address(key)
            if network_address is not None:
                bypass_running = True
                break
        if bypass_running:
            f.write("Bypass: Active (very possible)\n\n")
        else:
            f.write("Bypass: Not running\n\n")
            
        is_using_beta = is_using_beta_features()
        if is_using_beta:
            f.write("Beta features: On\n\n")
            used_beta_features = selected_features
            f.write("Used beta features:\n")
            for feature in used_beta_features:
                f.write(f"  - {feature}\n")
            f.write("\n")
        else:
            f.write("Beta features: Off\n\n")

        def get_mac_address_for_transport(transport_name):
            output = subprocess.check_output(f'getmac | findstr {transport_name}', shell=True).decode()

            match = re.search(r"([\da-fA-F]{2}-){5}[\da-fA-F]{2}", output)
            if match:
                return match.group(0)
            else:
                return None

        transport_names, most_probable_transport_name = get_transport_names()
        f.write("Transport names:\n")
        for transport_name in transport_names:
            f.write(f"  - {transport_name}\n")
            mac_address = get_mac_address_for_transport(transport_name)
            if mac_address:
                f.write(f"     - {mac_address}\n")
            else:
                f.write("     - No MAC address found\n")
        f.write("\n")

        selected_transport = get_selected_transport()
        f.write(f"Selected transport: {selected_transport}\n\n")

        transport_dir = get_transport_dir(selected_transport)
        f.write(f"Transport directory: {transport_dir}\n\n")

        mac_address_history = get_previous_mac_address()
        if mac_address_history:
            last_mac_address = mac_address_history[-12:]
            formatted_mac_address = ':'.join(last_mac_address[i:i+2] for i in range(0, len(last_mac_address), 2))
            f.write(f"Current MAC address: {formatted_mac_address}\n")
        else:
            f.write("No MAC address history found.\n")

        ip_address = socket.gethostbyname(socket.gethostname())
        masked_ip_address = re.sub(r'\.\d+\.\d+$', '.XX.XX', ip_address)
        f.write(f"IP address: {masked_ip_address}\n")

        if not subprocess.call("netsh advfirewall firewall show rule name=\"BlockAllOutbound\"", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT):
            f.write("Outbound connections: Blocked\n")
        else:
            f.write("Outbound connections: Not blocked\n")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        f.write(f"Socket family: {sock.family}\n")
        f.write(f"Socket type: {sock.type}\n")
        f.write(f"Socket protocol: {sock.proto}\n")

def testdebug():
    input("testing pyinstaller: ")()