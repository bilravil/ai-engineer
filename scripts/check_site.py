#!/usr/bin/env python3
"""Check generated links and fragments, including GitHub Pages subpaths."""
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids, self.links = set(), []
        self.feed(path.read_text())
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'public').resolve()
pages = {path: Page(path) for path in root.rglob('*.html')}
errors = []
for path, page in pages.items():
    for href in page.links:
        link = urlsplit(href)
        if link.scheme or link.netloc:
            continue
        target = unquote(link.path)
        if target == '/ai-engineer':
            resolved = root / 'index.html'
        elif target.startswith('/ai-engineer/'):
            resolved = root / target[len('/ai-engineer/'):]
        elif target.startswith('/'):
            resolved = root / target.lstrip('/')
        else:
            resolved = path.parent / target if target else path
        resolved = resolved.resolve()
        candidates = [resolved, Path(str(resolved) + '.html'), resolved / 'index.html']
        match = next((p for p in candidates if p.is_file()), None)
        if match is None:
            errors.append(f'{path.relative_to(root)}: missing {href}')
        elif link.fragment and match in pages and unquote(link.fragment) not in pages[match].ids:
            errors.append(f'{path.relative_to(root)}: missing anchor {href}')
if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)
print(f'Проверены ссылки и якоря на {len(pages)} страницах.')
