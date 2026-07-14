# Security Policy

## Reporting a vulnerability

**Do not report security vulnerabilities through public GitHub issues.**

Use GitHub's private vulnerability reporting instead:

1. Open the repository's **Security** tab.
2. Select **Report a vulnerability**.
3. Provide the details requested below.

If private reporting is unavailable, contact the maintainer through the
[iamteedoh GitHub profile](https://github.com/iamteedoh).

## What to include

- A description of the issue and its potential impact
- Reproduction steps or a minimal proof of concept
- The affected release, commit, platform, and component
- A suggested remediation, if known

Never include live passwords, SSH keys, private hostnames, host lists, or
unredacted logs in a report.

## Security-sensitive areas

connchk opens network connections and can execute a script on a remote host
over SSH, so the most sensitive surfaces are:

- SSH credential handling in `connchk.py` (username and password prompts)
- SSH host-key acceptance (`AutoAddPolicy` trusts unknown hosts on first use)
- Copying `chkports.py` to `/tmp` on the remote host and executing it there
- Parsing of user-supplied host lists and port input
- Outbound TCP connection checks against user-supplied hosts and ports

## Supported versions

Security fixes land on `main` and ship in the next tagged source release. Test
against the latest release or `main` before reporting an issue.
