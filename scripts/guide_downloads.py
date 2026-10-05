"""Versioned walkthrough ZIPs and cumulative GitHub release-asset downloads."""
import argparse
import hashlib
import io
import json
import os
import re
import zipfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

REPOSITORY = 'Dollars-Archive/Game-Walkthrough-Archive'


def release_tag(guide_id):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', guide_id):
        raise ValueError('Invalid guide id')
    return 'guide-' + guide_id


def package(guide_id, entries):
    release_tag(guide_id)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content, compresslevel=9)
    payload = buffer.getvalue()
    return f'{guide_id}-{hashlib.sha256(payload).hexdigest()[:16]}.zip', payload


def download_stats(guide, assets):
    pattern = re.compile(re.escape(guide['id']) + r'-[0-9a-f]{16}\.zip')
    count, current_url = 0, ''
    for asset in assets:
        if asset.get('state') != 'uploaded' or not pattern.fullmatch(asset.get('name', '')):
            continue
        value = asset.get('download_count')
        if type(value) is not int or value < 0:
            raise ValueError('Invalid asset download count')
        count += value
        if asset['name'] == guide['download_asset_name']:
            expected = (f'https://github.com/{REPOSITORY}/releases/download/'
                        f'{release_tag(guide["id"])}/{asset["name"]}')
            if asset.get('browser_download_url') != expected:
                raise ValueError('Unexpected release download URL')
            current_url = expected
    if not current_url:
        raise ValueError('Current walkthrough download is not available')
    return {'download_count': count, 'download_url': current_url}


class GitHub:
    def __init__(self, token):
        if not token:
            raise ValueError('GH_TOKEN is required to publish walkthrough downloads')
        self.token = token

    def request(self, path, method='GET', data=None, upload=False):
        host = 'uploads.github.com' if upload else 'api.github.com'
        headers = {'Authorization': f'Bearer {self.token}', 'Accept': 'application/vnd.github+json',
                   'X-GitHub-Api-Version': '2026-03-10', 'User-Agent': 'Dollars-Archive-walkthroughs'}
        if data is not None:
            headers['Content-Type'] = 'application/zip' if upload else 'application/json'
            if not upload:
                data = json.dumps(data).encode('utf-8')
        request = Request(f'https://{host}/repos/{REPOSITORY}/{path}', headers=headers,
                          method=method, data=data)
        with urlopen(request, timeout=90) as response:
            return json.load(response)

    def get_release(self, tag):
        try:
            return self.request('releases/tags/' + quote(tag, safe=''))
        except HTTPError as error:
            if error.code == 404:
                return None
            raise

    def create_release(self, guide):
        return self.request('releases', 'POST', {
            'tag_name': release_tag(guide['id']), 'target_commitish': 'main',
            'name': guide['title'], 'draft': False, 'prerelease': False, 'make_latest': 'false',
            'body': f"[공략 읽기]({guide['url']})\n\n공략집 다운로드용 ZIP입니다. "
                    '대문에는 최신 파일을 연결하고 이전 파일은 누적 다운로드 집계를 위해 보존합니다.'})

    def assets(self, release_id):
        assets, page = [], 1
        while True:
            batch = self.request(f'releases/{release_id}/assets?per_page=100&page={page}')
            if not isinstance(batch, list):
                raise ValueError('Invalid release assets response')
            assets.extend(batch)
            if len(batch) < 100:
                return assets
            page += 1

    def upload(self, release_id, name, payload):
        return self.request(f'releases/{release_id}/assets?name={quote(name, safe="")}',
                            'POST', payload, upload=True)


def publish(root, client):
    root = root.resolve()
    catalogue_path = root / 'docs/data/guides.json'
    catalogue = json.loads(catalogue_path.read_text(encoding='utf-8'))
    for guide in catalogue['guides']:
        tag = release_tag(guide['id'])
        if guide.get('download_release_tag') != tag:
            raise ValueError('Build the catalogue before publishing downloads')
        name = guide['download_asset_name']
        if not re.fullmatch(re.escape(guide['id']) + r'-[0-9a-f]{16}\.zip', name):
            raise ValueError('Invalid package name')
        payload = (root / '.local/downloads' / name).read_bytes()
        if name != f'{guide["id"]}-{hashlib.sha256(payload).hexdigest()[:16]}.zip':
            raise ValueError('Download package content does not match its name')
        release = client.get_release(tag) or client.create_release(guide)
        if release.get('draft') or release.get('prerelease') or release.get('tag_name') != tag:
            raise ValueError('Expected a published walkthrough release')
        assets = client.assets(release['id'])
        existing = next((asset for asset in assets if asset.get('name') == name), None)
        if existing:
            if existing.get('state') != 'uploaded' or existing.get('size') != len(payload):
                raise ValueError('Existing walkthrough asset is incomplete or conflicts with this package')
        else:
            client.upload(release['id'], name, payload)
            assets = client.assets(release['id'])
        guide.update(download_stats(guide, assets))
    catalogue_path.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return catalogue


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    result = publish(parser.parse_args().root, GitHub(os.environ.get('GH_TOKEN')))
    print(json.dumps({'downloads_published': len(result['guides'])}))
