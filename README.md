# ShopLite Analytics

B2B2C D2C 電商品牌數據分析平台（Python FastAPI + MapReduce + K-Means）。

## 線上體驗

- 儀表板：https://shoplite-henna.vercel.app/
- API 健康檢查：https://shoplite-henna.vercel.app/api/health

## 功能

- CSV 訂單匯入 / 範例資料載入
- MapReduce 風格聚合：品類營收、每日趨勢、熱銷商品
- K-Means 客群分群（RFM：Recency / Frequency / Monetary）
- 多頁面儀表板：總覽、商品、顧客、通路（Chart.js）
- 可部署至 Vercel

## 專案結構

```
shoplite/
├── api/index.py          # Vercel serverless 入口
├── app/
│   ├── main.py           # FastAPI app
│   ├── config.py         # .env 設定
│   ├── routers/          # API 路由
│   └── services/         # ingest / mapreduce / kmeans / analytics
├── public/               # 前端靜態頁
├── data/sample_orders.csv
├── scripts/generate_sample_data.py
├── start.bat             # Windows 一鍵本地啟動
├── requirements.txt
└── vercel.json
```

## 本地開發

**Windows（建議）**：雙擊 `start.bat`，瀏覽器開啟 http://localhost:8000

**手動啟動**：

```bash
cd shoplite
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env
python scripts/generate_sample_data.py
uvicorn app.main:app --reload --port 8000
```

開啟：
- 儀表板：http://localhost:8000
- API Docs：http://localhost:8000/docs

> 請透過上述網址存取，不要直接開啟 `public/index.html`，否則 API 無法連線。

## 環境變數（.env）

| 變數 | 說明 |
|------|------|
| `API_SECRET_KEY` | 選填；設定後上傳/寫入 API 需帶 `X-API-Key` |
| `USE_MULTIPROCESSING` | 本地可設 `true`；Vercel 請保持 `false` |
| `KMEANS_CLUSTERS` | 分群數（預設 3） |
| `MAPREDUCE_WORKERS` | 平行 worker 數 |

## API 端點

| Method | Path | 說明 |
|--------|------|------|
| GET | `/api/health` | 健康檢查 |
| POST | `/api/v1/orders/upload` | 上傳 CSV |
| POST | `/api/v1/orders/load-sample` | 載入範例資料 |
| GET | `/api/v1/orders/import-status` | 匯入狀態診斷 |
| POST | `/api/v1/events` | 寫入 C 端行為事件 |
| GET | `/api/v1/analytics/dashboard` | 儀表板摘要 |
| GET | `/api/v1/analytics/sales-by-category` | 品類營收 |
| GET | `/api/v1/analytics/sales-over-time` | 每日營收 |
| GET | `/api/v1/analytics/top-products` | 熱銷商品 |
| GET | `/api/v1/analytics/customer-segments` | K-Means 客群 |
| GET | `/api/v1/analytics/pages/products` | 商品分析頁 |
| GET | `/api/v1/analytics/pages/customers` | 顧客分析頁 |
| GET | `/api/v1/analytics/pages/channels` | 通路分析頁 |

### CSV 欄位

必填：`order_id`, `user_id`, `product_id`, `category`, `quantity`, `amount`, `order_time`

選填：`l2_tenant_id`, `channel`

## 部署到 Vercel

1. 將專案推送到 GitHub
2. 在 Vercel Import 專案（root 選 `shoplite`）
3. 於 Vercel Project Settings → Environment Variables 設定：
   - `API_SECRET_KEY`（建議正式環境一定要設）
   - `USE_MULTIPROCESSING=false`
4. Deploy

部署後：
- 前端：https://shoplite-henna.vercel.app/
- API：https://shoplite-henna.vercel.app/api/health

> 注意：Vercel serverless 使用記憶體儲存，實例重啟後資料會清空。展示時可每次按「匯入模擬訂單」重新載入資料。
