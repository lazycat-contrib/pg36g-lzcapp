"""Validate and annotate the generated book, without executing book examples."""
import html
import re
import sys
import shutil
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

root = Path(sys.argv[1]).resolve()
commit = sys.argv[2]
theme = Path(sys.argv[3]).resolve()
legal_files = [p for p in theme.rglob('*') if p.is_file() and p.name.lower().startswith(('license', 'copying', 'notice'))]
assert legal_files, 'Theme license files missing'
for legal in legal_files:
    target = root / 'licenses' / 'OINK' / legal.relative_to(theme)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(legal, target)
print(f'Bundled theme/third-party legal notices: {len(legal_files)} files')
pages = list(root.rglob('*.html'))
assert len(pages) >= 40, f'Incomplete book output: {len(pages)} HTML pages'
assert (root / 'index.html').is_file()
assert (root / 'toc' / 'index.html').is_file()
assert (root / 'LICENSE.txt').is_file()
footer = '<footer style="padding:1rem;text-align:center;font-size:.85rem">阅读包署名与许可：<a href="/package-notice.html">Vonng · CC BY-NC-SA 4.0 · 仅限非商业</a></footer>'
pattern = re.compile(r'((?:href|src)=[\"\x27])https://pg36g\.vonng\.com(?::443)?/')
missing_assets = set()
external_assets = set()

class Assets(HTMLParser):
    def __init__(self, page):
        super().__init__()
        self.page = page
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        target = a.get('src') if tag in ('script', 'img') else a.get('href') if tag == 'link' and a.get('rel') == 'stylesheet' else None
        if not target or target.startswith(('data:', '#')):
            return
        u = urlsplit(target)
        if u.scheme or u.netloc:
            external_assets.add(target)
            return
        path = unquote(u.path)
        resolved = (root / path.lstrip('/')) if path.startswith('/') else (self.page.parent / path)
        if not resolved.is_file():
            missing_assets.add((str(self.page.relative_to(root)), target))

for page in pages:
    text = pattern.sub(r'\1/', page.read_text(encoding='utf-8'))
    text = text.replace('</body>', footer + '</body>')
    page.write_text(text, encoding='utf-8')
    Assets(page).feed(text)

notice = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PG 三十六计：阅读包署名与许可</title><body style="max-width:52rem;margin:3rem auto;padding:1rem;font-family:sans-serif;line-height:1.8"><h1>PG 三十六计：阅读包署名与许可</h1><p>作者：<a href="https://vonng.com/">Vonng（冯若航）</a>。<a href="https://pg36g.vonng.com/">原站</a> · <a href="https://github.com/Vonng/pg36g">源码</a>。内容快照：<code>{html.escape(commit)}</code>。</p><p>原内容按 <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a> 许可：署名、非商业、相同方式共享。<a href="/LICENSE.txt">完整许可证</a>。本阅读包不收费，不提交官方商店激励。</p><p>改动仅涉及静态站本地构建、站内绝对链接改为本地、禁用 Google Analytics 及附加署名许可入口；书籍正文不作编辑。2026.10.31 为阅读包版本，不代表作者发行版。主题 OINK v1.4.0 使用 Apache-2.0，独立许可与随附声明保存在 /licenses/OINK/ 目录；原站为更新与勘误的权威来源。</p><p>本包仅阅读，不运行 PostgreSQL 或 Pigsty，不执行书中 SQL 或 shell 示例。实验可能含破坏性操作，请在隔离环境人工审查后使用。外部参考链接、字体和服务可能仍需联网。本轻量版保留普通章节，不生成重复的汇总打印、Markdown或LLMS导出。本地生成不等于已通过实机阅读、搜索、打印或实验运行验证。</p><p><a href="/">进入阅读</a></p></body></html>'''
(root / 'package-notice.html').write_text(notice, encoding='utf-8')
print(f'Static output: {len(pages)} HTML pages; {len(external_assets)} external asset references; {len(missing_assets)} missing local assets')
for item in sorted(missing_assets)[:20]:
    print('Missing local asset:', item)
assert not missing_assets, 'Generated book has missing local script/image/style assets'
