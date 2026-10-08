#!/bin/sh
# Professional Camera Man — Created by Caleb Elizondo
# Asks how you want to set up your studio, then starts it.
set -e
cd "$(dirname "$0")"
command -v python3 >/dev/null 2>&1 || { echo "Python 3.8+ is required: https://www.python.org/downloads/"; exit 1; }
echo "Professional Camera Man — Created by Caleb Elizondo"
echo
if [ -f data/profile.json ]; then
  echo "You already have a studio profile (data/profile.json). Run  python3 pcm.py setup  to redo it."
else
  echo "How do you want to describe your studio (look, camera, lights, distances)?"
  echo "  1) In the browser — recommended (the wizard opens by itself)"
  echo "  2) Here in the terminal"
  echo "  3) Later"
  printf "> [1] "; read -r choice
  [ "$choice" = "2" ] && python3 pcm.py setup
fi
URL="http://localhost:8770"
( sleep 1.5; (command -v open >/dev/null 2>&1 && open "$URL") || (command -v xdg-open >/dev/null 2>&1 && xdg-open "$URL") || true ) &
exec python3 pcm.py
