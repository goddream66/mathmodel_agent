from pathlib import Path
import json
Path('summary.json').write_text(json.dumps({'ok': True}), encoding='utf-8')
print('done')