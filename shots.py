from playwright.sync_api import sync_playwright
B="http://localhost:9393"
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":1440,"height":1000})
    for name,url,full in [("home","/",False),("search",'/?q=coffee&max_price=40&in_stock=1',True),("agents","/agents",True)]:
        pg.goto(B+url,wait_until="networkidle"); pg.wait_for_timeout(2500)
        pg.screenshot(path=f"shots/{name}.png",full_page=full)
    b.close()
