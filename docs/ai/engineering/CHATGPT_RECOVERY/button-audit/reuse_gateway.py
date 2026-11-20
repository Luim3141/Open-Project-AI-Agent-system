"""Core-only follow-up keeps the exact qualified, measured Gateway image."""
import json
import release_buttons as setup
release=setup.release
path=setup.BUNDLE/'manifest.json'
manifest=json.loads(path.read_text())
image=release.BASE_IMAGES['gateway']
assert release.runtime_hashes('gateway',image)=={k:v for k,v in manifest['source_hashes'].items() if release.SOURCES[k][0]=='gateway'}
manifest['images']['gateway']=image
manifest['gateway_reused_unchanged']=True
release.write_json(path,manifest)
print(json.dumps({'gateway':image,'source_parity':'PASS'}))
