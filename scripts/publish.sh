#!/bin/bash
set -euo pipefail
export GIT_AUTHOR_NAME=bilravil
export GIT_AUTHOR_EMAIL=13206523+bilravil@users.noreply.github.com
export GIT_COMMITTER_NAME=bilravil
export GIT_COMMITTER_EMAIL=13206523+bilravil@users.noreply.github.com
SITE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SITE_DIR"
export PATH="$SITE_DIR/.tools/node_modules/.bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
SOURCE_DIR="${AI_ENGINEER_SOURCE:-$HOME/obsidian-memory/roadmap-ai-engineer}"
command -v gh >/dev/null || { echo 'Для публикации нужен GitHub CLI (gh).'; exit 1; }
if [ ! -d node_modules ] || ! command -v node >/dev/null || [ "$(node -p 'Number(process.versions.node.split(".")[0])')" -lt 22 ]; then
  echo 'Не найдена настроенная среда сайта. См. README.md.'
  exit 1
fi
LOCK_DIR="$SITE_DIR/.local/publish.lock"
mkdir -p "$SITE_DIR/.local"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo 'Обновление уже запущено. Дождись его завершения.'
  exit 1
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT
if [ -n "$(git status --porcelain --untracked-files=normal -- . ':!content')" ]; then
  echo 'В настройках сайта есть несохранённые изменения. Сначала проверь и сохрани их.'
  exit 1
fi
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/export_notes.py "$SOURCE_DIR" content
node ./quartz/bootstrap-cli.mjs build
python3 scripts/check_site.py
# Stage course content only; unrelated vault files never enter this repository.
git add --all -- content
if ! git diff --cached --quiet; then
  git commit -m "Обновить конспекты $(date '+%Y-%m-%d %H:%M')"
fi
git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push origin main
DEPLOY_DIR="$SITE_DIR/.local/deploy-repo"
if [ ! -d "$DEPLOY_DIR/.git" ]; then
  git init -b gh-pages "$DEPLOY_DIR"
  git -C "$DEPLOY_DIR" remote add origin https://github.com/bilravil/ai-engineer.git
fi
if git -c credential.helper= -c 'credential.helper=!gh auth git-credential' -C "$DEPLOY_DIR" ls-remote --exit-code origin refs/heads/gh-pages >/dev/null 2>&1; then
  git -c credential.helper= -c 'credential.helper=!gh auth git-credential' -C "$DEPLOY_DIR" fetch --depth=1 origin gh-pages
  git -C "$DEPLOY_DIR" checkout -B gh-pages FETCH_HEAD
fi
rsync -a --delete --exclude='.git/' "$SITE_DIR/public/" "$DEPLOY_DIR/"
touch "$DEPLOY_DIR/.nojekyll"
git -C "$DEPLOY_DIR" add --all
if ! git -C "$DEPLOY_DIR" diff --cached --quiet; then
  git -C "$DEPLOY_DIR" commit -m "Обновить сайт $(date '+%Y-%m-%d %H:%M')"
fi
DEPLOY_COMMIT="$(git -C "$DEPLOY_DIR" rev-parse HEAD)"
git -c credential.helper= -c 'credential.helper=!gh auth git-credential' -C "$DEPLOY_DIR" push origin gh-pages
if [ "${AI_ENGINEER_SKIP_WAIT:-0}" = 1 ]; then
  echo 'Файлы отправлены: https://bilravil.github.io/ai-engineer/'
  exit 0
fi
echo 'Ожидаю завершения публикации GitHub Pages…'
for attempt in $(seq 1 90); do
  BUILD_INFO="$(gh api repos/bilravil/ai-engineer/pages/builds/latest --jq '[.commit, .status] | @tsv' 2>/dev/null || true)"
  IFS=$'\t' read -r BUILD_COMMIT BUILD_STATUS <<< "$BUILD_INFO"
  if [ "$BUILD_COMMIT" = "$DEPLOY_COMMIT" ]; then
    case "$BUILD_STATUS" in
      built) echo 'Сайт обновлён: https://bilravil.github.io/ai-engineer/'; exit 0 ;;
      errored) echo 'GitHub Pages не завершил публикацию. Подробности: https://github.com/bilravil/ai-engineer/actions'; exit 1 ;;
    esac
  fi
  sleep 5
done
echo 'Файлы отправлены, но GitHub ещё не подтвердил публикацию. Статус: https://github.com/bilravil/ai-engineer/actions'
exit 1
