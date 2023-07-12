import os
import sys
import paramiko
from getpass import getpass
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
    run_location = input("Do you want to run the program locally (l) or on a remote host (r)? ")
    if run_location == 'r':
        username = input("Enter your username: ")
        password = getpass("Enter your password: ")  # Use getpass to securely get the password
        host = input("Enter the remote host IP: ")

        key = paramiko.RSAKey(filename="~/.ssh/id_rsa")  # Replace with your private key path
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Auto add host key. Be careful with this in real scenarios. You don't want to blindly add hosts keys of systems you don't recognize onto your local system.
        ssh.connect(host, username=username, password=password)

        # Assume the script name is check_ports.py and it's in the current working directory
        ftp = ssh.open_sftp()
        ftp.put('chkports.py', '/tmp/chkports.py')  # Copy to /tmp/ on the remote machine
        ftp.close()

        # Now run the script on the remote machine and print output
        stdin, stdout, stderr = ssh.exec_command('python3 /tmp/chkports.py')
        print(stdout.read().decode())
        
        # Remove the file from the remote host
        ssh.exec_command('rm /tmp/chkports.py')

        ssh.close()
    else:
        ports_input = input("Enter the ports for all hosts (comma-separated): ")
        ports = [port.strip() for port in ports_input.split(",")]
        host_ports = []

        input_method = input("Do you want to input hosts from command line arguments (c) or from a file (f)? ")
        if input_method == 'c':
            for host in sys.argv[1:]:
                for port in ports:
                    host_ports.append((host, port))
        elif input_method == 'f':
            try:
                with open(sys.argv[1], 'r') as file:
                    for host in file:
                        host = host.strip()
                        for port in ports:
                            host_ports.append((host, port))
            except IndexError:
                print("Please supply a filename as a command line argument.")
            except FileNotFoundError:
                print("File not found. Please check your file path.")

        check_connection(host_ports)

if __name__ == "__main__":
    main()

