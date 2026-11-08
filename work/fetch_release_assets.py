"""Prepare the repaired artwork release used by all application builds."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_REPOSITORY = 'jingh12312-rgb/bailong-desktop-pet'
UPSTREAM_TAG = 'v0.5.1'
ASSET_REPOSITORY = 'Joseph-Blue/bailong-desktop-pet-optimization'
ASSET_TAG = 'v0.5.1-opt.assets.repaired.2'
ASSET_NAME = 'bailong-repaired-v0.5.1-assets.zip'
REPAIRED_IDS = ('idle', 'idle2', 'drag', 'landing')


def uses_repaired_animations(manifest):
    paths = {item['id']: item.get('playbackFile') for item in animation_items(manifest)}
    return all(paths.get(name) == f'修复WebM/{name}.webm' for name in REPAIRED_IDS)


def repaired_release_selected():
    return (asset_release_tag() == ASSET_TAG
            and (os.environ.get('ASSET_FILE_NAME') or ASSET_NAME) == ASSET_NAME)


def asset_release_tag():
    return os.environ.get('ASSET_RELEASE_TAG') or (
        UPSTREAM_TAG if os.environ.get('ASSET_REPOSITORY') == UPSTREAM_REPOSITORY else ASSET_TAG)


def animation_items(manifest):
    return ([manifest['idle']] + manifest.get('additionalIdleAnimations', [])
            + manifest['variants'] + [v for v in manifest.get('workAnimations', []) if v]
            + manifest.get('movementAnimations', [])
            + [manifest[k] for k in ('dragAnimation', 'landingAnimation', 'quotaAnimation') if manifest.get(k)])


def animation_paths(manifest):
    items = animation_items(manifest)
    paths = {v.get('playbackFile') or v['file'].replace('.webm', '.webp') for v in items}
    paths.update(v['returnTransition']['file'] for v in items if v.get('returnTransition'))
    return paths


def missing_assets():
    assets = ROOT / 'outputs/白龙桌宠素材'
    manifest_path = assets / '素材清单.json'
    if not manifest_path.is_file():
        return [manifest_path]
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if repaired_release_selected() and not uses_repaired_animations(manifest):
        return [manifest_path]
    return [assets / relative for relative in sorted(animation_paths(manifest))
            if not (assets / relative).is_file()]


class DownloadRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, *args, **kwargs):
        redirected = super().redirect_request(request, *args, **kwargs)
        if redirected is not None:
            redirected.remove_header('Authorization')
        return redirected


def copy_download(response, output, total):
    downloaded = last_bytes = 0
    last_time = time.monotonic()
    print(f'下载：0.0 / {total / 1_000_000:.1f} MB  0.0%  0.00 MB/s', end='\r', flush=True)
    while chunk := response.read(256 * 1024):
        output.write(chunk)
        downloaded += len(chunk)
        now = time.monotonic()
        if now - last_time >= 0.5 or downloaded == total:
            speed = (downloaded - last_bytes) / max(now - last_time, 0.001)
            print(f'下载：{downloaded / 1_000_000:.1f} / {total / 1_000_000:.1f} MB'
                  f'  {downloaded / total * 100:.1f}%  {speed / 1_000_000:.2f} MB/s    ',
                  end='\r', flush=True)
            last_time, last_bytes = now, downloaded
    print(flush=True)


def download_assets():
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    use_gh = bool(not token and shutil.which('gh') and subprocess.run(
        ['gh', 'auth', 'status', '--hostname', 'github.com'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0)
    if use_gh:
        # 仅在内存中使用现有 CLI 登录，让两种认证共用流式下载与进度显示。
        token = subprocess.check_output(['gh', 'auth', 'token', '--hostname', 'github.com'], text=True).strip()
    repository = os.environ.get('ASSET_REPOSITORY') or ASSET_REPOSITORY
    tag = asset_release_tag()
    print(f'准备动画素材，从 {repository} / {tag} 获取；原作者：{UPSTREAM_REPOSITORY}。', flush=True)
    headers = {'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = urllib.request.Request(f'https://api.github.com/repos/{repository}/releases/tags/{tag}', headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        release = json.load(response)
    asset_name = os.environ.get('ASSET_FILE_NAME') or ASSET_NAME
    asset = next((item for item in release['assets'] if item['name'] == asset_name), None)
    if asset is None and repository == UPSTREAM_REPOSITORY:
        asset = next((item for item in release['assets']
                      if item['name'].endswith(('-windows-x64-webm.zip', '-windows-x86_64.zip'))), None)
    if asset is None:
        raise RuntimeError(f'{repository} / {tag} 没有素材附件 {asset_name}。')
    work = ROOT / '.build/downloads'
    work.mkdir(parents=True, exist_ok=True)
    # 下载成功才留下缓存，避免下次构建使用中断的 ZIP。
    with tempfile.TemporaryDirectory(prefix='assets-', dir=work) as temporary:
        archive = Path(temporary) / Path(asset['name']).name
        headers['Accept'] = 'application/octet-stream'
        url = asset['url'] if token else asset['browser_download_url']
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.build_opener(DownloadRedirect()).open(request, timeout=120) as response, archive.open('wb') as out:
            copy_download(response, out, asset['size'])
        cached = work / archive.name
        archive.replace(cached)
    copied = 0
    with zipfile.ZipFile(cached) as bundle:
        for item in bundle.infolist():
            name = item.filename.removeprefix('BailongPet/')
            if item.is_dir() or not name.startswith('outputs/'):
                continue
            destination = (ROOT / name).resolve()
            if not destination.is_relative_to((ROOT / 'outputs').resolve()):
                raise ValueError(f'Invalid asset path: {item.filename}')
            # 原版迁移到修复版时必须一并更新清单；保留已有动画文件。
            if destination.exists() and name != 'outputs/白龙桌宠素材/素材清单.json':
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(item) as source, destination.open('wb') as out:
                shutil.copyfileobj(source, out)
            copied += 1
    print(f'素材已补齐 {copied} 个文件：{asset["name"]}', flush=True)


def ensure_assets():
    missing = missing_assets()
    if not missing:
        return
    download_assets()
    missing = missing_assets()
    if missing:
        raise RuntimeError('下载后仍缺少素材：' + '\n'.join(str(path) for path in missing))


if __name__ == '__main__':
    ensure_assets()
