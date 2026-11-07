"""Check release contents and test the extracted source archive (no Bluebird writes)."""
import argparse
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import zipfile


def check(directory):
    wheels=list(directory.glob('*.whl'))
    sources=list(directory.glob('*.tar.gz'))
    if len(wheels)!=1 or len(sources)!=1:
        raise ValueError('Expected one wheel and one source archive in a clean output directory')
    assets=['native/ax.swift','web_assets/index.html','web_assets/app.js','web_assets/style.css']
    with zipfile.ZipFile(wheels[0]) as archive:
        for name in assets:
            if 'bluebird_cli/'+name not in archive.namelist():
                raise ValueError('Wheel missing '+name)
    with tempfile.TemporaryDirectory() as temporary:
        root=Path(temporary).resolve()
        with tarfile.open(sources[0]) as archive:
            members=archive.getmembers()
            for member in members:
                if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                    raise ValueError('Unsupported archive member')
                if not (root/member.name).resolve().is_relative_to(root):
                    raise ValueError('Archive path escapes extraction directory')
            archive.extractall(root)
        folders=list(root.iterdir())
        if len(folders)!=1 or not folders[0].is_dir():
            raise ValueError('Expected one source root')
        source=folders[0]
        required=['bluebird','LICENSE','README.md','README.zh-CN.md','SECURITY.md','CHANGELOG.md',
                  'CONTRIBUTING.md','skills/bluebird/SKILL.md','scripts/check_distribution.py',
                  'tests/test_web_cli.py']
        for language in ('en','zh-CN','ja'):
            required.extend('docs/'+language+'/'+page+'.md' for page in
                            ('README','setup','authorization','architecture','agent-workflow','verification','compatibility','release','security'))
        for name in required:
            if not (source/name).is_file():
                raise ValueError('Source archive missing '+name)
        subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-v'],cwd=source,check=True)
    print('Release contents and extracted-source tests passed.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    check(parser.parse_args().directory)
