#!/bin/sh
# lid-watch.sh: in agent mode, put the display to sleep when the lid closes.
# With `pmset disablesleep 1` the system stays awake on lid close, but the
# internal display can stay lit under the closed lid. Every 2 s this reads the
# lid sensor (no root needed); on an open-to-closed change, if agent mode is on,
# it sleeps the display (`pmset displaysleepnow`, no root needed).
# Run it in the background, or as a LaunchAgent (see README.md).
prev=""
while :; do
  s=$(/usr/sbin/ioreg -r -k AppleClamshellState -d 4 | grep -o '"AppleClamshellState" = [A-Za-z]*' | awk '{print $3}')
  if [ "$s" = Yes ] && [ "$prev" = No ] && /usr/bin/pmset -g | grep -q 'SleepDisabled[[:space:]]*1'; then
    /usr/bin/pmset displaysleepnow
    echo "$(date '+%F %T') lid closed in agent mode: display off"
  fi
  [ -n "$s" ] && prev=$s
  sleep 2
done
