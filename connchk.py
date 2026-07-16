# SPDX-License-Identifier: GPL-3.0-or-later
"""connchk — run the port check locally or on a remote host over SSH.

Wraps chkports.py with a local/remote switch. Remote mode connects with
paramiko, copies chkports.py to /tmp on the target, runs it there
non-interactively, streams the output back, and removes the file afterwards.

Like chkports.py it runs either non-interactively (everything supplied as
flags) or interactively (guided prompts fill in what you leave out).
"""
import argparse
import os
import shlex
import sys
from getpass import getpass

import paramiko

import chkports
from chkports import Fore, Style, _paint, prompt, render_banner, supports_color

CHKPORTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chkports.py")
REMOTE_PATH = "/tmp/chkports.py"


def run_local(args, interactive, color):
    """Resolve hosts/ports and run the check on this machine."""
    hosts = chkports.resolve_hosts(args, interactive, color)
    ports = chkports.resolve_ports(args, interactive, color)
    pairs = chkports.build_pairs(hosts, ports)
    return chkports.run_checks(pairs, args.timeout, color)


def build_remote_command(hosts, ports, timeout):
    """Build the shell command that runs chkports.py on the remote host."""
    parts = ["python3", REMOTE_PATH]
    parts += list(hosts)
    parts += ["--ports", ",".join(str(port) for port in ports)]
    parts += ["--timeout", str(timeout), "--no-banner"]
    return " ".join(shlex.quote(part) for part in parts)


def run_remote(args, interactive, color):
    """Copy chkports.py to the remote host, run it there, print the output."""
    host = args.host or (prompt("Remote host IP/name: ", color).strip() if interactive else None)
    user = args.user or (prompt("SSH username: ", color).strip() if interactive else None)
    if not host or not user:
        raise ValueError("remote mode needs both --host and --user")

    # Hosts/ports must be supplied up front for remote mode; prompt only when interactive.
    hosts = chkports.resolve_hosts(args, interactive, color)
    ports = chkports.resolve_ports(args, interactive, color)

    connect_kwargs = {"hostname": host, "username": user}
    if args.identity:
        connect_kwargs["key_filename"] = os.path.expanduser(args.identity)
    else:
        password = os.environ.get("CONNCHK_PASSWORD")
        if password is None:
            if not interactive:
                raise ValueError("no credentials: pass --identity or set CONNCHK_PASSWORD")
            password = getpass("SSH password: ")
        connect_kwargs["password"] = password

    print(_paint(f"\nConnecting to {user}@{host} ...", Style.DIM, color=color))
    ssh = paramiko.SSHClient()
    # AutoAddPolicy trusts unknown host keys — safe only on networks you control.
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(**connect_kwargs)
        sftp = ssh.open_sftp()
        sftp.put(CHKPORTS_PATH, REMOTE_PATH)
        sftp.close()
        try:
            command = build_remote_command(hosts, ports, args.timeout)
            _, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode()
            errors = stderr.read().decode()
            exit_status = stdout.channel.recv_exit_status()
        finally:
            ssh.exec_command(f"rm -f {shlex.quote(REMOTE_PATH)}")
    except (paramiko.SSHException, OSError) as exc:
        print(_paint(f"Remote error: {exc}", Fore.RED, Style.BRIGHT, color=color), file=sys.stderr)
        return 1
    finally:
        ssh.close()

    print(_paint(f"Results from {host}:", Style.BRIGHT, color=color) + "\n")
    if output:
        print(output.rstrip("\n"))
    if errors.strip():
        print(_paint(errors.rstrip("\n"), Fore.RED, color=color), file=sys.stderr)
    return exit_status


def build_parser():
    parser = argparse.ArgumentParser(
        prog="connchk.py",
        description="Run the connchk port check locally or on a remote host over SSH.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  connchk.py --local 192.0.2.10 --ports 22,80,443\n"
            "  connchk.py --remote --host 192.0.2.50 --user ops \\\n"
            "             --file hosts.txt --ports 443\n"
            "  connchk.py             # fully interactive, guided prompts\n"
            "\n"
            "For remote password auth non-interactively, set CONNCHK_PASSWORD;\n"
            "or use --identity to authenticate with an SSH key."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--local", action="store_true", help="run the check on this machine")
    mode.add_argument("--remote", action="store_true", help="run the check on a remote host over SSH")
    parser.add_argument("--host", help="remote host IP/name (remote mode)")
    parser.add_argument("--user", help="SSH username (remote mode)")
    parser.add_argument("--identity", metavar="KEYFILE", help="SSH private key file (remote mode)")
    parser.add_argument("hosts", nargs="*", help="one or more hosts/IPs to check")
    parser.add_argument("-f", "--file", metavar="PATH", help="read hosts from a file, one per line")
    parser.add_argument("-p", "--ports", metavar="LIST", help="comma-separated ports, e.g. 22,80,443")
    parser.add_argument(
        "-t", "--timeout", type=float, default=3.0, metavar="SECONDS",
        help="per-connection timeout in seconds (default: 3)",
    )
    parser.add_argument("--no-banner", action="store_true", help="do not print the title banner")
    parser.add_argument("--no-color", action="store_true", help="disable colored output")
    return parser


def resolve_mode(args, interactive, color):
    """Return 'local' or 'remote', prompting only when neither flag was given."""
    if args.remote:
        return "remote"
    if args.local:
        return "local"
    if args.host or args.user or args.identity:
        return "remote"
    if not interactive:
        return "local"
    answer = prompt("Run [l]ocally or on a [r]emote host? ", color).strip().lower()
    return "remote" if answer == "r" else "local"


def main(argv=None):
    args = build_parser().parse_args(argv)
    color = not args.no_color and supports_color(sys.stdout)
    interactive = sys.stdin.isatty()

    if not args.no_banner:
        print(render_banner(color))

    try:
        mode = resolve_mode(args, interactive, color)
        if mode == "remote":
            return run_remote(args, interactive, color)
        return run_local(args, interactive, color)
    except (ValueError, OSError) as exc:
        print(_paint(f"Error: {exc}", Fore.RED, Style.BRIGHT, color=color), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
