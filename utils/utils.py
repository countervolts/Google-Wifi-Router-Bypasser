import random
import string
import ctypes
import os
import sys
import requests
import subprocess

def set_window_title():
    random_title = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    random_title += " - created by countervolts (v2.1.2)"
    ctypes.windll.kernel32.SetConsoleTitleW(random_title)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        return False

def run_as_admin():
    """Run the current script as administrator."""
    try:
        script_path = os.path.abspath(sys.argv[0])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}"', None, 1)
    except Exception as e:
        print(f"Error running as admin: {e}")

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def check_for_updates(current_version):
    response = requests.get('https://api.github.com/repos/countervolts/Google-Wifi-Router-Bypasser/releases/latest')
    latest_release = response.json()

    latest_version = latest_release['tag_name']
    if latest_version.startswith('v'):
        latest_version = latest_version[1:]  

    current_version_tuple = tuple(map(int, current_version.split('.')))
    latest_version_tuple = tuple(map(int, latest_version.split('.')))

    if latest_version_tuple > current_version_tuple:
        print(f"New version {latest_version} available. Downloading...")

        for asset in latest_release['assets']:
            if asset['name'].endswith('.exe'):
                response = requests.get(asset['browser_download_url'], stream=True)
                new_file_name = f"NetAddress{latest_version}.exe"
                new_file_path = os.path.join(sys.path[0], new_file_name)
                with open(new_file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                print("Download complete. Press any key to run the new version as admin...")
                input()
                ctypes.windll.shell32.ShellExecuteW(None, "runas", new_file_path, None, None, 1)
                print(f"Running {new_file_path} as admin...")
                os.remove(sys.argv[0])
                sys.exit()
    else:
        print("You're running the latest version.")

current_version = '2.1.2'
check_for_updates(current_version)
