#!/bin/bash
# 부울경 주요 도시 z17-18 렌더 → city1718.mbtiles (3개 도시 순차)
set -e
cd ~/build_carto
PY=/usr/bin/python3.12
XML=openstreetmap-carto/mapnik.xml
OUT=city1718.mbtiles
NPROC=30

echo "===== z17-18 도시 렌더 시작 $(date '+%H:%M:%S') ====="

# 부산 도심 (서면·남포·동래·해운대·연산)
echo "--- [1/3] 부산 도심 ---"
$PY render_parallel.py $XML $OUT 128.95 35.07 129.20 35.27 17 18 $NPROC

# 울산 도심 (남구·중구)
echo "--- [2/3] 울산 도심 ---"
$PY render_parallel.py $XML $OUT 129.27 35.50 129.42 35.58 17 18 $NPROC

# 창원·마산·김해
echo "--- [3/3] 창원·마산·김해 ---"
$PY render_parallel.py $XML $OUT 128.55 35.17 128.92 35.32 17 18 $NPROC

echo "===== 렌더 전체 완료 $(date '+%H:%M:%S') ====="
ls -la $OUT
