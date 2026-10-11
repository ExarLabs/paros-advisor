# mac-power.zsh: two power modes for a Mac, from the terminal.
# Load it from ~/.zshrc:  source /path/to/mac-power.zsh
#
#   prezi [min]    the display never sleeps, on battery too (default 180 minutes)
#   prezi off      switch it off
#   agent-on [h]   the Mac keeps running with the lid closed, on battery too.
#                  A timer switches it off after h hours (default 4, 0 = no timer),
#                  and always below 15% battery. Also turns on the "Agent" Focus.
#   agent-off      switch it off now (also turns off the "Agent" Focus)
#   power          state of both modes
#
# agent-on/off need root for `pmset -a disablesleep`. With the narrow sudoers
# rule from the playbook they run without a password; without it sudo asks.

MAC_POWER_STATE=${MAC_POWER_STATE:-$HOME/.local/state/mac-power}

prezi() {
  local pidf=$MAC_POWER_STATE/prezi.pid
  if [[ "$1" == off ]]; then
    [[ -f $pidf ]] && kill "$(<$pidf)" 2>/dev/null
    rm -f $pidf
    echo "Prezi mode: off"
    return
  fi
  local min=${1:-180}
  if [[ ! "$min" == <-> ]]; then echo "usage: prezi [minutes] | prezi off"; return 1; fi
  mkdir -p $MAC_POWER_STATE
  [[ -f $pidf ]] && kill "$(<$pidf)" 2>/dev/null
  caffeinate -d -t $((min * 60)) &!
  echo $! > $pidf
  echo "Prezi mode: on for $min minutes. Off: prezi off"
}

_mp_pmset() {
  sudo -n /usr/bin/pmset -a disablesleep "$1" 2>/dev/null || sudo /usr/bin/pmset -a disablesleep "$1"
}

# Runs the first existing shortcut of the given names (flips the Agent Focus).
_mp_focus() {
  local list name
  list=$(shortcuts list 2>/dev/null)
  for name in "$@"; do
    if print -r -- "$list" | grep -qx "$name"; then
      shortcuts run "$name" >/dev/null 2>&1
      return
    fi
  done
}

# A pid file, not `pkill -f`: inside `sh -c` a pattern kill matches its own shell.
_mp_timer_stop() {
  local f=$MAC_POWER_STATE/agent-timer.pid
  [[ -f $f ]] && kill "$(<$f)" 2>/dev/null
  rm -f $f
}

agent-on() {
  local h=${1:-4}
  if [[ ! "$h" == <-> ]]; then echo "usage: agent-on [hours]   (0 = no timer)"; return 1; fi
  _mp_pmset 1 || return 1
  _mp_timer_stop
  if (( h > 0 )); then
    mkdir -p $MAC_POWER_STATE
    nohup /bin/sh -c '
      end=$(( $(date +%s) + $1 ))
      while [ $(date +%s) -lt $end ]; do
        b=$(pmset -g batt)
        pct=$(echo "$b" | grep -o "[0-9]*%" | head -1 | tr -d %)
        if echo "$b" | grep -q discharging && [ "${pct:-100}" -lt 15 ]; then break; fi
        sleep 60
      done
      sudo -n /usr/bin/pmset -a disablesleep 0
    ' mac-power-agent-timer $(( h * 3600 )) >/dev/null 2>&1 &!
    echo $! > $MAC_POWER_STATE/agent-timer.pid
  fi
  _mp_focus "Agent On"
  if (( h > 0 )); then
    echo "Agent mode: on. Runs with the lid closed, on battery too. Off after $h h or below 15% battery. Sooner: agent-off"
  else
    echo "Agent mode: on, NO timer. Off: agent-off"
  fi
}

agent-off() {
  _mp_pmset 0 || return 1
  _mp_timer_stop
  _mp_focus "Agent Off"
  echo "Agent mode: off. Closing the lid sleeps the Mac again."
}

power() {
  pmset -g batt | sed -n 2p
  if [[ -f $MAC_POWER_STATE/prezi.pid ]] && kill -0 "$(<$MAC_POWER_STATE/prezi.pid)" 2>/dev/null; then
    echo "Prezi mode: ON"
  else
    echo "Prezi mode: off (display sleeps after $(pmset -g | awk '/^ *displaysleep/ {print $2}') min)"
  fi
  if pmset -g | grep -q 'SleepDisabled[[:space:]]*1'; then
    if [[ -f $MAC_POWER_STATE/agent-timer.pid ]] && kill -0 "$(<$MAC_POWER_STATE/agent-timer.pid)" 2>/dev/null; then
      echo "Agent mode: ON (timer running)"
    else
      echo "Agent mode: ON (no timer!)"
    fi
  else
    echo "Agent mode: off"
  fi
}
