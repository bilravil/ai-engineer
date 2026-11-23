#!/usr/bin/env python3
"""Export the course only; never modify the source vault."""
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit
from privacy import public_text

ALLOWED = {'.md', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.avif'}

def export(source, destination):
    source, destination = source.resolve(), destination.resolve()
    if not (source / 'index.md').is_file():
        raise ValueError('В папке курса отсутствует index.md; публикация остановлена.')
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError('Папки источника и сайта должны быть отдельными.')
    selected = {}
    for path in sorted(source.rglob('*')):
        rel = path.relative_to(source)
        if any(part.startswith('.') for part in rel.parts) or path.name.upper() in {'AGENTS.MD', 'CLAUDE.MD'}:
            continue
        if any(parent.is_symlink() for parent in [path, *path.parents]) or not path.is_file():
            continue
        if path.suffix.lower() in ALLOWED:
            selected[rel] = path
    errors = []
    for rel, path in selected.items():
        if path.suffix != '.md':
            continue
        text = re.sub(r'```.*?```|~~~.*?~~~', '', public_text(path.read_text(), rel), flags=re.S)
        for target in re.findall(r'!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)', text):
            parsed = urlsplit(target.strip('<>'))
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            resolved = (path.parent / unquote(parsed.path)).resolve()
            try:
                target_rel = resolved.relative_to(source)
            except ValueError:
                errors.append(f'{rel}: ссылка за пределы курса: {target}')
                continue
            if target_rel not in selected:
                errors.append(f'{rel}: отсутствует {target}')
    if errors:
        raise ValueError('\n'.join(errors))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix='.export-') as tmp:
        staged = Path(tmp) / 'content'
        staged.mkdir()
        for rel, path in selected.items():
            output = staged / rel
            output.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix != '.md':
                shutil.copyfile(path, output)
                continue
            text = public_text(path.read_text(), rel)
            frontmatter = re.match(r'\A---\n(.*?)\n---\n', text, re.S)
            metadata = frontmatter.group(1) if frontmatter else ''
            body = text[frontmatter.end():] if frontmatter else text
            heading = re.search(r'^# (.+)$', body, re.M)
            title = heading.group(1).strip() if heading else path.stem
            section = re.match(r'^(\d+)-', rel.parent.name) if path.name == 'index.md' else None
            if section:
                title = section.group(1) + '. ' + title
            if not re.search(r'^title:', metadata, re.M):
                metadata = 'title: ' + json.dumps(title, ensure_ascii=False) + '\n' + metadata
            if heading:
                body = body[:heading.start()] + body[heading.end():]
            def normalize_anchor(match):
                target = match.group(1)
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.fragment:
                    return match.group(0)
                anchor = re.sub(r'[^\w\s-]', '', unquote(parsed.fragment)).lower().replace(' ', '-')
                return '](' + target.split('#', 1)[0] + '#' + anchor + ')'
            body = re.sub(r'\]\(([^\s)]+)\)', normalize_anchor, body)
            output.write_text('---\n' + metadata.rstrip() + '\n---\n\n' + body.strip() + '\n')
        if destination.exists():
            shutil.rmtree(destination)
        staged.rename(destination)
    print(f'Экспортировано файлов: {len(selected)}')

if __name__ == '__main__':
    try:
        export(Path(sys.argv[1]), Path(sys.argv[2]))
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
