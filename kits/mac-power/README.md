# Kit: mac-power

Two power modes for a Mac: **prezi** (the display never sleeps, on battery too) and **agent** (lid closed, display off, the Mac keeps working, on battery too). The why, the setup and the pitfalls are in the playbook: [`playbooks/keep-your-mac-awake.md`](../../playbooks/keep-your-mac-awake.md).

| File | What it does | Install |
|---|---|---|
| `mac-power.zsh` | `prezi`, `agent-on`, `agent-off`, `power` | `source` it from `~/.zshrc` |
| `agent-focus` | Called by the "Agent On" / "Agent Off" shortcuts; switches agent mode, logs every run, writes a marker file | copy to `~/.local/bin/`, `chmod +x` |
| `lid-watch.sh` | In agent mode, sleeps the display when the lid closes | run in the background or as a LaunchAgent |

State, logs and pid files go to `~/.local/state/mac-power/` (change with `MAC_POWER_STATE`).

## The sudoers rule (you run this once, yourself)

Exactly two commands, nothing else:

```bash
echo "$(whoami) ALL=(root) NOPASSWD: /usr/bin/pmset -a disablesleep 0, /usr/bin/pmset -a disablesleep 1" > /tmp/mac-power && sudo visudo -cf /tmp/mac-power && sudo install -m 440 -o root -g wheel /tmp/mac-power /etc/sudoers.d/mac-power && rm /tmp/mac-power
```

Undo: `sudo rm /etc/sudoers.d/mac-power`.

## lid-watch as a LaunchAgent

Save as `~/Library/LaunchAgents/local.mac-power.lid-watch.plist` (replace the path), then `launchctl load` it:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>local.mac-power.lid-watch</string>
  <key>ProgramArguments</key><array><string>/bin/sh</string><string>/ABSOLUTE/PATH/lid-watch.sh</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict></plist>
```
