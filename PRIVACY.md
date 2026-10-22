# Privacy: the anonymous usage ping

The advisor counts how often it is used, so we know whether people use it and which versions and systems to support. It does this without any identifier and without asking for consent, because nothing it sends can be tied to you.

## When it is sent

Once each time the installer runs: when you install the advisor, and every time you type `/paros` (the command first refreshes the advisor with `install.py --update`). Nothing runs in the background, and nothing is sent between runs.

## What is sent

| Field | Example | Why |
|---|---|---|
| event | `install`, `update` or `use` | first install, a new version arrived, or a normal run |
| version, from_version | `0.14.0`, `0.13.0` | which versions are in use, how fast updates spread |
| os, os_release | `Windows`, `10` | which systems to test on |
| agent | `claude-code`, `codex`, `unknown` | which agent apps to support |
| language | `Hungarian_Hungary` | which languages to write guides in |
| install_method | `git` or `zip` | whether the no-git path is used |

The server adds the date (day only) and the country, derived from the connection by Cloudflare.

## What is not sent or stored

- No name, e-mail, account, machine name, user name or any random or persistent identifier.
- No IP address is stored. The server uses it only in memory, for an hourly rate limit, and forgets it.
- Nothing from your vault, your notes, your files or your conversations.

Because there is no identifier, we cannot tell two runs of the same person apart, and we cannot find, show or delete "your" records: there are none that point to you.

## Where it goes and how long it stays

The ping goes to `https://ignis.academy/api/paros-ping` (a Cloudflare worker) and is stored as one row per run in our CRM. Rows are kept for at most 24 months; reports use only counts. The data controller is the maintainer of this repository (ExarLabs). Questions: send them with `tools/feedback.py` or open an issue in this repository.

## Turn it off

Either of these stops the ping completely; everything else keeps working:

- set the environment variable `PAROS_NO_PING=1`, or
- create an empty file named `.no-ping` in the advisor folder (by default `~/.paros-advisor/.no-ping`). Updates keep this file.

The code is in `install/install.py` (the `ping` function); you can read exactly what is sent.

## The plugin sends nothing

The PAROS plugin (Claude Cowork, or Claude Code through `/plugin`) does not run the installer, so it sends no usage ping at all. Only the `/paros` command, through `install.py`, sends the ping described above.
