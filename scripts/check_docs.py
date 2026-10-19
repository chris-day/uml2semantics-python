"""Validate built links, navigation, migration coverage, privacy and LLM exports."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
import json
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
config = tomllib.loads((ROOT / 'zensical.toml').read_text())['project']
base = config['site_url']
errors = []

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = set()
        self.links = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for attr in ('href', 'src'):
            if attr in attrs:
                self.links.append((tag, attrs[attr]))

pages = {p.relative_to(SITE).as_posix(): Page(p.read_text()) for p in SITE.rglob('*.html')}
for name, page in pages.items():
    for tag, link in page.links:
        url = urlsplit(urljoin(base + name, link))
        if not url.geturl().startswith(base):
            if tag in ('script', 'iframe', 'img', 'link') and url.scheme in ('http', 'https') and tag != 'link':
                errors.append(f'{name}: remote embedded resource {link}')
            continue
        path = unquote(url.path[len(urlsplit(base).path):]) or 'index.html'
        if path.endswith('/'):
            path += 'index.html'
        if not (SITE / path).is_file():
            errors.append(f'{name}: missing {link}')
        elif url.fragment and path in pages and unquote(url.fragment) not in pages[path].ids:
            errors.append(f'{name}: missing anchor {link}')

sections = config['plugins']['llmstxt']['sections']
selected = [p for paths in sections.values() for p in paths]
assert len(selected) == len(set(selected)), 'Duplicate LLM selection'
def nav_pages(items):
    for item in items:
        for value in item.values():
            if isinstance(value, list):
                yield from nav_pages(value)
            else:
                yield value

navigation = list(nav_pages(config['nav']))
assert len(navigation) == len(set(navigation)), 'Duplicate navigation entry'
assert set(navigation) == set(selected), 'Navigation and LLM coverage differ'
assert set(selected) == {p.name for p in (ROOT / 'docs').glob('*.md') if p.name != config['exclude_docs']}
index = (SITE / 'llms.txt').read_text()
for section in sections:
    assert f'## {section}' in index, section
for name in selected:
    assert (SITE / name).is_file(), f'Missing Markdown export: {name}'
    assert base + name in index, f'Missing index URL: {name}'
    for target in re.findall(r'\]\(<?([^\s)>]+)', (SITE / name).read_text()):
        if target.startswith(base):
            local = unquote(urlsplit(target).path[len(urlsplit(base).path):])
            assert (SITE / local).is_file(), f'{name}: broken exported link {target}'
assert (SITE / 'llms-full.txt').stat().st_size > 1000
assert not list(SITE.glob('*GDSN*')), 'Private draft published'
for p in SITE.glob('*.md'):
    assert '/var/software/' not in p.read_text(), f'Local path leaked: {p}'

manifest = json.loads((ROOT / 'documentation-migration/map.json').read_text())
for row in manifest:
    assert row['decision'] in ('retain', 'consolidate', 'exclude', 'adapt')
    if row['destination']:
        for target in row['destination'].split('; '):
            assert (ROOT / target).exists(), f'Missing migration target: {target}'
mapped = {row['source'] for row in manifest}
for p in (ROOT / 'docs').glob('*.md'):
    assert 'docs/' + p.name in mapped, f'Unaccounted page {p}'

home = (SITE / 'index.html').read_text()
assert config['repo_url'] in home
assert 'Made with' not in home
assert 'href="#__consent"' in home
assert 'fonts.googleapis.com' not in home
assert config['extra']['generator'] is False
assert config['extra']['consent']['cookies']['github']['checked'] is False
assert set(config['extra']['consent']['actions']) == {'accept', 'reject', 'manage'}
icon = (SITE / 'assets/images/favicon.png').read_bytes()
assert icon[:8] == b'\x89PNG\r\n\x1a\n'
assert icon == (ROOT / 'docs/assets/images/favicon.png').read_bytes()
assert 'assets/images/favicon.png' in home
assert (SITE / 'search.json').is_file()
assert not errors, '\n'.join(errors)
print(f'PASS: {len(pages)} HTML pages, {len(selected)} Markdown exports, migration coverage, favicon, privacy configuration and links')
