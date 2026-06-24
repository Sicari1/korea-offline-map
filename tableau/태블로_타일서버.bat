@echo off
chcp 949 >nul
cd /d "%~dp0"
echo ============================================
echo  [태블로용] 부울경 지도 타일 서버
echo  포트 8788 에서 타일을 제공합니다.
echo  이 창은 닫지 마세요 (닫으면 태블로 지도도 안 나옵니다).
echo ============================================
echo.
echo  서버 주소: http://localhost:8788/busangyeong/{z}/{x}/{y}.png
echo.
pmtiles.exe serve . --port 8788 --cors "*"
pause
