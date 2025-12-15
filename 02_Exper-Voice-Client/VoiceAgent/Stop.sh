#!/usr/bin/env bash
set -e
PIDFILE="$HOME/EjOS/ejos_voice/voice.pid"
if [ ! -f "$PIDFILE" ]; then
  echo "PID dosyası yok."
  exit 0
fi
PID="$(cat "$PIDFILE" || true)"
if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "Durduruldu: $PID"
fi
rm -f "$PIDFILE"
