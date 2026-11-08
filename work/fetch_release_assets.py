"""Prepare original animation assets from this repository's Windows release."""
import json
import os
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class DownloadRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, *args, **kwargs):
        redirected = super().redirect_request(request, *args, **kwargs)
        if redirected is not None:
            redirected.remove_header('Authorization')
        return redirected


def main():
    repository = os.environ.get('ASSET_REPOSITORY', 'jingh12312-rgb/bailong-desktop-pet')
    tag = os.environ.get('ASSET_RELEASE_TAG', 'v0.5.1')
    headers = {'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
               'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}
    request = urllib.request.Request(f'https://api.github.com/repos/{repository}/releases/tags/{tag}', headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        release = json.load(response)
    asset = next(item for item in release['assets']
                 if item['name'].endswith(('-windows-x64-webm.zip', '-windows-x86_64.zip')))
    headers['Accept'] = 'application/octet-stream'
    request = urllib.request.Request(asset['url'], headers=headers)
    work = ROOT / '.build/downloads'
    work.mkdir(parents=True, exist_ok=True)
    archive = work / asset['name']
    import shutil
    with urllib.request.build_opener(DownloadRedirect()).open(request, timeout=120) as response, archive.open('wb') as out:
        shutil.copyfileobj(response, out)
    with zipfile.ZipFile(archive) as bundle:
        for item in bundle.infolist():
            if item.is_dir() or not item.filename.startswith('BailongPet/outputs/'):
                continue
            destination = (ROOT / item.filename.removeprefix('BailongPet/')).resolve()
            if not destination.is_relative_to(ROOT / 'outputs'):
                raise ValueError(f'Invalid asset path: {item.filename}')
            destination.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(item) as source, destination.open('wb') as out:
                shutil.copyfileobj(source, out)
    print(f'素材已准备：{asset["name"]}')


if __name__ == '__main__':
    main()
