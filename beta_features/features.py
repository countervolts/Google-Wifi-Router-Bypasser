import subprocess
import re
import ctypes
import socket
import os

def run_batch_commands():
    print("attempting fakedc")
    ip = subprocess.check_output("ipconfig | findstr /C:\"IPv4 Address\"", shell=True).decode().split(":")[-1].strip()
    blocking = "No"

    print("THIS IS A BETA FEATURE IT IS NOT PERFECT AND MAY NOT WORK ACCORDINGLY")
    print(f"fake disconnect: {ip}")
    print(f"Blocking: {blocking}")
    print("\n1. Block\n2. Unblock")
    choice = input("Enter your choice: ")

    if choice == "1":
        if subprocess.call("netsh advfirewall firewall show rule name=\"BlockAllOutbound\"", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT):
            subprocess.call("netsh advfirewall firewall add rule name=\"BlockAllOutbound\" dir=out action=block", shell=True)
            blocking = "Yes"
    elif choice == "2":
        if not subprocess.call("netsh advfirewall firewall show rule name=\"BlockAllOutbound\"", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT):
            subprocess.call("netsh advfirewall firewall delete rule name=\"BlockAllOutbound\"", shell=True)
            blocking = "No"

    if not subprocess.call("netsh advfirewall firewall show rule name=\"BlockAllOutbound\"", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT):
        print("Outbound connections: Blocked")
    else:
        print("Outbound connections: Not blocked")

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def create_restore_point(description='NetAddress Restore Point', restore_point_type=0, event_type=100):
    SRP = ctypes.windll.srclient
    restore_point = ctypes.create_string_buffer(200)
    ctypes.windll.kernel32.RtlZeroMemory(ctypes.byref(restore_point), 200)
    ctypes.windll.kernel32.lstrcpyA(ctypes.byref(restore_point), description.encode('utf-8')) 

    class RESTOREPOINTINFO(ctypes.Structure):
        _fields_ = [
            ('dwEventType', ctypes.c_long),
            ('dwRestorePtType', ctypes.c_long),
            ('llSequenceNumber', ctypes.c_longlong),
            ('szDescription', ctypes.c_char_p),
        ]

    restore_point_info = RESTOREPOINTINFO(event_type, restore_point_type, 0, restore_point.raw)
    status = SRP.SRSetRestorePointA(ctypes.byref(restore_point_info), None)
    if status == 0:
        print('Restore point created successfully.')
    else:
        print('Failed to create restore point.')

def display_beta_features(beta_dict):
    print("Beta features available:\n")
    for i, feature in enumerate(beta_dict.keys(), start=1):
        print(f"{i}. {feature}")

def handle_beta_feature_selection(beta_dict):
    print(f"{len(beta_dict) + 1}. Test all\n")
    choices = input("Enter the numbers of the features you want to try (separated by '/' for example 1/2):").split('/')
    selected_features = []
    for choice in choices:
        if int(choice) == len(beta_dict) + 1:
            for function_to_run in beta_dict.values():
                function_to_run()
            selected_features = list(beta_dict.keys())
        else:
            function_to_run = list(beta_dict.values())[int(choice) - 1]
            function_to_run()
            selected_features.append(list(beta_dict.keys())[int(choice) - 1])
    return selected_features

def create_vnet():
    create_vnet_option = input("false self (faux idenity): no return after (y/n?): ").lower()
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

def create_hotspot():
    ssid = input("name of hotspot: ")
    key = input("password: ")
    subprocess.run(f'netsh wlan set hostednetwork mode=allow ssid={ssid} key={key}', shell=True)
    subprocess.run('netsh wlan start hostednetwork', shell=True)
    hosted_network_info = subprocess.check_output('netsh wlan show hostednetwork', shell=True).decode()
    status = re.search(r'Status\s+:\s+(\w+)', hosted_network_info)
    if status:
        print(f"Hosted network status: {status.group(1)}")
    else:
        print("Could not determine hosted network status.")

beta_dict = {
    "FakeDc\n- Also known as FakeDisconnect, this will attempt to false your device diconnection so when bypassing there will be no new device pop up\n": run_batch_commands,
    "Faux identity\n- This pairs perfectly with FakeDc, by creating a fake you!\n": create_vnet,
    "Failsafe/Restore Point\n- this will create a restore point which can be used if something bad happens (not really tested)\n": create_restore_point,
    "Personal Hotspot\n- this will create a personal hotspot using the built-in Windows feature\n": create_hotspot
}

display_beta_features(beta_dict)

beta_choice = input("Would you like to test beta features? (y/n): ")

def is_using_beta_features():
    return beta_choice.lower() == "y"

if beta_choice.lower() == "y":
    clear_console()
    display_beta_features(beta_dict)
    selected_features = handle_beta_feature_selection(beta_dict)