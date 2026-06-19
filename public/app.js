const API_BASE = `${window.location.origin}/api/v1`;
const LOCAL_ENTRY = "http://localhost:8000";

const FALLBACK_BRANDS = [
  { id: "aura_beauty", name: "Aura Beauty" },
  { id: "loom_fashion", name: "Loom Fashion" },
  { id: "nest_home", name: "Nest Home" },
];

let categoryChart;
let timeChart;
let segmentChart;
let toastTimer;

function getTenantId() {
  return document.getElementById("tenantId").value.trim() || FALLBACK_BRANDS[0].id;
}

function showApiBanner(message) {
  const banner = document.getElementById("apiBanner");
  banner.innerHTML = message;
  banner.hidden = false;
}

function hideApiBanner() {
  document.getElementById("apiBanner").hidden = true;
}

async function parseJsonResponse(res, actionLabel) {
  const contentType = res.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    const isFileProtocol = window.location.protocol === "file:";
    if (isFileProtocol) {
      throw new Error(`請不要直接開啟 HTML 檔案。請執行 start.bat，再用瀏覽器開啟 ${LOCAL_ENTRY}`);
    }
    throw new Error(
      `後端 API 未連線（${actionLabel}）。請在 shoplite 資料夾執行 start.bat，並開啟 ${LOCAL_ENTRY}`
    );
  }
  const data = await res.json();
  if (!res.ok) {
    const detail = data.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg || item).join(", ")
      : detail || `${actionLabel}失敗`;
    throw new Error(message);
  }
  return data;
}

async function checkApiHealth() {
  try {
    const res = await fetch(`${window.location.origin}/api/health`);
    if (!res.ok) return false;
    const data = await parseJsonResponse(res, "健康檢查");
    return data.status === "ok";
  } catch {
    return false;
  }
}

function getHeaders() {
  const headers = {};
  const apiKey = localStorage.getItem("shoplite_api_key");
  if (apiKey) headers["X-API-Key"] = apiKey;
  return headers;
}

function showToast(message, isError = false) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.classList.toggle("error", isError);
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    el.hidden = true;
  }, 2800);
}

function setLastUpdated() {
  const now = new Date();
  document.getElementById("lastUpdated").textContent =
    `更新於 ${now.toLocaleString("zh-TW", { hour12: false })}`;
}

async function loadBrandOptions() {
  const select = document.getElementById("tenantId");
  try {
    const res = await fetch(`${API_BASE}/orders/brands`, { headers: getHeaders() });
    if (!res.ok) throw new Error("brands unavailable");
    const data = await res.json();
    renderBrandOptions(data.brands);
  } catch {
    renderBrandOptions(FALLBACK_BRANDS);
  }
}

function renderBrandOptions(brands) {
  const select = document.getElementById("tenantId");
  select.innerHTML = brands
    .map((brand) => `<option value="${brand.id}">${brand.name}</option>`)
    .join("");
}

async function apiGet(path) {
  const tenant = getTenantId();
  const url = `${API_BASE}${path}${path.includes("?") ? "&" : "?"}tenant_id=${encodeURIComponent(tenant)}`;
  const res = await fetch(url, { headers: getHeaders() });
  return parseJsonResponse(res, "讀取資料");
}

async function loadSampleData(allBrands = true) {
  const url = allBrands
    ? `${API_BASE}/orders/load-sample`
    : `${API_BASE}/orders/load-sample?tenant_id=${encodeURIComponent(getTenantId())}`;
  const res = await fetch(url, {
    method: "POST",
    headers: getHeaders(),
  });
  return parseJsonResponse(res, "匯入模擬訂單");
}

async function fetchImportStatus() {
  const res = await fetch(`${API_BASE}/orders/import-status`, { headers: getHeaders() });
  return parseJsonResponse(res, "讀取匯入狀態");
}

async function uploadCsv(file) {
  const tenant = getTenantId();
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/orders/upload?tenant_id=${encodeURIComponent(tenant)}`, {
    method: "POST",
    headers: getHeaders(),
    body: form,
  });
  return parseJsonResponse(res, "匯入訂單");
}

function formatMoney(value) {
  return `NT$ ${Number(value).toLocaleString("zh-TW", { maximumFractionDigits: 0 })}`;
}

function formatCategoryLabel(category) {
  const labels = {
    skincare: "保養",
    fashion: "服飾",
    home: "居家",
    beauty: "美妝",
  };
  return labels[category] || category;
}

function renderSummary(data) {
  document.getElementById("totalOrders").textContent = data.total_orders.toLocaleString("zh-TW");
  document.getElementById("totalRevenue").textContent = formatMoney(data.total_revenue);
  document.getElementById("uniqueCustomers").textContent = data.unique_customers.toLocaleString("zh-TW");
  document.getElementById("avgOrderValue").textContent = formatMoney(data.avg_order_value);
}

function renderCategoryChart(items) {
  const ctx = document.getElementById("categoryChart");
  if (categoryChart) categoryChart.destroy();
  categoryChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: items.map((i) => formatCategoryLabel(i.category)),
      datasets: [{
        data: items.map((i) => i.revenue),
        backgroundColor: ["#2563eb", "#7c3aed", "#059669", "#d97706", "#e11d48"],
        borderWidth: 0,
      }],
    },
    options: {
      plugins: { legend: { position: "bottom" } },
    },
  });
}

function renderTimeChart(items) {
  const ctx = document.getElementById("timeChart");
  if (timeChart) timeChart.destroy();
  timeChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: items.map((i) => i.date),
      datasets: [{
        label: "營收",
        data: items.map((i) => i.revenue),
        borderColor: "#2563eb",
        backgroundColor: "rgba(37, 99, 235, 0.08)",
        fill: true,
        tension: 0.3,
        pointRadius: 0,
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { maxTicksLimit: 8, color: "#64748b" }, grid: { display: false } },
        y: { ticks: { color: "#64748b" }, grid: { color: "#e2e8f0" } },
      },
    },
  });
}

function renderTopProducts(items) {
  const body = document.getElementById("topProductsBody");
  if (!items.length) {
    body.innerHTML = `<tr><td colspan="4">尚無資料</td></tr>`;
    return;
  }
  body.innerHTML = items.map((item) => `
    <tr>
      <td>${item.product_id}</td>
      <td>${formatCategoryLabel(item.category)}</td>
      <td>${formatMoney(item.revenue)}</td>
      <td>${item.quantity.toLocaleString("zh-TW")}</td>
    </tr>
  `).join("");
}

function renderSegments(items) {
  const body = document.getElementById("segmentsBody");
  if (!items.length) {
    body.innerHTML = `<tr><td colspan="5">尚無資料</td></tr>`;
    return;
  }

  body.innerHTML = items.map((item) => `
    <tr>
      <td>${item.label}</td>
      <td>${item.count.toLocaleString("zh-TW")}</td>
      <td>${item.avg_recency_days} 天</td>
      <td>${item.avg_frequency}</td>
      <td>${formatMoney(item.avg_monetary)}</td>
    </tr>
  `).join("");

  const ctx = document.getElementById("segmentChart");
  if (segmentChart) segmentChart.destroy();
  segmentChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: items.map((i) => i.label),
      datasets: [{
        label: "人數",
        data: items.map((i) => i.count),
        backgroundColor: "#059669",
        borderRadius: 8,
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false } },
        y: { grid: { color: "#e2e8f0" } },
      },
    },
  });
}

async function refreshDashboard() {
  const [summary, categories, timeline, products, segments] = await Promise.all([
    apiGet("/analytics/dashboard"),
    apiGet("/analytics/sales-by-category"),
    apiGet("/analytics/sales-over-time"),
    apiGet("/analytics/top-products?limit=10"),
    apiGet("/analytics/customer-segments"),
  ]);

  renderSummary(summary);
  renderCategoryChart(categories.items);
  renderTimeChart(timeline.items);
  renderTopProducts(products.items);
  renderSegments(segments.items);
  setLastUpdated();
}

async function handleLoadSample() {
  const button = document.getElementById("loadSampleBtn");
  button.disabled = true;
  button.textContent = "匯入中...";
  try {
    const healthy = await checkApiHealth();
    if (!healthy) {
      throw new Error(`後端未啟動。請執行 start.bat，並開啟 ${LOCAL_ENTRY}`);
    }

    const result = await loadSampleData(true);
    const totalRows = Number(result.rows_added || 0);
    if (!totalRows) {
      throw new Error("模擬訂單匯入失敗，後端未寫入任何資料");
    }

    const status = await fetchImportStatus();
    const storeTotal = Number(status.store?.total_rows || 0);
    const sampleTotal = Number(status.sample_file?.total_rows || 0);
    if (storeTotal === 0) {
      throw new Error(
        `模擬檔案有 ${sampleTotal} 筆，但寫入失敗。請確認你是從 ${LOCAL_ENTRY} 開啟，不是直接開 HTML。`
      );
    }

    await refreshDashboard();
    const tenant = getTenantId();
    const tenantRows = Number(status.store?.by_brand?.[tenant] || result.rows_in_store?.[tenant] || 0);
    showToast(`已匯入 ${totalRows.toLocaleString("zh-TW")} 筆；目前品牌 ${tenantRows.toLocaleString("zh-TW")} 筆`);
    hideApiBanner();
  } catch (error) {
    const message = typeof error.message === "string"
      ? error.message
      : "模擬訂單匯入失敗";
    showToast(message, true);
    showApiBanner(message);
  } finally {
    button.disabled = false;
    button.textContent = "匯入模擬訂單";
  }
}

async function handleRefresh() {
  try {
    await refreshDashboard();
    showToast("資料已更新");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function handleUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    await uploadCsv(file);
    await refreshDashboard();
    showToast("訂單匯入完成");
  } catch (error) {
    showToast(error.message, true);
  } finally {
    event.target.value = "";
  }
}

async function handleBrandChange() {
  try {
    await refreshDashboard();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function initializeDashboard() {
  await loadBrandOptions();

  const healthy = await checkApiHealth();
  if (!healthy) {
    showApiBanner(
      `後端 API 未連線。請在 <code>shoplite</code> 資料夾雙擊 <code>start.bat</code>，再用瀏覽器開啟 <code>${LOCAL_ENTRY}</code>。不要直接開啟 HTML 檔案。`
    );
    return;
  }

  try {
    const status = await fetchImportStatus();
    if (status.store?.total_rows > 0) {
      await refreshDashboard();
      return;
    }
    showToast("請點擊「匯入模擬訂單」載入資料", true);
  } catch (error) {
    showApiBanner(error.message);
  }
}

document.getElementById("loadSampleBtn").addEventListener("click", handleLoadSample);
document.getElementById("refreshBtn").addEventListener("click", handleRefresh);
document.getElementById("csvFile").addEventListener("change", handleUpload);
document.getElementById("tenantId").addEventListener("change", handleBrandChange);

initializeDashboard();
