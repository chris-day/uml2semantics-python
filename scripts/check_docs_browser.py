"""Exercise rendered documentation and consent under the production URL subpath."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlsplit
import json
import tomllib
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
CONFIG = tomllib.loads((ROOT / 'zensical.toml').read_text())['project']
PREFIX = urlsplit(CONFIG['site_url']).path
ARTIFACTS = ROOT / '.cache/docs-verification'
ARTIFACTS.mkdir(parents=True, exist_ok=True)

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path.startswith(PREFIX):
            path = '/' + path[len(PREFIX):]
        return super().translate_path(path)

    def log_message(self, *args):
        pass

server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(ROOT / 'site')))
Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}' + PREFIX
results = {}
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1365, 'height': 900})
        # Zensical uses closed shadow roots for Mermaid. Capture references for
        # inspection without changing the roots' mode or production assets.
        context.add_init_script('''
          window.diagramRoots = [];
          const attach = Element.prototype.attachShadow;
          Element.prototype.attachShadow = function(options) {
            const root = attach.call(this, options);
            window.diagramRoots.push(root);
            return root;
          };
        ''')
        page = context.new_page()
        external = []
        errors = []
        failures = []
        page.on('request', lambda r: external.append(r.url) if urlsplit(r.url).hostname != '127.0.0.1' else None)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('response', lambda r: failures.append(f'{r.status} {r.url}') if r.status >= 400 else None)
        page.goto(base, wait_until='networkidle')
        expect(page.get_by_text('Privacy preferences', exact=True)).to_be_visible()
        assert not page.locator('input[name=github]').is_checked()
        assert not external, external
        assert page.locator('a.md-source').first.get_attribute('href') == CONFIG['repo_url']
        assert 'Made with' not in page.locator('body').inner_text()
        dimensions = page.evaluate('''async () => {
          const image = new Image();
          image.src = document.querySelector('link[rel="icon"]').href;
          await image.decode();
          return [image.naturalWidth, image.naturalHeight];
        }''')
        assert min(dimensions) > 0
        results['favicon_dimensions'] = dimensions
        results['before_selection'] = {'external': list(external), 'storage': page.evaluate('({...localStorage})')}
        page.get_by_role('button', name='Reject', exact=True).click()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(500)
        assert not external, external
        results['rejected'] = {'external': list(external), 'storage': page.evaluate('({...localStorage})')}
        page.get_by_role('link', name='Change cookie settings').click()
        expect(page.get_by_text('Privacy preferences', exact=True)).to_be_visible()
        assert not page.locator('input[name=github]').is_checked()
        page.get_by_text('Manage settings', exact=True).click()
        page.locator('label').filter(has_text='GitHub repository statistics').click()
        page.get_by_role('button', name='Accept', exact=True).click()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1500)
        assert any(url.startswith('https://api.github.com/') for url in external), external
        assert all(urlsplit(url).hostname == 'api.github.com' for url in external), external
        results['accepted'] = {'external': list(external), 'storage': page.evaluate('({...localStorage})')}
        page.get_by_role('link', name='Change cookie settings').click()
        expect(page.get_by_text('Privacy preferences', exact=True)).to_be_visible()
        assert page.locator('input[name=github]').is_checked()
        external.clear()
        page.get_by_role('button', name='Reject', exact=True).click()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(500)
        assert not external, external
        results['revoked'] = {'external': list(external), 'storage': page.evaluate('({...localStorage})')}
        diagram_count = 0
        for name in [n for group in CONFIG['plugins']['llmstxt']['sections'].values() for n in group]:
            print('Checking', name, flush=True)
            page.goto(base + name.replace('.md', '.html'), wait_until='networkidle')
            expected = (ROOT / 'docs' / name).read_text().count('```mermaid')
            if expected:
                page.wait_for_function('(n) => window.diagramRoots.filter(r => r.querySelector("svg[id^=__mermaid]")).length === n', arg=expected)
                assert page.evaluate('window.diagramRoots.filter(r => r.host.classList.contains("mermaid")).every(r => !r.textContent.includes("Syntax error") && r.host.getBoundingClientRect().height > 20)')
                diagram_count += expected
            assert 'Syntax error in text' not in page.locator('body').inner_text()
            if name in ('index.md', 'Examples.md', 'TSV-Specification.md'):
                page.screenshot(path=str(ARTIFACTS / (name + '.png')), full_page=True)
        page.goto(base, wait_until='networkidle')
        page.keyboard.press('Control+k')
        page.keyboard.insert_text('datatype')
        page.wait_for_function('window.diagramRoots.some(r => r.querySelector("dialog") && [...r.querySelectorAll("a")].some(a => a.href.includes("Datatypes-and-Facets")))')
        results['search'] = 'PASS: datatype results displayed'
        page.set_viewport_size({'width': 390, 'height': 844})
        page.keyboard.press('Escape')
        page.mouse.move(0, 0)
        page.screenshot(path=str(ARTIFACTS / 'mobile.png'), full_page=True)
        assert not external, external
        assert not errors, errors
        assert not failures, failures
        results.update(diagrams=diagram_count, page_errors=errors, http_errors=failures)
        browser.close()
finally:
    server.shutdown()
    (ARTIFACTS / 'browser.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results, indent=2))
