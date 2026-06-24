@echo off
chcp 949 >nul
cd /d "%~dp0"
echo ============================================
echo  한국 지도 서버 시작 중...
echo  이 창은 닫지 마세요 (지도 서버입니다).
echo  지도를 다 봤으면 그때 이 창을 닫으세요.
echo ============================================
echo.
echo  서버를 먼저 띄우고 잠시 후 브라우저가 열립니다.
start "korea-map 서버 (닫지마세요)" miniserve.exe --index index.html --port 8787 .
timeout /t 3 /nobreak >nul
start "" http://localhost:8787
echo.
echo  브라우저가 안 열리면 http://localhost:8787 로 접속하세요.
echo  연결 거부가 뜨면 2~3초 뒤 F5 로 새로고침 하세요.
pause
