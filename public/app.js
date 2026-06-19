const API_BASE = `${window.location.origin}/api/v1`;
const LOCAL_ENTRY = "http://localhost:8000";

const FALLBACK_BRANDS = [
  { id: "aura_beauty", name: "Aura Beauty" },
  { id: "loom_fashion", name: "Loom Fashion" },
  { id: "nest_home", name: "Nest Home" },
];

const PAGE_TITLES = {
  overview: "營運總覽",
  products: "商品分析",
  customers: "顧客分析",
  channels: "通路分析",
};

const CHANNEL_COLORS = {
  website: "#2563eb",
  shopee: "#f97316",
  instagram: "#db2777",
};

let currentPage = "overview";
let toastTimer;

const charts = {
  category: null,
  time: null,
  segment: null,
  productCategory: null,
  productBar: null,
  customerSegment: null,
  channelPie: null,
  channelAov: null,
  channelTrend: null,
};

function getTenantId() {
  return document.getElementById("tenantId").value.trim() || FALLBACK_BRANDS[0].id;
}

function destroyChart(key) {
  if (charts[key]) {
    charts[key].destroy();
    charts[key] = null;
  }
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

function switchPage(page) {
  currentPage = page;
  document.getElementById("pageTitle").textContent = PAGE_TITLES[page] || "ShopLite";
  document.querySelectorAll(".page").forEach((section) => {
    section.classList.toggle("active", section.id === `page-${page}`);
  });
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.page === page);
  });
}

async function loadBrandOptions() {
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
  const res = await fetch(url, { method: "POST", headers: getHeaders() });
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

function formatChannelLabel(channel) {
  const labels = {
    website: "官網",
    shopee: "蝦皮",
    instagram: "Instagram",
  };
  return labels[channel] || channel;
}

function renderEmptyRow(bodyId, colspan, text = "尚無資料") {
  document.getElementById(bodyId).innerHTML =
    `<tr><td colspan="${colspan}">${text}</td></tr>`;
}

function renderSummary(data) {
  document.getElementById("totalOrders").textContent = data.total_orders.toLocaleString("zh-TW");
  document.getElementById("totalRevenue").textContent = formatMoney(data.total_revenue);
  document.getElementById("uniqueCustomers").textContent = data.unique_customers.toLocaleString("zh-TW");
  document.getElementById("avgOrderValue").textContent = formatMoney(data.avg_order_value);
}

function renderCategoryChart(items) {
  const ctx = document.getElementById("categoryChart");
  destroyChart("category");
  charts.category = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: items.map((i) => formatCategoryLabel(i.category)),
      datasets: [{
        data: items.map((i) => i.revenue),
        backgroundColor: ["#2563eb", "#7c3aed", "#059669", "#d97706", "#e11d48"],
        borderWidth: 0,
      }],
    },
    options: { plugins: { legend: { position: "bottom" } } },
  });
}

function aggregateRevenueByQuarter(items) {
  const quarters = new Map();
  for (const item of items) {
    const [year, month] = item.date.split("-").map(Number);
    const quarter = Math.ceil(month / 3);
    const key = `${year}-${quarter}`;
    const current = quarters.get(key) || { revenue: 0, orders: 0, year, quarter };
    current.revenue += item.revenue;
    current.orders += item.orders;
    quarters.set(key, current);
  }
  return Array.from(quarters.values())
    .sort((a, b) => (a.year - b.year) || (a.quarter - b.quarter))
    .map((entry) => ({
      label: `${entry.year}/${String((entry.quarter - 1) * 3 + 1).padStart(2, "0")}`,
      revenue: entry.revenue,
    }));
}

function smoothSeries(values, windowSize = 3) {
  if (!values.length) return [];
  return values.map((_, index) => {
    const start = Math.max(0, index - windowSize + 1);
    const slice = values.slice(start, index + 1);
    return Math.round(slice.reduce((sum, value) => sum + value, 0) / slice.length);
  });
}

function renderTimeChart(items) {
  const ctx = document.getElementById("timeChart");
  destroyChart("time");
  const quarterly = aggregateRevenueByQuarter(items);
  const labels = quarterly.map((item) => item.label);
  const revenues = quarterly.map((item) => item.revenue);
  charts.time = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "季度營收",
          data: revenues,
          borderColor: "#93c5fd",
          backgroundColor: "rgba(147, 197, 253, 0.18)",
          fill: true,
          tension: 0.15,
          pointRadius: 4,
          borderWidth: 2,
        },
        {
          label: "平滑趨勢",
          data: smoothSeries(revenues, 3),
          borderColor: "#1d4ed8",
          fill: false,
          tension: 0.42,
          pointRadius: 0,
          borderWidth: 3,
        },
      ],
    },
    options: {
      plugins: { legend: { position: "bottom" } },
      scales: {
        x: { title: { display: true, text: "月份（每 3 個月）" } },
        y: { ticks: { callback: (v) => `NT$ ${Number(v).toLocaleString("zh-TW")}` } },
      },
    },
  });
}

function renderTopProducts(items) {
  const body = document.getElementById("topProductsBody");
  if (!items.length) return renderEmptyRow("topProductsBody", 4);
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
    renderEmptyRow("segmentsBody", 5);
    destroyChart("segment");
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
  destroyChart("segment");
  charts.segment = new Chart(ctx, {
    type: "bar",
    data: {
      labels: items.map((i) => i.label),
      datasets: [{ label: "人數", data: items.map((i) => i.count), backgroundColor: "#059669", borderRadius: 8 }],
    },
    options: { plugins: { legend: { display: false } } },
  });
}

async function refreshOverviewPage() {
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
}

function renderProductsPage(data) {
  const s = data.summary;
  document.getElementById("productCount").textContent = s.product_count.toLocaleString("zh-TW");
  document.getElementById("categoryCount").textContent = s.category_count.toLocaleString("zh-TW");
  document.getElementById("topProductName").textContent = s.top_product || "—";
  document.getElementById("productRevenue").textContent = formatMoney(s.total_revenue);

  destroyChart("productCategory");
  charts.productCategory = new Chart(document.getElementById("productCategoryChart"), {
    type: "bar",
    data: {
      labels: data.categories.map((i) => formatCategoryLabel(i.category)),
      datasets: [{
        label: "營收",
        data: data.categories.map((i) => i.revenue),
        backgroundColor: "#2563eb",
        borderRadius: 8,
      }],
    },
    options: { plugins: { legend: { display: false } } },
  });

  const top5 = data.products.slice(0, 5);
  destroyChart("productBar");
  charts.productBar = new Chart(document.getElementById("productBarChart"), {
    type: "bar",
    data: {
      labels: top5.map((i) => i.product_name),
      datasets: [{
        label: "營收",
        data: top5.map((i) => i.revenue),
        backgroundColor: "#7c3aed",
        borderRadius: 8,
      }],
    },
    options: {
      indexAxis: "y",
      plugins: { legend: { display: false } },
    },
  });

  const body = document.getElementById("productTableBody");
  if (!data.products.length) return renderEmptyRow("productTableBody", 6);
  body.innerHTML = data.products.map((item) => `
    <tr>
      <td>${item.product_name}</td>
      <td>${item.product_id}</td>
      <td>${formatCategoryLabel(item.category)}</td>
      <td>${formatMoney(item.revenue)}</td>
      <td>${item.quantity.toLocaleString("zh-TW")}</td>
      <td>${formatMoney(item.avg_price)}</td>
    </tr>
  `).join("");
}

async function refreshProductsPage() {
  const data = await apiGet("/analytics/pages/products");
  renderProductsPage(data);
}

function renderCustomersPage(data) {
  const s = data.summary;
  document.getElementById("customerTotal").textContent = s.total_customers.toLocaleString("zh-TW");
  document.getElementById("customerRepeatRate").textContent = `${s.repeat_rate}%`;
  document.getElementById("customerAvgFreq").textContent = s.avg_frequency;
  document.getElementById("customerAvgMonetary").textContent = formatMoney(s.avg_monetary);

  const segBody = document.getElementById("customerSegmentBody");
  if (!data.segments.length) {
    renderEmptyRow("customerSegmentBody", 5);
    destroyChart("customerSegment");
  } else {
    segBody.innerHTML = data.segments.map((item) => `
      <tr>
        <td>${item.label}</td>
        <td>${item.count.toLocaleString("zh-TW")}</td>
        <td>${item.avg_recency_days} 天</td>
        <td>${item.avg_frequency}</td>
        <td>${formatMoney(item.avg_monetary)}</td>
      </tr>
    `).join("");
    destroyChart("customerSegment");
    charts.customerSegment = new Chart(document.getElementById("customerSegmentChart"), {
      type: "doughnut",
      data: {
        labels: data.segments.map((i) => i.label),
        datasets: [{
          data: data.segments.map((i) => i.count),
          backgroundColor: ["#059669", "#2563eb", "#f97316"],
          borderWidth: 0,
        }],
      },
      options: { plugins: { legend: { position: "bottom" } } },
    });
  }

  const body = document.getElementById("customerTableBody");
  if (!data.customers.length) return renderEmptyRow("customerTableBody", 5);
  body.innerHTML = data.customers.map((item) => `
    <tr>
      <td>${item.user_id}</td>
      <td>${item.segment}</td>
      <td>${item.recency_days} 天</td>
      <td>${item.frequency}</td>
      <td>${formatMoney(item.monetary)}</td>
    </tr>
  `).join("");
}

async function refreshCustomersPage() {
  const data = await apiGet("/analytics/pages/customers?limit=20");
  renderCustomersPage(data);
}

function buildChannelTrendDatasets(trends) {
  const months = [...new Set(trends.map((t) => t.month))].sort();
  const channels = [...new Set(trends.map((t) => t.channel))];
  return {
    labels: months,
    datasets: channels.map((channel) => ({
      label: formatChannelLabel(channel),
      data: months.map((month) => {
        const row = trends.find((t) => t.channel === channel && t.month === month);
        return row ? row.revenue : 0;
      }),
      borderColor: CHANNEL_COLORS[channel] || "#64748b",
      backgroundColor: "transparent",
      tension: 0.3,
      pointRadius: 2,
    })),
  };
}

function renderChannelsPage(data) {
  const s = data.summary;
  document.getElementById("channelCount").textContent = s.channel_count.toLocaleString("zh-TW");
  document.getElementById("topChannelName").textContent = s.top_channel || "—";
  document.getElementById("channelRevenue").textContent = formatMoney(s.total_revenue);

  destroyChart("channelPie");
  charts.channelPie = new Chart(document.getElementById("channelPieChart"), {
    type: "doughnut",
    data: {
      labels: data.channels.map((i) => i.channel_label),
      datasets: [{
        data: data.channels.map((i) => i.revenue),
        backgroundColor: data.channels.map((i) => CHANNEL_COLORS[i.channel] || "#94a3b8"),
        borderWidth: 0,
      }],
    },
    options: { plugins: { legend: { position: "bottom" } } },
  });

  destroyChart("channelAov");
  charts.channelAov = new Chart(document.getElementById("channelAovChart"), {
    type: "bar",
    data: {
      labels: data.channels.map((i) => i.channel_label),
      datasets: [{
        label: "平均客單價",
        data: data.channels.map((i) => i.avg_order_value),
        backgroundColor: data.channels.map((i) => CHANNEL_COLORS[i.channel] || "#94a3b8"),
        borderRadius: 8,
      }],
    },
    options: { plugins: { legend: { display: false } } },
  });

  const trendData = buildChannelTrendDatasets(data.trends);
  destroyChart("channelTrend");
  charts.channelTrend = new Chart(document.getElementById("channelTrendChart"), {
    type: "line",
    data: trendData,
    options: {
      plugins: { legend: { position: "bottom" } },
      scales: {
        x: { ticks: { maxTicksLimit: 8 } },
        y: { ticks: { callback: (v) => `NT$ ${Number(v).toLocaleString("zh-TW")}` } },
      },
    },
  });

  const body = document.getElementById("channelTableBody");
  if (!data.channels.length) return renderEmptyRow("channelTableBody", 4);
  body.innerHTML = data.channels.map((item) => `
    <tr>
      <td>${item.channel_label}</td>
      <td>${formatMoney(item.revenue)}</td>
      <td>${item.orders.toLocaleString("zh-TW")}</td>
      <td>${formatMoney(item.avg_order_value)}</td>
    </tr>
  `).join("");
}

async function refreshChannelsPage() {
  const data = await apiGet("/analytics/pages/channels");
  renderChannelsPage(data);
}

async function refreshCurrentPage() {
  if (currentPage === "overview") await refreshOverviewPage();
  else if (currentPage === "products") await refreshProductsPage();
  else if (currentPage === "customers") await refreshCustomersPage();
  else if (currentPage === "channels") await refreshChannelsPage();
  setLastUpdated();
}

async function handleLoadSample() {
  const button = document.getElementById("loadSampleBtn");
  button.disabled = true;
  button.textContent = "匯入中...";
  try {
    if (!(await checkApiHealth())) {
      throw new Error(`後端未啟動。請執行 start.bat，並開啟 ${LOCAL_ENTRY}`);
    }
    const result = await loadSampleData(true);
    if (!Number(result.rows_added || 0)) {
      throw new Error("模擬訂單匯入失敗，後端未寫入任何資料");
    }
    const status = await fetchImportStatus();
    if (Number(status.store?.total_rows || 0) === 0) {
      throw new Error(`模擬檔案有 ${status.sample_file?.total_rows || 0} 筆，但寫入失敗。`);
    }
    await refreshCurrentPage();
    showToast(`已匯入 ${Number(result.rows_added).toLocaleString("zh-TW")} 筆模擬訂單`);
    hideApiBanner();
  } catch (error) {
    showToast(error.message, true);
    showApiBanner(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "匯入模擬訂單";
  }
}

async function handleRefresh() {
  try {
    await refreshCurrentPage();
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
    await refreshCurrentPage();
    showToast("訂單匯入完成");
  } catch (error) {
    showToast(error.message, true);
  } finally {
    event.target.value = "";
  }
}

async function handleBrandChange() {
  try {
    await refreshCurrentPage();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function handleNavClick(event) {
  const page = event.currentTarget.dataset.page;
  if (!page || page === currentPage) return;
  switchPage(page);
  try {
    await refreshCurrentPage();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function initializeDashboard() {
  await loadBrandOptions();
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.addEventListener("click", handleNavClick);
  });

  if (!(await checkApiHealth())) {
    showApiBanner(
      `後端 API 未連線。請在 <code>shoplite</code> 資料夾雙擊 <code>start.bat</code>，再用瀏覽器開啟 <code>${LOCAL_ENTRY}</code>。`
    );
    return;
  }

  try {
    const status = await fetchImportStatus();
    if (status.store?.total_rows > 0 || status.sample_file?.total_rows > 0) {
      await refreshCurrentPage();
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
