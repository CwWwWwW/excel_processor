from transaction.commit import atomic_commit

def test_atomic_commit_rename_policy(tmp_path):
    c=tmp_path/'candidate.xlsx'; c.write_bytes(b'abc')
    target=tmp_path/'out.xlsx'; target.write_bytes(b'old')
    final=atomic_commit(c, target, overwrite_policy='rename')
    assert final.name == 'out_1.xlsx'
    assert final.read_bytes() == b'abc'
    assert target.read_bytes() == b'old'
