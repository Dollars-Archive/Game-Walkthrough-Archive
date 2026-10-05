"""Register one owner-authored guide without hand-editing YAML; never push Git."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

import yaml

try:
    from .build_guides import load_patch_games, validate
except ImportError:
    from build_guides import load_patch_games, validate


def register(root, source, *, guide_id, title, original, patch_repo='', game='', platforms=None,
             category='전체 공략', patch_games=None):
    root, source = Path(root).resolve(), Path(source).resolve()
    if not original:
        raise ValueError('사용자가 직접 작성한 공략임을 확인한 뒤 --original을 지정합니다.')
    if not source.is_file() or source.suffix.lower() not in ('.md', '.pdf', '.html'):
        raise ValueError('등록할 실제 Markdown, PDF 또는 HTML 파일이 필요합니다.')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', guide_id) or not title.strip():
        raise ValueError('영문 소문자·숫자·하이픈 id와 공략 제목이 필요합니다.')
    if not isinstance(patch_repo, str) or (patch_repo and not re.fullmatch(r'[A-Za-z0-9_.-]+', patch_repo)):
        raise ValueError('patch_repo는 저장소 이름만 입력합니다.')
    if patch_repo:
        games = patch_games if patch_games is not None else load_patch_games()
        if patch_repo not in games:
            raise ValueError('한글패치 허브에 등록된 정확한 저장소 이름을 확인하세요.')
    elif not game.strip() or not platforms or any(not isinstance(p, str) or not p.strip() for p in platforms):
        raise ValueError('패치와 연결하지 않는 공략은 게임 이름과 기종이 필요합니다.')
    registry = root / 'guides.yml'
    data = yaml.safe_load(registry.read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict) or not isinstance(data.get('guides'), list):
        raise ValueError('기존 guides.yml 목록을 먼저 확인하세요.')
    records = data['guides']
    if any(not isinstance(r, dict) for r in records) or len({r.get('id') for r in records}) != len(records):
        raise ValueError('기존 등록 목록의 형식 또는 중복 id를 확인하세요.')
    existing = next((r for r in records if r.get('id') == guide_id), None)
    if existing and (existing.get('patch_repo', '') != patch_repo or (not patch_repo and existing.get('game') != game)):
        raise ValueError('같은 id를 다른 게임에 재사용할 수 없습니다.')
    if any(r.get('id') != guide_id and r.get('title') == title
           and r.get('patch_repo', '') == patch_repo and (patch_repo or r.get('game') == game) for r in records):
        raise ValueError('동일 게임·제목의 공략이 있습니다. 기존 id로 업데이트하세요.')
    relative = Path('guides') / (patch_repo or guide_id) / (guide_id + source.suffix.lower())
    destination = (root / relative).resolve()
    if not destination.is_relative_to((root / 'guides').resolve()):
        raise ValueError('등록 경로가 guides/ 밖입니다.')
    record = {**(existing or {}), 'id': guide_id, 'patch_repo': patch_repo, 'title': title,
              'category': category, 'file': relative.as_posix(), 'original': True}
    if not patch_repo:
        record.update(game=game, platforms=platforms)
    payload = source.read_bytes()
    backup = root / '.local/registration-backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup.mkdir(parents=True, exist_ok=False)
    (backup / 'guides-before.yml').write_bytes(registry.read_bytes())
    if destination.exists():
        (backup / ('guide-before' + destination.suffix)).write_bytes(destination.read_bytes())
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    validate(root, record)
    data['guides'] = [record if r.get('id') == guide_id else r for r in records] if existing else records + [record]
    registry.write_text('# 직접 작성한 공략 등록 목록 — scripts/register_guide.py로 등록·수정합니다.\n' +
                        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding='utf-8')
    return {'action': 'updated' if existing else 'registered', 'id': guide_id,
            'file': relative.as_posix(), 'backup': str(backup)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--id', required=True)
    parser.add_argument('--title', required=True)
    parser.add_argument('--patch-repo', default='')
    parser.add_argument('--game', default='')
    parser.add_argument('--platform', action='append', default=[])
    parser.add_argument('--category', default='전체 공략')
    parser.add_argument('--original', action='store_true')
    args = parser.parse_args()
    result = register(args.root, args.input, guide_id=args.id, title=args.title, original=args.original,
                      patch_repo=args.patch_repo, game=args.game, platforms=args.platform, category=args.category)
    print(json.dumps(result, ensure_ascii=False))
