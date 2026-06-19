const { existsSync } = require("fs");
const { spawnSync } = require("child_process");
const path = require("path");

const root = path.join(__dirname, "..");
const sampleJson = path.join(root, "data", "sample_orders.json");

function run(command, args) {
  const result = spawnSync(command, args, {
    cwd: root,
    stdio: "inherit",
    shell: true,
  });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

run("python", ["-m", "pip", "install", "-r", "requirements.txt"]);

if (!existsSync(sampleJson)) {
  console.log("正在產生模擬訂單資料...");
  run("python", ["scripts/generate_sample_data.py"]);
}
