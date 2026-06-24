# 부울경 카토 래스터 타일 렌더 -> mbtiles
# 사용: python3 render_carto.py <mapnik.xml> <out.mbtiles> minlon minlat maxlon maxlat minz maxz
import sys, os, math, sqlite3
import mapnik

xml, out = sys.argv[1], sys.argv[2]
minlon, minlat, maxlon, maxlat = map(float, sys.argv[3:7])
minz, maxz = int(sys.argv[7]), int(sys.argv[8])
TILE = 256

merc = mapnik.Projection('epsg:3857')
wgs  = mapnik.Projection('epsg:4326')
tr = mapnik.ProjTransform(wgs, merc)

def lonlat_to_tile(lon, lat, z):
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    lat_r = math.radians(lat)
    y = int((1.0 - math.asinh(math.tan(lat_r)) / math.pi) / 2.0 * n)
    return max(0, min(n-1, x)), max(0, min(n-1, y))

def tile_bounds_merc(x, y, z):
    # 웹메르카토르 타일 경계
    n = 2 ** z
    R = 20037508.342789244
    minx = x / n * 2*R - R
    maxx = (x+1) / n * 2*R - R
    maxy = R - y / n * 2*R
    miny = R - (y+1) / n * 2*R
    return mapnik.Box2d(minx, miny, maxx, maxy)

m = mapnik.Map(TILE, TILE)
mapnik.load_map(m, xml)
m.srs = merc.params()

con = sqlite3.connect(out)
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS metadata (name text, value text)")
cur.execute("CREATE TABLE IF NOT EXISTS tiles (zoom_level int, tile_column int, tile_row int, tile_data blob)")
cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS tile_idx ON tiles(zoom_level, tile_column, tile_row)")
for k, v in [("name","부울경 OSM Carto"),("format","png"),("type","baselayer"),
             ("minzoom",str(minz)),("maxzoom",str(maxz)),
             ("bounds",f"{minlon},{minlat},{maxlon},{maxlat}")]:
    cur.execute("INSERT INTO metadata VALUES (?,?)", (k, v))

total = 0
for z in range(minz, maxz+1):
    x0, y0 = lonlat_to_tile(minlon, maxlat, z)   # 좌상단
    x1, y1 = lonlat_to_tile(maxlon, minlat, z)   # 우하단
    cnt = 0
    for x in range(x0, x1+1):
        for y in range(y0, y1+1):
            m.zoom_to_box(tile_bounds_merc(x, y, z))
            im = mapnik.Image(TILE, TILE)
            mapnik.render(m, im)
            data = im.tostring('png256')
            tms_y = (2**z - 1) - y          # mbtiles 는 TMS(y 뒤집힘)
            cur.execute("INSERT OR REPLACE INTO tiles VALUES (?,?,?,?)",
                        (z, x, tms_y, sqlite3.Binary(data)))
            cnt += 1; total += 1
    con.commit()
    print(f"z{z}: {cnt} tiles (누적 {total})", flush=True)
con.commit(); con.close()
print("완료:", total, "tiles ->", out)
