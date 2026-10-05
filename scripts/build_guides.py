"""Publish only owner-authored, registered Markdown and PDF walkthroughs."""
import argparse
import html
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import markdown
import yaml

HOME = 'https://dollars-archive.github.io/Game-Walkthrough-Archive/'
HUB = 'https://dollars-archive.github.io/Dollars-Archive/'


def validate(root, item):
    if not isinstance(item, dict) or item.get('original') is not True:
        raise ValueError('직접 작성한 공략은 original: true 확인이 필요합니다.')
    for key in ('id', 'title', 'file'):
        if not isinstance(item.get(key), str) or not item[key].strip():
            raise ValueError(f'{key} 입력이 필요합니다.')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', item['id']):
        raise ValueError('id는 영문 소문자·숫자·하이픈으로 입력합니다.')
    source = (root / item['file']).resolve()
    guide_root = (root / 'guides').resolve()
    if not source.is_relative_to(guide_root) or not source.is_file() or source.suffix.lower() not in ('.md', '.pdf'):
        raise ValueError('파일은 guides/ 아래의 실제 Markdown 또는 PDF여야 합니다.')
    repo = item.get('patch_repo', '')
    if not isinstance(repo, str) or (repo and not re.fullmatch(r'[A-Za-z0-9_.-]+', repo)):
        raise ValueError('patch_repo는 저장소 이름이어야 합니다.')
    if not repo and (not isinstance(item.get('game'), str) or not item['game'].strip()
                     or not isinstance(item.get('platforms'), list) or not item['platforms']
                     or any(not isinstance(p, str) or not p for p in item['platforms'])):
        raise ValueError('패치가 없는 게임은 game과 platforms를 입력합니다.')
    return source


def load_patch_games():
    request = Request(HUB + 'data/patches.json', headers={'User-Agent': 'Dollars-Archive-walkthroughs'})
    with urlopen(request, timeout=30) as response:
        return {p['repo']: p for p in json.load(response)['patches']}


def updated(root, source):
    result = subprocess.run(['git', 'log', '-1', '--format=%cI', '--', source.relative_to(root).as_posix()],
                            cwd=root, text=True, capture_output=True)
    value = result.stdout.strip()
    return value or datetime.fromtimestamp(source.stat().st_mtime, timezone.utc).isoformat(timespec='seconds')


def render_document(title, body):
    return ('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(title)}</title><style>body{{font-family:"Malgun Gothic",sans-serif;line-height:1.8;max-width:900px;margin:32px auto;padding:0 20px;color:#18202e}}'
            'img{max-width:100%;height:auto}table{border-collapse:collapse}td,th{border:1px solid #dadde5;padding:8px}pre{overflow:auto;background:#f2f3f6;padding:16px}a{color:#2648d8}'
            '@media(prefers-color-scheme:dark){body{background:#0f131b;color:#e6e9f0}pre{background:#171c27}a{color:#7c98ff}}</style>'
            f'<nav><a href="{HOME}">← 공략집 모음</a> · <a href="{HUB}">한글패치 모음</a></nav><main>{body}</main></html>')


def build(root, patch_games=None):
    root = root.resolve()
    data = yaml.safe_load((root / 'guides.yml').read_text(encoding='utf-8-sig'))
    records = data.get('guides') if isinstance(data, dict) else None
    if not isinstance(records, list):
        raise ValueError('guides.yml에는 guides 목록이 필요합니다.')
    sources = [validate(root, item) for item in records]
    if len({item['id'] for item in records}) != len(records):
        raise ValueError('공략 id가 중복되었습니다.')
    games = patch_games if patch_games is not None else load_patch_games() if any(i.get('patch_repo') for i in records) else {}
    output, guides = {}, []
    for item, source in zip(records, sources):
        repo = item.get('patch_repo', '')
        if repo and repo not in games:
            raise ValueError(f'{repo}: 한글패치 허브에 등록된 저장소 이름을 확인하세요.')
        game = games.get(repo, {})
        relative = source.relative_to(root).as_posix()
        destination = Path('docs') / relative
        if source.suffix.lower() == '.md':
            destination = destination.with_suffix('.html')
            content = markdown.markdown(source.read_text(encoding='utf-8-sig'), extensions=['extra', 'toc', 'sane_lists'])
            output[destination] = render_document(item['title'], content).encode('utf-8')
        else:
            output[destination] = source.read_bytes()
        cover = game.get('cover', '')
        if cover:
            cover = HUB + cover + ('?v=' + game['cover_revision'] if game.get('cover_revision') else '')
        guides.append({'id': item['id'], 'patch_repo': repo, 'game': game.get('title') or item.get('game'),
            'platforms': game.get('platforms') or item.get('platforms'), 'title': item['title'],
            'category': item.get('category') or '전체 공략', 'format': source.suffix[1:].upper(),
            'url': HOME + quote(destination.relative_to('docs').as_posix()),
            'source_url': 'https://github.com/Dollars-Archive/Game-Walkthrough-Archive/blob/main/' + quote(relative),
            'cover': cover, 'cover_source': game.get('cover_source', ''), 'updated_at': updated(root, source)})
    # Copy assets beside registered Markdown so relative image links keep working.
    for source in (root / 'guides').rglob('*'):
        if source.is_file() and source.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'):
            resolved = source.resolve()
            if not resolved.is_relative_to((root / 'guides').resolve()):
                raise ValueError('공략 이미지 경로가 guides/ 밖을 가리킵니다.')
            output[Path('docs') / source.relative_to(root)] = source.read_bytes()
    guides.sort(key=lambda g: g['updated_at'], reverse=True)
    catalogue = {'guides': guides}
    output[Path('docs/data/guides.json')] = (json.dumps(catalogue, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    readme = (root / 'README.md').read_text(encoding='utf-8')
    listing = '\n'.join(f"- [{g['game']} — {g['title']}]({g['url']})" for g in guides) or '아직 등록된 공략이 없습니다.'
    output[Path('README.md')] = re.sub(r'(?<=<!-- WALKTHROUGHS:START -->).*?(?=<!-- WALKTHROUGHS:END -->)', '\n' + listing + '\n', readme, flags=re.S).encode('utf-8')
    for path, content in output.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_bytes() != content:
            target.write_bytes(content)
    # Delete only stale generated files inside this checkout's docs/guides.
    generated_root = (root / 'docs/guides').resolve()
    if generated_root.is_relative_to(root) and generated_root.exists():
        for path in generated_root.rglob('*'):
            if path.is_file() and path.relative_to(root) not in output:
                path.unlink()
    return catalogue


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    print(json.dumps({'registered': len(build(parser.parse_args().root)['guides'])}, ensure_ascii=False))
