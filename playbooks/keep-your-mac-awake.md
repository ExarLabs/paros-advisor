---
title: keep-your-mac-awake
date: 2026-10-11
status: active
description: Playbook for two Mac power modes. Prezi keeps the display on while presenting, on battery too, and a slide deck can switch it on by itself. Agent keeps the Mac working with the lid closed so long agent runs finish, on battery too, with the display off. Both switch from the terminal and from a Focus in Control Center, need only a two-command sudo rule, and cannot be left on by mistake (timer, battery guard). Intent first, so it carries to other machines.
---

# Playbook: keep your Mac awake, on purpose

## What you get

- **Prezi mode:** the screen does not dim or sleep during a talk, also on battery. A deck in full screen can switch it on by itself.
- **Agent mode:** close the lid, the display goes dark, and the Mac keeps working: your agents, builds and long runs finish. Also on battery.
- One switch for each, in the terminal (`prezi`, `agent-on`, `agent-off`, `power`) and as an **"Agent" Focus** in Control Center and the menu bar (also from your phone).
- No way to forget it on: a timer, a battery guard, and a deck signal that expires.

Scripts: [`kits/mac-power/`](../kits/mac-power/README.md).

## When the advisor offers it

When the person runs long agent sessions on a laptop, mentions that a run stopped because the Mac went to sleep, or that the screen went dark during a presentation.

## The intent (carry this to any machine)

1. **Two modes, because two needs.** A presenter needs the *display*. An agent needs the *processor*; a lit display under a closed lid only heats and drains. Merging them gives you the worst of both.
2. **A deliberate, visible state, not a changed setting.** A changed system setting gets forgotten. A Focus named "Agent" shows in the menu bar, switches from Control Center and the phone, and is the same gesture as Do Not Disturb.
3. **Every way in has a way out without you.** A timer (default 4 hours), a battery guard (off below 15%), a deck signal that expires. A closed laptop running on battery in a bag is the outcome to design against.
4. **The narrowest permission.** Agent mode needs root. Grant exactly two commands without a password (`disablesleep 1` and `disablesleep 0`), never a broad `pmset` or general sudo.
5. **One source of truth.** Every switch sets and reads the system state itself (`pmset -g`), never a private copy that can drift. Where the state cannot be read (the Focus store is privacy-protected), a marker file is the fallback, and you say so.
6. **What can happen by itself, should.** The deck switches prezi on when it goes full screen; closing the lid in agent mode turns the display off.
7. **Log every step.** Shortcuts error messages say nothing; a small logging helper turns an hour of guessing into a minute of reading.

## Steps

### 1. Read the state (no root)

```bash
pmset -g | grep -E 'SleepDisabled|displaysleep'
```

`SleepDisabled 1` means agent mode is on. `pmset -g batt` gives power source and percentage; `ioreg -r -k AppleClamshellState -d 4 | grep AppleClamshellState` gives the lid.

### 2. Prezi mode (no root)

`caffeinate -d -t <seconds>` keeps the display awake and stops by itself. A long-running process that owns it should add `-w <its pid>`, so it can never outlive its owner.

### 3. The sudoers rule (the person runs it, once)

Show the one-line command from the kit README and let the person run it themselves. It writes to a temp file, validates it with `visudo -cf` (a broken sudoers file can lock you out of sudo), and only then installs it. Never write into `/etc/sudoers.d/` directly.

### 4. Terminal commands

Source `kits/mac-power/mac-power.zsh` from `~/.zshrc` (show the line first, add it with a yes).

### 5. The Agent Focus (the person clicks, you guide)

1. System Settings › Focus › add a custom Focus named `Agent`.
2. Copy `kits/mac-power/agent-focus` to `~/.local/bin/` and make it executable.
3. Shortcuts › Settings › Advanced › turn on **Allow Running Scripts**.
4. Two shortcuts:
   - **Agent On:** *Set Focus* (Agent, on, until turned off), then *Run Shell Script* `~/.local/bin/agent-focus on`.
   - **Agent Off:** *Set Focus* (Agent, off), then *Run Shell Script* `~/.local/bin/agent-focus off`.
   - Leave *Run as Administrator* off: the sudoers rule grants the right, not the shortcut.
5. Two automations: *When Agent is turned on* › run "Agent On"; *When Agent is turned off* › run "Agent Off". Run immediately, no notification.
6. Test: turn the Focus on, check `pmset -g | grep SleepDisabled` and the log in `~/.local/state/mac-power/agent-focus.log` (`pmset exit 0`); then off.

`agent-on` and `agent-off` run the same shortcuts, so the terminal and the Focus always agree.

### 6. Display off under the closed lid

Run `kits/mac-power/lid-watch.sh` (in the background or as a LaunchAgent). Check with `pmset -g log | grep -i "display is turned off"`.

### 7. Optional: a deck that keeps the screen on

In your slide engine: when the deck fills the screen and is visible, request a **Screen Wake Lock** (works on any machine, no setup). If you run a local service that holds `caffeinate`, the deck can also send it a heartbeat every 30 s, and the service drops prezi mode when the heartbeat stops (for example after 75 s). Send the heartbeat only from local origins (`file:`, `localhost`) or after an explicit opt-in, so audience browsers never get a local-network permission prompt.

## Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `sudo -n -l <cmd>` says yes, but there is no passwordless rule | For an admin with `(ALL) ALL`, `sudo -l <cmd>` answers yes even when a password would be asked | Read the whole `sudo -n -l` listing and look for the command on a `NOPASSWD:` line |
| That search sometimes misses | Without a terminal, sudo wraps long rule lines (rules indented 4 spaces, continuations 8) | Join only newlines followed by 8 or more spaces |
| A background service cannot read the Focus state (EPERM) | `~/Library/DoNotDisturb/DB/` is privacy-protected (TCC); a launchd service without Full Disk Access is denied | The shortcut helper writes a marker file; do not grant Full Disk Access just for this |
| The Focus automation has no place for a script | On recent macOS, "When Focus turns on/off" can only run an existing shortcut | Two shortcuts, the automations run them |
| "Run Shell Script finished with an error" although pmset worked | Unknown, on the Shortcuts side | A logging helper that always exits 0; read the log, not the Shortcuts message |
| The display stays lit under the closed lid | With `disablesleep 1` the internal display does not always sleep | `lid-watch.sh` and `pmset displaysleepnow` |
| Stopping the timer killed its own shell | `pkill -f <pattern>` inside `sh -c` also matches its own command line | A pid file and a targeted `kill` |
| An unattended scheduled agent run waited all night | It stopped at its first tool permission prompt | Pre-approve the tools with one manual run before scheduling; agent mode only helps when the run is truly unattended |

## Safety and advice

- **Heat.** A closed Mac working hard heats up. Leave it on a hard surface, not in a bag. The battery guard is for the worst case, not for planned use.
- **Timer by default.** `agent-on 0` (no timer) only when someone is watching.
- **Keep the rule narrow.** `pmset` can also schedule wake-ups and change hibernation; a broad rule opens those too.
- **Other systems, same intent.** Linux: `systemd-inhibit --what=sleep:handle-lid-switch` for agent mode, the desktop's inhibit or wake lock for prezi. Windows: lid action "Do nothing" plus a standby timeout of 0 for agent mode, `SetThreadExecutionState` or a presentation setting for prezi.

## What the advisor does and does not do

- Reads the state and explains it; writes the kit files and the `~/.zshrc` line with a yes.
- Never runs `sudo` or installs the sudoers rule itself: the person runs that one command.
- Never changes system power settings permanently.
