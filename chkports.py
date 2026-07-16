# SPDX-License-Identifier: GPL-3.0-or-later
"""connchk / chkports — a small, colorful TCP port reachability checker.

Runs either non-interactively (hosts and ports supplied as flags/arguments) or
interactively (guided prompts fill in whatever you leave out). This module is
kept self-contained on purpose: connchk.py copies it to remote hosts and runs
it there, so it must not import any sibling project files.
"""
import argparse
import re
import socket
import sys

from colorama import Fore, Style, init

init()  # enable ANSI handling (needed on Windows); resets are managed by _paint

APP_NAME = "connchk"
TAGLINE = "Check whether ports are reachable across your source and destination."

# Figlet-style title, rendered with a trailing tagline beneath it.
BANNER_LINES = (
    "                            _     _    ",
    "  ___ ___  _ __  _ __   ___| |__ | | __",
    " / __/ _ \\| '_ \\| '_ \\ / __| '_ \\| |/ /",
    "| (_| (_) | | | | | | | (__| | | |   < ",
    " \\___\\___/|_| |_|_| |_|\\___|_| |_|_|\\_\\",
)


def _paint(text, *styles, color=True):
    """Wrap text in colorama styles, or return it unchanged when color is off."""
    if not color or not styles:
        return text
    return "".join(styles) + text + Style.RESET_ALL


def supports_color(stream):
    """True when the stream is an interactive terminal that can show color."""
    return hasattr(stream, "isatty") and stream.isatty()


def render_banner(color=True):
    """Return the multi-line title banner with its tagline."""
    art = "\n".join(_paint(line, Fore.CYAN, Style.BRIGHT, color=color) for line in BANNER_LINES)
    tagline = _paint("  " + TAGLINE, Style.DIM, color=color)
    return f"\n{art}\n\n{tagline}\n"


def parse_ports(raw):
    """Parse a comma-separated port list into a list of ints, validating each."""
    ports = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if not chunk.isdigit() or not 0 < int(chunk) < 65536:
            raise ValueError(f"invalid port {chunk!r} (expected 1-65535)")
        ports.append(int(chunk))
    if not ports:
        raise ValueError("no ports given")
    return ports


def hosts_from_file(path):
    """Read hosts from a file, one per line, ignoring blanks and # comments."""
    with open(path, "r") as handle:
        hosts = [line.strip() for line in handle]
    hosts = [h for h in hosts if h and not h.startswith("#")]
    if not hosts:
        raise ValueError(f"no hosts found in {path}")
    return hosts


def build_pairs(hosts, ports):
    """Cartesian product of hosts and ports as (host, port) tuples."""
    return [(host, port) for host in hosts for port in ports]


def check_pair(host, port, timeout):
    """Attempt a TCP connection; return True when the port accepts it."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        return sock.connect_ex((host, int(port))) == 0
    except socket.gaierror:
        return False  # host name did not resolve
    finally:
        sock.close()


def run_checks(pairs, timeout, color=True):
    """Check every pair, print a color-coded line each, then a summary.

    Returns 0 when every pair connected, 1 when at least one failed.
    """
    header = f"Checking {len(pairs)} host:port pair(s) with a {timeout:g}s timeout"
    print(_paint(header, Style.DIM, color=color) + "\n")

    width = max((len(f"{host}:{port}") for host, port in pairs), default=0)
    passed = 0
    for host, port in pairs:
        target = f"{host}:{port}".ljust(width)
        if check_pair(host, port, timeout):
            passed += 1
            mark = _paint("✔", Fore.GREEN, Style.BRIGHT, color=color)
            label = _paint("SUCCESS", Fore.GREEN, color=color)
        else:
            mark = _paint("✘", Fore.RED, Style.BRIGHT, color=color)
            label = _paint("FAILED ", Fore.RED, color=color)
        print(f"  {mark} {label}  {target}")

    failed = len(pairs) - passed
    passed_txt = _paint(f"{passed} passed", Fore.GREEN, Style.BRIGHT, color=color)
    if failed:
        failed_txt = _paint(f"{failed} failed", Fore.RED, Style.BRIGHT, color=color)
    else:
        failed_txt = _paint("0 failed", Style.DIM, color=color)
    print("\n  " + _paint("Summary:", Style.BRIGHT, color=color) + f"  {passed_txt}   {failed_txt}")
    return 0 if failed == 0 else 1


def prompt(message, color=True):
    """Prompt the user with a styled message and return their input."""
    return input(_paint(message, Fore.CYAN, color=color))


def resolve_hosts(args, interactive, color):
    """Determine the hosts to check from flags, else interactive prompts."""
    if args.file:
        return hosts_from_file(args.file)
    if args.hosts:
        return args.hosts
    if not interactive:
        raise ValueError("no hosts given (pass hosts, --file, or run in a terminal)")
    method = prompt("Read hosts from [c]ommand-line entry or a [f]ile? ", color).strip().lower()
    if method == "f":
        return hosts_from_file(prompt("Path to hosts file: ", color).strip())
    raw = prompt("Hosts to check (space- or comma-separated): ", color).strip()
    hosts = [h for h in re.split(r"[\s,]+", raw) if h]
    if not hosts:
        raise ValueError("no hosts entered")
    return hosts


def resolve_ports(args, interactive, color):
    """Determine the ports to check from flags, else an interactive prompt."""
    if args.ports:
        return parse_ports(args.ports)
    if not interactive:
        raise ValueError("no ports given (pass --ports or run in a terminal)")
    return parse_ports(prompt("Ports to test (comma-separated, e.g. 22,80,443): ", color))


def build_parser():
    parser = argparse.ArgumentParser(
        prog="chkports.py",
        description=TAGLINE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  chkports.py 192.0.2.10 192.0.2.20 --ports 22,80,443\n"
            "  chkports.py --file hosts.txt --ports 443 --timeout 1.5\n"
            "  chkports.py            # fully interactive, guided prompts"
        ),
    )
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


def main(argv=None):
    args = build_parser().parse_args(argv)
    color = not args.no_color and supports_color(sys.stdout)
    interactive = sys.stdin.isatty()

    if not args.no_banner:
        print(render_banner(color))

    try:
        hosts = resolve_hosts(args, interactive, color)
        ports = resolve_ports(args, interactive, color)
    except (ValueError, OSError) as exc:
        print(_paint(f"Error: {exc}", Fore.RED, Style.BRIGHT, color=color), file=sys.stderr)
        return 2

    return run_checks(build_pairs(hosts, ports), args.timeout, color)


if __name__ == "__main__":
    sys.exit(main())
