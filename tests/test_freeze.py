import hashlib,json,subprocess
from pathlib import Path
import pytest
from karstfinder.freeze import verify_freeze


def test_freeze_audits_archived_code_local_metadata_and_immutable_data(tmp_path):
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=tmp_path,text=True,stderr=subprocess.DEVNULL).strip()
    git('init','-q')
    src=tmp_path/'src';src.mkdir();code=src/'example.py';code.write_text('original implementation\n')
    metadata=src/'example.egg-info';metadata.mkdir();pkg=metadata/'PKG-INFO';pkg.write_text('generated local metadata\n')
    (tmp_path/'.gitignore').write_text('*.egg-info/\n')
    git('add','.');git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','frozen implementation')
    commit=git('rev-parse','HEAD')
    data=tmp_path/'data';data.mkdir();output=data/'result.bin';output.write_bytes(b'independent prediction')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    m={'status':'frozen_before_validation','implementation_git_commit':commit,'sha256':{str(p.relative_to(tmp_path)):sha(p) for p in [code,pkg,output]}}
    path=tmp_path/'experiments/frozen';path.mkdir(parents=True);(path/'blind_v002.json').write_text(json.dumps(m))
    code.write_text('later implementation, distinct experiment\n')
    assert verify_freeze(tmp_path)['implementation_git_commit']==commit
    output.write_bytes(b'altered prediction')
    with pytest.raises(RuntimeError,match='Frozen artifact changed: data/result.bin'):verify_freeze(tmp_path)
