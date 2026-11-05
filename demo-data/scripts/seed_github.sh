#!/usr/bin/env bash
# Seed real PRs and issues on GitHub from demo-data/prs/*.md and demo-data/issues/*.md,
# then write the numbers/urls back into demo-data/manifest.json.
#
#   DRY_RUN=1 demo-data/scripts/seed_github.sh    # print what would happen
#   demo-data/scripts/seed_github.sh              # do it (needs gh auth, push access)
#
# Idempotent: a PR or issue whose exact title already exists is skipped (its number is still recorded).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DATA="$ROOT/demo-data"
MANIFEST="$DATA/manifest.json"
REPO="$(sed -n 's/.*"repo": *"\([^"]*\)".*/\1/p' "$MANIFEST" | head -1)"
BASE="$(sed -n 's/.*"branch": *"\([^"]*\)".*/\1/p' "$MANIFEST" | head -1)"
DRY="${DRY_RUN:-0}"

say() { printf '%s\n' "$*" >&2; }
run() { if [ "$DRY" = 1 ]; then say "  [dry] $*"; else "$@"; fi; }

# front matter helpers (simple key: value lines)
fm() { awk -v k="$2" 'NR==1&&$0!="---"{exit} NR>1&&$0=="---"{exit} NR>1{ if (index($0,k": ")==1) { sub("^"k": *",""); gsub(/^"|"$/,""); print; exit } }' "$1"; }
body() { awk 'NR==1&&$0=="---"{infm=1;next} infm&&$0=="---"{infm=0;next} !infm{print}' "$1"; }
files_of() { fm "$1" files | tr -d '[]' | tr ',' '\n' | sed 's/^ *//;s/ *$//' | grep -v '^$'; }

cd "$ROOT"
git fetch -q origin "$BASE" || true
START_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
RESULTS="$(mktemp)"
trap 'rm -f "$RESULTS"' EXIT

say "repo=$REPO base=$BASE dry_run=$DRY"

for md in "$DATA"/prs/*.md; do
  slug="$(fm "$md" pr)"; title="$(fm "$md" title)"; branch="$(fm "$md" branch)"; author="$(fm "$md" author)"; date="$(fm "$md" date)"
  existing="$(gh pr list -R "$REPO" --state all --search "in:title \"$title\"" --json number,url,title --jq ".[] | select(.title==\"$title\") | \"\(.number) \(.url)\"" | head -1 || true)"
  if [ -n "$existing" ]; then
    printf 'prs\t%s\t%s\t%s\n' "$slug" "${existing%% *}" "${existing#* }" >> "$RESULTS"
    say "skip PR (exists): $title -> #${existing%% *}"; continue
  fi
  say "create PR: $title  [$branch] by $author on $date"
  if [ "$DRY" = 1 ]; then files_of "$md" | sed 's/^/  [dry] touch /' >&2; continue; fi
  git checkout -q -B "$branch" "origin/$BASE" 2>/dev/null || git checkout -q -B "$branch" "$BASE"
  while IFS= read -r f; do
    [ -f "$f" ] || continue
    case "$f" in
      *.json) ;;  # don't break JSON; marker goes in a sibling file instead
      *) printf '\n# %s: %s (%s)\n' "$author" "$title" "$date" >> "$f" ;;
    esac
    printf '%s\n' "$slug" > "$(dirname "$f")/.pr-$slug"
    git add "$f" "$(dirname "$f")/.pr-$slug"
  done < <(files_of "$md")
  git -c user.name="$author" -c user.email="$(echo "$author" | tr 'A-Z ' 'a-z.')@acme.example" commit -q -m "$title" --date="$date 12:00:00" || true
  git push -q -u origin "$branch" --force
  url="$(body "$md" | gh pr create -R "$REPO" --base "$BASE" --head "$branch" --title "$title" --body-file -)"
  printf 'prs\t%s\t%s\t%s\n' "$slug" "${url##*/}" "$url" >> "$RESULTS"
  say "  -> $url"
done
[ "$DRY" = 1 ] || git checkout -q "$START_BRANCH"

for md in "$DATA"/issues/*.md; do
  slug="$(basename "$md" .md)"; title="$(fm "$md" title)"
  existing="$(gh issue list -R "$REPO" --state all --search "in:title \"$title\"" --json number,url,title --jq ".[] | select(.title==\"$title\") | \"\(.number) \(.url)\"" | head -1 || true)"
  if [ -n "$existing" ]; then
    printf 'issues\t%s\t%s\t%s\n' "$slug" "${existing%% *}" "${existing#* }" >> "$RESULTS"
    say "skip issue (exists): $title -> #${existing%% *}"; continue
  fi
  say "create issue: $title"
  [ "$DRY" = 1 ] && continue
  url="$(body "$md" | gh issue create -R "$REPO" --title "$title" --body-file -)"
  printf 'issues\t%s\t%s\t%s\n' "$slug" "${url##*/}" "$url" >> "$RESULTS"
  say "  -> $url"
done

[ "$DRY" = 1 ] && { say "dry run complete, manifest untouched"; exit 0; }

# write numbers back into manifest.json
uv run python -I - "$MANIFEST" "$RESULTS" <<'PY'
import json, sys
path = sys.argv[1]
m = json.load(open(path))
for line in open(sys.argv[2]):
    kind, slug, num, url = line.rstrip("\n").split("\t")
    if slug in m.get(kind, {}):
        m[kind][slug]["number"] = int(num)
        m[kind][slug]["url"] = url
json.dump(m, open(path, "w"), indent=2)
print("manifest updated:", path)
PY
say "done. Re-run the agent indexer so {{pr:...}} references render with real numbers."
