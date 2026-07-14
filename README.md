# connchk

[![CI](https://github.com/iamteedoh/connchk/actions/workflows/ci.yml/badge.svg)](https://github.com/iamteedoh/connchk/actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-GPL--3.0-blue)
[![GitHub Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-%E2%9D%A4-ea4aaa?logo=githubsponsors)](https://github.com/sponsors/iamteedoh)
[![Patreon](https://img.shields.io/badge/Patreon-support-f96854?logo=patreon)](https://patreon.com/iamteedoh)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-ffdd00?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/iamteedoh)

A tool to check if the connectivity of a system exists between source and destination

## What's in the repo

- `chkports.py` — interactive TCP port checker. Prompts for the ports to test,
  takes hosts from command-line arguments or from a file, and prints a
  color-coded SUCCESS/FAILED line per host:port pair.
- `connchk.py` — runner around the same check. Prompts whether to run locally
  or on a remote host; remote mode connects over SSH (paramiko), copies
  `chkports.py` to `/tmp` on the remote machine, executes it there, prints the
  output, and removes the file afterwards.

## Requirements

- Python 3
- `colorama` (both scripts) and `paramiko` (`connchk.py` remote mode):

```bash
python -m pip install -r requirements.txt
```

## Usage

### Check ports from the local machine

Hosts as command-line arguments (answer `c` at the prompt):

```bash
python3 chkports.py 192.0.2.10 192.0.2.20
```

Hosts from a file, one per line (answer `f` at the prompt and pass the
filename as the only argument):

```bash
python3 chkports.py hosts.txt
```

Either way, the script then asks for the ports to test (comma-separated),
for example `22,80,443`, and checks every host against every port with a
3-second timeout.

### Run the check locally or on a remote host

```bash
python3 connchk.py <hosts-or-filename>
```

`connchk.py` first asks whether to run locally (`l`) or on a remote host
(`r`). Remote mode prompts for a username, password, and the remote host IP
(for example `192.0.2.50`), then runs the port check from that machine.

Note: remote mode auto-accepts unknown SSH host keys (`AutoAddPolicy`). Be
careful with this outside of environments you control — don't blindly trust
host keys of systems you don't recognize.

## License

connchk is licensed under the [GNU General Public License v3](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, the validation
suite, and the pull request process.

## Security

Please report vulnerabilities privately — see [SECURITY.md](SECURITY.md).
Never include passwords, SSH keys, or private host details in public issues.
