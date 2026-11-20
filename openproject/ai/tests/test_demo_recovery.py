import io
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from cryptography.exceptions import InvalidTag
from automation.demo_recovery import encrypt, decrypt, sha, validate_archive, package_tree
from automation.decrypt_demo_recovery import unpack
from automation import demo_recovery


class DemoRecoveryTests(unittest.TestCase):
    def test_ollama_backup_requires_real_manifest_and_content_addressed_blobs(self):
        import json,hashlib
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);blob=b'restored-model';blob_digest=hashlib.sha256(blob).hexdigest()
            manifest=json.dumps({'config':{'digest':'sha256:'+blob_digest},'layers':[]}).encode()
            runtime={'version':{'version':'fixture'},'tags':{'models':[{'name':'bge-m3:latest','digest':'runtime-resolved-identity'}]},'model_sources':[{'model':'bge-m3:latest','blob':'sha256-'+blob_digest}]}
            (folder/'ollama-runtime.json').write_text(json.dumps(runtime))
            def write(data):
                with tarfile.open(folder/'ollama-models.tar','w') as archive:
                    for name,content in [('ollama-models/manifests/registry/library/bge-m3/latest',manifest),('ollama-models/blobs/sha256-'+blob_digest,data)]:
                        member=tarfile.TarInfo(name);member.size=len(content);archive.addfile(member,io.BytesIO(content))
            write(blob)
            self.assertEqual(demo_recovery.verify_ollama_files(folder)['content_addressed_blobs_verified'],1)
            write(b'corrupt')
            with self.assertRaisesRegex(ValueError,'BLOB_CORRUPT'):demo_recovery.verify_ollama_files(folder)
    def test_failed_qdrant_start_cleans_only_the_owned_private_network(self):
        calls=[];label=None
        def run(args,**kwargs):
            nonlocal label
            calls.append(args)
            if args[:3]==['docker','network','create']:
                label=args[-2].split('=',1)[1];return b'created'
            if args[:2]==['docker','run']:raise RuntimeError('INJECTED_START_FAILURE')
            if args[:3]==['docker','network','inspect']:
                import json
                return json.dumps([{'Labels':{'org.qldapm.demo-dr':label}}]).encode()
            return b''
        with patch.object(demo_recovery,'run',side_effect=run):
            with self.assertRaisesRegex(RuntimeError,'INJECTED_START_FAILURE'):
                demo_recovery.verify_qdrant(Path('fixture'),'fixture-image','fixture-runner')
        self.assertEqual(sum(args[:3]==['docker','network','rm'] for args in calls),1)
        self.assertFalse(any(args[:2]==['docker','rm'] for args in calls))
    def test_stream_roundtrip_tamper_and_wrong_key_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);source=folder/'data';source.write_bytes(os.urandom(2_100_000))
            key=os.urandom(32);encrypted=folder/'encrypted';encrypt(source,encrypted,key)
            result=folder/'restored';decrypt(encrypted,result,key);self.assertEqual(sha(source),sha(result))
            bad=bytearray(encrypted.read_bytes());bad[-30]^=1;corrupt=folder/'corrupt';corrupt.write_bytes(bad)
            for path,secret in [(corrupt,key),(encrypted,os.urandom(32))]:
                output=folder/'untrusted'
                with self.assertRaises(InvalidTag):decrypt(path,output,secret)
                self.assertFalse(output.exists())

    def test_archive_rejects_traversal_links_and_duplicate_names(self):
        with tempfile.TemporaryDirectory() as folder:
            for index,names in enumerate([['manifest.json','../evil'],['manifest.json','C:/evil'],['manifest.json','..\\evil'],['manifest.json','manifest.json']]):
                path=Path(folder)/str(index)
                with tarfile.open(path,'w') as archive:
                    for name in names:
                        info=tarfile.TarInfo(name);info.size=2;archive.addfile(info,io.BytesIO(b'{}'))
                with self.assertRaises(ValueError):validate_archive(path)
            path=Path(folder)/'link'
            with tarfile.open(path,'w') as archive:
                info=tarfile.TarInfo('manifest.json');info.type=tarfile.SYMTYPE;info.linkname='../other';archive.addfile(info)
            with self.assertRaises(ValueError):validate_archive(path)

    def test_source_archive_keeps_history_and_source_skips_rebuildable_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);source=folder/'source';source.mkdir();(source/'.git').mkdir();(source/'.git/HEAD').write_text('ref: refs/heads/demo')
            (source/'app.py').write_text('hello');(source/'.venv').mkdir();(source/'.venv/cache').write_text('skip')
            target=folder/'source.tar'
            with tarfile.open(target,'w') as archive:package_tree(archive,source,'src')
            with tarfile.open(target) as archive:self.assertEqual(set(archive.getnames()),{'src/.git/HEAD','src/app.py'})

    def test_portable_bootstrap_restores_bytes_without_workspace_dependencies(self):
        import json,hashlib
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);archive=folder/'payload.tar';data=b'fixture';key=os.urandom(32)
            manifest={'label':'unit','created_utc':'fixture','files':{'data.bin':{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}}}
            with tarfile.open(archive,'w') as output:
                for name,content in [('manifest.json',json.dumps(manifest).encode()),('data.bin',data)]:
                    member=tarfile.TarInfo(name);member.size=len(content);output.addfile(member,io.BytesIO(content))
            (folder/'key').write_bytes(key);encrypt(archive,folder/'encrypted',key)
            result=unpack(folder/'encrypted',folder/'key',folder/'restored')
            self.assertEqual(result['files'],1);self.assertEqual((folder/'restored/data.bin').read_bytes(),data)
            self.assertFalse((folder/'restored/authenticated-payload.tar').exists())
            with self.assertRaises(ValueError):unpack(folder/'encrypted',folder/'key',folder/'restored')


if __name__=='__main__':unittest.main()
