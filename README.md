# ShopLite Analytics

B2B2C D2C 電商品牌數據分析平台（Python FastAPI + MapReduce + K-Means）。

## 功能

- CSV 訂單匯入 / 範例資料載入
- MapReduce 風格聚合：品類營收、每日趨勢、熱銷商品
- K-Means 客群分群（RFM：Recency / Frequency / Monetary）
- 簡易前端儀表板（Chart.js）
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
├── requirements.txt
└── vercel.json
```

## 本地開發

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
- API Docs: http://localhost:8000/docs
- 儀表板（本地需另開 static 或用 Vercel dev）

本地若要看完整前端 + API，建議：

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

並用 Vercel CLI：

```bash
npm i -g vercel
vercel dev
```

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
| POST | `/api/v1/events` | 寫入 C 端行為事件 |
| GET | `/api/v1/analytics/dashboard` | 儀表板摘要 |
| GET | `/api/v1/analytics/sales-by-category` | 品類營收 |
| GET | `/api/v1/analytics/sales-over-time` | 每日營收 |
| GET | `/api/v1/analytics/top-products` | 熱銷商品 |
| GET | `/api/v1/analytics/customer-segments` | K-Means 客群 |

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
- 前端：`https://your-app.vercel.app/`
- API：`https://your-app.vercel.app/api/health`

> 注意：Vercel serverless 使用記憶體儲存，實例重啟後資料會清空。期末展示可每次按「載入範例資料」。

## HW2 方法論延伸

- `app/services/mapreduce.py`：Map / Reduce 分片聚合
- `app/services/kmeans.py`：K-Means 分群（呼應 HW2 的 mapper/reducer 概念）
- Vercel 環境預設用 ThreadPoolExecutor；本地可開 multiprocessing
