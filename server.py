"""BotShop server: python3 server.py [port]"""
import json,sys,os,urllib.parse
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
import core
W=os.path.join(os.path.dirname(os.path.abspath(__file__)),"web")
class H(BaseHTTPRequestHandler):
    def send(s,code,body,ct="application/json"):
        b=body if isinstance(body,bytes) else (json.dumps(body,indent=1) if ct=="application/json" else body).encode()
        s.send_response(code);s.send_header("Content-Type",ct+"; charset=utf-8");s.send_header("Access-Control-Allow-Origin","*");s.send_header("Content-Length",len(b));s.end_headers();s.wfile.write(b)
    def do_GET(s):
        u=urllib.parse.urlparse(s.path);q={k:v[0] for k,v in urllib.parse.parse_qs(u.query).items()};p=u.path
        try:
            if p=="/api/search": return s.send(200,core.search(q.get("q",""),q.get("max_price"),q.get("min_price"),q.get("in_stock"),q.get("store"),q.get("limit",24),q.get("offset",0)))
            if p.startswith("/api/product/"):
                r=core.product(urllib.parse.unquote(p[13:])); return s.send(200 if r else 404,r or {"error":"not found"})
            if p=="/api/stores": return s.send(200,core.stores())
            f={"/":"index.html","/agents":"agents.html","/llms.txt":"llms.txt","/openapi.json":"openapi.json","/.well-known/mcp.json":"mcp.json","/favicon.ico":"favicon.ico","/favicon-32.png":"favicon-32.png","/apple-touch-icon.png":"apple-touch-icon.png","/icon-512.png":"icon-512.png"}.get(p)
            if f:
                ct={"html":"text/html","txt":"text/plain","json":"application/json","ico":"image/x-icon","png":"image/png"}[f.rsplit(".",1)[1]]
                return s.send(200,open(os.path.join(W,f),"rb").read(),ct)
            s.send(404,{"error":"not found"})
        except Exception as e: s.send(400,{"error":str(e)})
    def do_POST(s):
        if s.path!="/mcp": return s.send(404,{"error":"not found"})
        msg=json.loads(s.rfile.read(int(s.headers.get("Content-Length",0))))
        r=[x for x in map(core.mcp,msg) if x] if isinstance(msg,list) else core.mcp(msg)
        if r is None: s.send_response(202);s.end_headers();return
        s.send(200,r)
ThreadingHTTPServer(("0.0.0.0",int(sys.argv[1]) if len(sys.argv)>1 else int(os.environ.get("PORT",9393))),H).serve_forever()
