"""Privacy rules for public course copies; source notes remain private."""
import re
from pathlib import Path

PUBLIC_METADATA = {'title', 'type', 'level', 'source', 'topics', 'aliases', 'tags', 'description'}

def public_text(text: str, relative: Path) -> str:
    if relative == Path('progress.md'):
        return '# Прогресс обучения\n\n[← Карта обучения](index.md)\n\nЛичные отметки прохождения хранятся только в локальной базе.\n'
    if relative == Path('references/index.md'):
        return '# Источники структуры\n\n[← Карта обучения](../index.md)\n\n- [AI Engineer Roadmap](https://roadmap.sh/ai-engineer)\n- [Публичный PDF roadmap](https://roadmap.sh/pdfs/roadmaps/ai-engineer.pdf)\n\nПользовательские снимки и отметки обучения хранятся только локально.\n'
    if relative.parts[0] == 'practice':
        return '# Практика\n\n[← Карта обучения](../index.md)\n\nЛичные записи практики хранятся только в локальной базе.\n'
    text = re.sub(r'(?ms)^## Моя практика и выводы\s*\n.*?(?=^## |\Z)', '', text)
    text = re.sub(r'Прохождение (?:этого раздела|этих тем)[^.]*\.\s*', '', text)
    text = re.sub(r'(?m)^Отметки ниже сохраняют факт прохождения[^\n]*\n?', '', text)
    text = re.sub(r'(?m)^Пользователь[^\n]*\n?', '', text)
    text = re.sub(r'(?m)^> (?:Пройдено|Прохождение|Пользователь|Изучается|Изучаю)[^\n]*\n?', '', text)
    text = re.sub(r'(?m)^\s*- \[x\]', '- [ ]', text, flags=re.I)
    text = re.sub(r'(?m)^(?:> |\*\*)?Статус: изучаю[^\n]*\n?', '', text)
    text = re.sub(r'Пользователь (?:сообщил|прислал|проходит)[^.]*\.\s*', '', text)
    text = re.sub(r'Все 13 тем записаны в статусе «изучаю», без отметки завершения\.\s*', '', text)
    text = re.sub(r'Введение пройдено по сообщению пользователя [^.]*\.\s*', '', text)
    text = text.replace('из пройденного блока', 'базового блока')
    text = text.replace(' — изучаю', '')
    text = re.sub(r'Сейчас изучается Fundamentals;[^.]*\.\s*', '', text)
    text = text.replace('Остальные подразделы пока без отметок прохождения. ', '')
    text = text.replace('Пройден Core LLM Elements; остальные объяснения и самостоятельная практика не отмечаются автоматически завершёнными.', 'Core LLM Elements объединяет базовые понятия работы с LLM.')
    text = text.replace('пройденных', 'учебных').replace('пройденные понятия', 'учебные понятия').replace('Дополнительно пройдено', 'Дополнительные темы')
    text = re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[email скрыт]', text)
    text = re.sub(r'/(?:Users|home)/[^\s)\]<>]+', '[локальный путь скрыт]', text)
    text = re.sub(r'(?<!\w)(?:\+7|\+998|\+1)[ ()-]*(?:\d[ ()-]*){9,12}(?!\w)', '[телефон скрыт]', text)
    if text.startswith('---\n'):
        match = re.match(r'---\n(.*?)\n---\n', text, re.S)
        if match:
            keep = True
            lines = []
            for line in match.group(1).splitlines():
                if re.match(r'^[A-Za-z_][A-Za-z_-]*:', line):
                    keep = line.partition(':')[0] in PUBLIC_METADATA
                if keep:
                    lines.append(line)
            metadata = '\n'.join(lines)
            text = '---\n' + metadata + '\n---\n' + text[match.end():]
    return text
