import sys,json
from core import mcp
for line in sys.stdin:
    if not line.strip(): continue
    r=mcp(json.loads(line))
    if r: print(json.dumps(r),flush=True)
