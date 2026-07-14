# Contributing to connchk

Thanks for helping improve connchk. This guide covers local setup,
validation, and the pull request process.

## Ways to contribute

- **Report a bug** using the repository's bug report form.
- **Request a feature** using the feature request form.
- **Send a pull request** after opening an issue for non-trivial changes.
- **Report a vulnerability privately** by following [SECURITY.md](SECURITY.md).

## Prerequisites

- Python 3.12
- `colorama` (both scripts) and `paramiko` (`connchk.py` remote mode)
- gitleaks 8.30.1 or newer

## Set up from a clean clone

```bash
git clone https://github.com/iamteedoh/connchk.git
cd connchk

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Never commit `.env` files, tokens, passwords, SSH keys, or host lists
containing private infrastructure details.

## Run the validation suite

Run the same checks that protect `main`:

```bash
python -m compileall -q .
gitleaks git . --config .gitleaks.toml --redact --no-banner
```

When changing script behavior, exercise the affected run mode locally against
hosts you control. Do not point checks at systems you are not authorized to
probe while testing.

## Project layout

- `chkports.py` — interactive TCP port checker run on the local machine
- `connchk.py` — runner that performs the check locally or copies
  `chkports.py` to a remote host over SSH and executes it there
- `.github/workflows/` — source validation and source-only release automation

## Pull request process

1. Create a branch from `main`.
2. Make the smallest complete change and update documentation.
3. Run the full validation suite above.
4. Use a [Conventional Commit](https://www.conventionalcommits.org/) PR title:
   `feat:`, `fix:`, `docs:`, `refactor:`, `ci:`, `test:`, or `chore:`.
5. Complete the pull request template and link the related public issue.
6. Wait for all required checks to pass, then squash-merge.

The PR title becomes the squash commit subject and drives release-please:
`fix:` creates a patch release, `feat:` creates a minor release, and a `!` or
`BREAKING CHANGE:` footer creates a breaking release.

## License

By contributing, you agree that your contributions are licensed under the
project's [GNU General Public License v3](LICENSE).
