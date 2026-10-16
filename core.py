import sqlite3,json,re,os
DB=os.path.join(os.path.dirname(os.path.abspath(__file__)),"botshop.db")
def conn():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def fmt(r,full=False):
    d={k:r[k] for k in ("id","title","vendor","store","type","price","currency","image","url","cart_url")}
    d["in_stock"]=bool(r["available"]); d["checkout"]="merchant"
    if full:
        d["description"]=r["description"]; d["tags"]=r["tags"]; d["variants"]=json.loads(r["variants"]); d["updated"]=r["updated"]
    return d
def search(q="",max_price=None,min_price=None,in_stock=None,store=None,limit=24,offset=0):
    c=conn(); w=[];a=[]
    if q:
        toks=re.findall(r"\w+",q.lower())
        if toks:
            w.append("p.id IN (SELECT id FROM fts WHERE fts MATCH ?)"); a.append(" ".join(t+"*" for t in toks))
    if max_price not in (None,""): w.append("p.price<=?"); a.append(float(max_price))
    if min_price not in (None,""): w.append("p.price>=?"); a.append(float(min_price))
    if in_stock in (True,"1","true"): w.append("p.available=1")
    if store: w.append("p.store=?"); a.append(store)
    wh=("WHERE "+" AND ".join(w)) if w else ""
    order="ORDER BY (SELECT bm25(fts) FROM fts WHERE fts.id=p.id AND fts MATCH ?)" if q and toks else "ORDER BY p.available DESC, random()"
    total=c.execute(f"SELECT count(*) FROM products p {wh}",a).fetchone()[0]
    ob=a+([a[0]] if q and toks else [])
    rows=c.execute(f"SELECT * FROM products p {wh} {order} LIMIT ? OFFSET ?",ob+[min(int(limit),100),int(offset)]).fetchall()
    return {"query":q,"total":total,"results":[fmt(r) for r in rows]}
def product(pid):
    r=conn().execute("SELECT * FROM products WHERE id=?",(pid,)).fetchone()
    return fmt(r,True) if r else None
def stores():
    return [dict(r)|{"bot_checkout_ready":r["status"]=="ok"} for r in conn().execute("SELECT * FROM stores WHERE product_count>0 ORDER BY product_count DESC")]
TOOLS=[{"name":"search_products","description":"Search BotShop's index of products from merchants that allow bot checkout. Returns items with a direct cart_url on the merchant's store.",
 "inputSchema":{"type":"object","properties":{"q":{"type":"string"},"max_price":{"type":"number"},"min_price":{"type":"number"},"in_stock":{"type":"boolean"},"store":{"type":"string"},"limit":{"type":"integer","default":10}},"required":["q"]}},
 {"name":"get_product","description":"Get full details (variants, per-variant availability and cart links) for a BotShop product id.",
 "inputSchema":{"type":"object","properties":{"id":{"type":"string"}},"required":["id"]}}]
def mcp(msg):
    m=msg.get("method"); i=msg.get("id")
    if i is None: return None
    if m=="initialize": res={"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"botshop","version":"0.1.0"}}
    elif m=="tools/list": res={"tools":TOOLS}
    elif m=="tools/call":
        p=msg["params"];a=p.get("arguments",{})
        out=search(**{k:a[k] for k in ("q","max_price","min_price","in_stock","store","limit") if k in a}) if p["name"]=="search_products" else product(a.get("id"))
        res={"content":[{"type":"text","text":json.dumps(out)}]}
    elif m=="ping": res={}
    else: return {"jsonrpc":"2.0","id":i,"error":{"code":-32601,"message":"method not found"}}
    return {"jsonrpc":"2.0","id":i,"result":res}
