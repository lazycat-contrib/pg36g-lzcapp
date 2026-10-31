#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
WORK=$(mktemp -d "$ROOT/.build-pg36g.XXXXXX")
trap 'rm -rf -- "$WORK"' EXIT
SOURCE_SHA=602940b87754a3b16fadf82009b983308669e2c4
HUGO_SHA=787f100057328824f38c6ad7c87ff10d6451ae0a7bc39cedaad0dd2bcde17e53
mkdir -p "$WORK/tools" "$ROOT/content/site"
curl -fsSL --retry 2 https://github.com/gohugoio/hugo/releases/download/v0.168.0/hugo_extended_0.168.0_linux-amd64.tar.gz -o "$WORK/hugo.tar.gz"
printf '%s  %s\n' "$HUGO_SHA" "$WORK/hugo.tar.gz" | sha256sum -c -
tar -xzf "$WORK/hugo.tar.gz" -C "$WORK/tools" hugo
git clone --depth 1 https://github.com/Vonng/pg36g.git "$WORK/source"
if [ "$(git -C "$WORK/source" rev-parse HEAD)" != "$SOURCE_SHA" ]; then
  git -C "$WORK/source" fetch --depth 1 origin "$SOURCE_SHA"
  git -C "$WORK/source" checkout --detach FETCH_HEAD
fi
test "$(git -C "$WORK/source" rev-parse HEAD)" = "$SOURCE_SHA"
grep -Eqi 'NonCommercial|BY-NC-SA' "$WORK/source/LICENSE"
cat > "$WORK/offline.json" <<'JSON'
{"baseURL":"/","canonifyURLs":false,"relativeURLs":false,"services":{"googleAnalytics":{"ID":""}},"outputs":{"home":["HTML"],"page":["HTML"],"section":["HTML","RSS"]}}
JSON
export GOWORK=off HUGO_MODULE_WORKSPACE=off
unset HUGO_MODULE_REPLACEMENTS
cd "$WORK/source"
go mod download
go mod verify
"$WORK/tools/hugo" version
"$WORK/tools/hugo" --environment production --config "hugo.yaml,$WORK/offline.json" --baseURL / --destination "$ROOT/content/site" --cacheDir "$WORK/hugo-cache" --gc --minify
cp LICENSE "$ROOT/content/site/LICENSE.txt"
printf '%s\n' "$SOURCE_SHA" > "$ROOT/content/site/UPSTREAM-COMMIT.txt"
THEME_DIR=$(go list -m -f '{{.Dir}}' github.com/pgsty/oink)
python3 "$ROOT/scripts/finalize-site.py" "$ROOT/content/site" "$SOURCE_SHA" "$THEME_DIR"
