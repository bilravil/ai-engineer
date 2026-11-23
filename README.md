# AI Engineer — конспекты

Публичная версия личной базы знаний по AI Engineer Roadmap.

**Читать:** https://bilravil.github.io/ai-engineer/

Сайт работает на Quartz 5 и GitHub Pages. Исходные конспекты ведутся в Obsidian; папка `content/` — их публикуемая копия. Изменения вносите в исходную папку курса, затем публикуйте.

## Обновление

На настроенном компьютере дважды щёлкните файл **Обновить AI Engineer.command** в папке `obsidian-memory`.

Или запустите из папки сайта:

```bash
bash scripts/publish.sh
```

По умолчанию курс читается из `~/obsidian-memory/roadmap-ai-engineer`. Для другой папки:

```bash
AI_ENGINEER_SOURCE=/путь/к/курсу bash scripts/publish.sh
```

Команда проверяет экспорт, переносит заметки, собирает сайт, проверяет ссылки, отправляет исходники в `main`, готовый сайт в `gh-pages` и ждёт окончания публикации GitHub Pages. Сборка выполняется на компьютере; дополнительные разрешения для GitHub Actions не нужны. При ошибках сборки или ссылок изменения не отправляются. Новые Markdown-страницы появляются в дереве автоматически; авторские оглавления редактируются в исходных заметках. Удалённые заметки удаляются из сайта при следующей публикации.

Экспортируются только `.md`, `.pdf` и изображения курса. Скрытые файлы, символические ссылки, `AGENTS.md` и `CLAUDE.md` исключены. Настройки и скрипты сайта также публичны; остальные папки Obsidian не публикуются.

## Установка на другом компьютере

Нужны Git, Python 3, Node.js 24 с npm и GitHub CLI с выполненным `gh auth login`.

```bash
git clone https://github.com/bilravil/ai-engineer.git
cd ai-engineer
npm ci
npx quartz plugin install --from-config
bash scripts/publish.sh
```

На первом компьютере совместимый Node установлен локально в игнорируемой папке `.tools/`, без изменения системной версии.

## Проверки

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
npm test
npx quartz build
python3 scripts/check_site.py
```

Quartz распространяется по лицензии MIT — см. `LICENSE.txt`. Материалы курса содержат ссылки на исходные источники.
