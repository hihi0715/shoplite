@echo off
cd /d "%~dp0"
echo ShopLite 本地啟動中...
echo.
echo 地端入口: http://localhost:8000
echo 請用瀏覽器開啟上方網址，不要直接開啟 public\index.html
echo.
python -m pip install -r requirements.txt -q
if not exist "data\sample_orders.json" (
  echo 正在產生模擬訂單資料...
  python scripts\generate_sample_data.py
)
python -m uvicorn app.main:app --reload --port 8000
