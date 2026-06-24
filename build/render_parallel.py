# 부울경 카토 래스터 병렬 렌더 -> mbtiles
# 사용: python3.12 render_parallel.py <mapnik.xml> <out.mbtiles> minlon minlat maxlon maxlat minz maxz [nproc]
import sys, os, math, sqlite3, time
from multiprocessing import Pool
import mapnik

XML = sys.argv[1]
OUT = sys.argv[2]
MINLON, MINLAT, MAXLON, MAXLAT = map(float, sys.argv[3:7])
MINZ, MAXZ = int(sys.argv[7]), int(sys.argv[8])
NPROC = int(sys.argv[9]) if len(sys.argv) > 9 else max(1, os.cpu_count()-2)
TILE = 256
R = 20037508.342789244

def lonlat_to_tile(lon, lat, z):
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)
    return max(0, min(n-1, x)), max(0, min(n-1, y))

def tile_bounds_merc(x, y, z):
    n = 2 ** z
    return mapnik.Box2d(x/n*2*R - R, R - (y+1)/n*2*R, (x+1)/n*2*R - R, R - y/n*2*R)

_map = None
def _init():
    global _map
    _map = mapnik.Map(TILE, TILE)
    mapnik.load_map(_map, XML)
    _map.srs = mapnik.Projection('epsg:3857').params()

def _render(t):
    z, x, y = t
    _map.zoom_to_box(tile_bounds_merc(x, y, z))
    im = mapnik.Image(TILE, TILE)
    mapnik.render(_map, im)
    return (z, x, (2**z - 1) - y, im.tostring('png256'))

def build_list():
    tiles = []
    for z in range(MINZ, MAXZ+1):
        x0, y0 = lonlat_to_tile(MINLON, MAXLAT, z)
        x1, y1 = lonlat_to_tile(MAXLON, MINLAT, z)
        for x in range(x0, x1+1):
            for y in range(y0, y1+1):
                tiles.append((z, x, y))
    return tiles

if __name__ == "__main__":
    tiles = build_list()
    print(f"총 타일 {len(tiles)}개, 워커 {NPROC}개, z{MINZ}-{MAXZ}", flush=True)
    con = sqlite3.connect(OUT)
    cur = con.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("CREATE TABLE IF NOT EXISTS metadata (name text, value text)")
    cur.execute("CREATE TABLE IF NOT EXISTS tiles (zoom_level int, tile_column int, tile_row int, tile_data blob)")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS tile_idx ON tiles(zoom_level, tile_column, tile_row)")
    for k, v in [("name","부울경 OSM Carto"),("format","png"),("type","baselayer"),
                 ("minzoom",str(MINZ)),("maxzoom",str(MAXZ)),
                 ("bounds",f"{MINLON},{MINLAT},{MAXLON},{MAXLAT}")]:
        cur.execute("INSERT INTO metadata VALUES (?,?)", (k, v))
    con.commit()
    t0 = time.time(); done = 0
    with Pool(NPROC, initializer=_init) as pool:
        for z, x, ty, data in pool.imap_unordered(_render, tiles, chunksize=32):
            cur.execute("INSERT OR REPLACE INTO tiles VALUES (?,?,?,?)", (z, x, ty, sqlite3.Binary(data)))
            done += 1
            if done % 2000 == 0:
                con.commit()
                el = time.time()-t0
                rate = done/el
                eta = (len(tiles)-done)/rate/60
                print(f"  {done}/{len(tiles)}  {rate:.0f} t/s  ETA {eta:.1f}분", flush=True)
    con.commit(); con.close()
    print(f"완료 {done} tiles, {time.time()-t0:.0f}s", flush=True)
