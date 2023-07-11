import socket
import sys
from colorama import Fore, Style, init

init(autoreset=True)  # Automatically reset colorama colors after they're used

def check_connection(host_port_pairs):
    for host, port in host_port_pairs:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, int(port)))
        if result == 0:
            print(f"{Fore.GREEN}SUCCESS: Connected to {host} on port {port}")
        else:
            print(f"{Fore.RED}FAILED: Couldn't connect to {host} on port {port}")
        sock.close()

def main():
    input_method = input("Do you want to input hosts from command line arguments (c) or from a file (f)? ")
    host_ports = []
    port = input("Enter the port for all hosts: ")
    if input_method == 'c':
        for host in sys.argv[1:]:
            host_ports.append((host, port))
    elif input_method == 'f':
        try:
            with open(sys.argv[1], 'r') as file:
                for host in file:
                    host = host.strip()
                    host_ports.append((host, port))
        except IndexError:
            print("Please supply a filename as a command line argument.")
        except FileNotFoundError:
            print("File not found. Please check your file path.")
    else:
        print("Invalid input. Please choose c for command line or f for file.")
        return

    check_connection(host_ports)

if __name__ == "__main__":
    main()

