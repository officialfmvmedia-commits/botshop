"""Refresh BotShop catalog: python3 ingest.py [max_pages_per_store]"""
import json,sqlite3,sys,time,urllib.request,re,html
MAXP=int(sys.argv[1]) if len(sys.argv)>1 else 4
db=sqlite3.connect("botshop.db")
db.executescript("""
CREATE TABLE IF NOT EXISTS stores(domain TEXT PRIMARY KEY,category TEXT,name TEXT,currency TEXT,product_count INT,status TEXT,last_crawl TEXT);
CREATE TABLE IF NOT EXISTS products(id TEXT PRIMARY KEY,store TEXT,shopify_id INT,title TEXT,vendor TEXT,type TEXT,tags TEXT,description TEXT,
 price REAL,currency TEXT,available INT,image TEXT,url TEXT,cart_url TEXT,variants TEXT,updated TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(id UNINDEXED,title,vendor,type,tags,description,store,tokenize='porter');
""")
def get(u):
    r=urllib.request.Request(u,headers={"User-Agent":"BotShopIndexer/0.1 (+https://botshop)","Accept":"application/json"})
    with urllib.request.urlopen(r,timeout=20) as f: return f.status,f.read(),f.geturl()
def cur(dom):
    try:
        _,b,_=get(f"https://{dom}/cart.js"); return json.loads(b).get("currency","USD")
    except Exception: return "USD"
for dom,cat in json.load(open("stores.json")):
    n=0;status="ok"
    try:
        c=cur(dom); base=dom
        db.execute("DELETE FROM products WHERE store=?",(dom,)); db.execute("DELETE FROM fts WHERE store=?",(dom,))
        for p in range(1,MAXP+1):
            _,b,final=get(f"https://{dom}/products.json?limit=250&page={p}")
            base=re.match(r"https://([^/]+)",final).group(1)
            ps=json.loads(b).get("products",[])
            if not ps: break
            for x in ps:
                vs=[{"id":v["id"],"title":v.get("title"),"price":float(v.get("price") or 0),"available":bool(v.get("available",True)),"sku":v.get("sku"),
                     "cart_url":f"https://{base}/cart/{v['id']}:1"} for v in x.get("variants",[])]
                if not vs: continue
                av=[v for v in vs if v["available"]]; pick=(av or vs)[0]
                img=(x.get("images") or [{}])[0].get("src") if x.get("images") else None
                desc=re.sub(r"\s+"," ",html.unescape(re.sub("<[^>]+>"," ",x.get("body_html") or ""))).strip()[:600]
                pid=f"{dom.split('.')[0]}-{x['id']}"
                tags=",".join(x["tags"]) if isinstance(x.get("tags"),list) else (x.get("tags") or "")
                row=(pid,dom,x["id"],x["title"],x.get("vendor"),x.get("product_type"),tags,desc,min(v["price"] for v in (av or vs)),c,int(bool(av)),img,
                     f"https://{base}/products/{x['handle']}",pick["cart_url"],json.dumps(vs),x.get("updated_at"))
                db.execute("INSERT OR REPLACE INTO products VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",row)
                db.execute("INSERT INTO fts VALUES(?,?,?,?,?,?,?)",(pid,x["title"],x.get("vendor"),x.get("product_type"),tags,desc,dom)); n+=1
            time.sleep(0.7)
    except Exception as e: status=f"error: {e}"[:200]
    db.execute("INSERT OR REPLACE INTO stores VALUES(?,?,?,?,?,?,datetime('now'))",(dom,cat,dom.split('.')[0],c if status=='ok' or n else None,n,status if not n or status=='ok' else 'partial: '+status))
    db.commit(); print(dom,n,status,flush=True)
