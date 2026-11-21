#!/usr/bin/env bash
# Ersetzt (oder entfernt) den Ordner eines Branches auf gh-pages und erneuert die Startseite.
# Umgebung: BRANCH, LOESCHEN (true/false), QUELLE (fertige Testseiten), GH_TOKEN, GITHUB_REPOSITORY, RUNNER_TEMP;
#           ZIEL_URL ersetzt zum Ausprobieren das Repository (z. B. ein lokales Bare-Repository).
#
# gh-pages besteht immer aus genau einem Commit (die Testseiten sind groß, ihre Geschichte wird nicht gebraucht).
# Parallele Läufe verschiedener Branches schützt --force-with-lease: Hat sich gh-pages seit dem Abholen geändert,
# wird neu abgeholt und erneut versucht.
set -euo pipefail

ORDNER=$(printf '%s' "$BRANCH" | tr '/' '-' | tr -c 'A-Za-z0-9._-' '-')
URL="${ZIEL_URL:-https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git}"
HIER=$(cd "$(dirname "$0")" && pwd)
D="$RUNNER_TEMP/gh-pages"

for versuch in 1 2 3 4 5 6; do
  rm -rf "$D"
  mkdir -p "$D"
  git -C "$D" init -q -b gh-pages
  git -C "$D" remote add origin "$URL"
  ALT=""
  if git -C "$D" fetch -q --depth 1 origin gh-pages 2>/dev/null; then
    ALT=$(git -C "$D" rev-parse FETCH_HEAD)
    git -C "$D" checkout -q FETCH_HEAD -- .
  fi
  touch "$D/.nojekyll"
  rm -rf "${D:?}/$ORDNER"
  if [ "$LOESCHEN" != "true" ]; then
    cp -r "$QUELLE" "$D/$ORDNER"
  fi
  python3 "$HIER/startseite.py" "$D"
  git -C "$D" add -A
  git -C "$D" -c user.name="github-actions[bot]" -c user.email="41898282+github-actions[bot]@users.noreply.github.com" \
    commit -q -m "Testseiten: $BRANCH" --allow-empty
  if [ -n "$ALT" ]; then
    LEASE="--force-with-lease=gh-pages:$ALT"
  else
    LEASE="--force-with-lease=gh-pages:"
  fi
  if git -C "$D" push -q "$LEASE" origin HEAD:gh-pages; then
    echo "Veröffentlicht: $ORDNER ($([ "$LOESCHEN" = "true" ] && echo entfernt || echo aktualisiert))"
    exit 0
  fi
  echo "gh-pages hat sich zwischenzeitlich geändert, neuer Versuch ($versuch) …"
  sleep $((versuch * 5))
done
echo "Veröffentlichen fehlgeschlagen." >&2
exit 1
