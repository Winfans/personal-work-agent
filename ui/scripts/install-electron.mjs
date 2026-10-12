import { existsSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { arch, platform } from "node:os";
import { dirname, join } from "node:path";
import { spawnSync } from "node:child_process";

const require = createRequire(import.meta.url);
const packagePath = require.resolve("electron/package.json");
const electronDirectory = dirname(packagePath);
const { version } = require(packagePath);

const platformName = platform();
const architecture = arch();
const supportedPlatforms = new Set(["darwin", "linux"]);

if (!supportedPlatforms.has(platformName)) {
  throw new Error(`Unsupported platform for this installer: ${platformName}`);
}

const archiveName = `electron-v${version}-${platformName}-${architecture}.zip`;
const mirror = process.env.ELECTRON_MIRROR
  ?? "https://cdn.npmmirror.com/binaries/electron/";
const url = `${mirror.replace(/\/+$/, "")}/v${version}/${archiveName}`;
const cacheDirectory = join(process.cwd(), ".cache", "electron");
const archivePath = join(cacheDirectory, archiveName);
const distPath = join(electronDirectory, "dist");
const executablePath = platformName === "darwin"
  ? "Electron.app/Contents/MacOS/Electron"
  : "electron";

mkdirSync(cacheDirectory, { recursive: true });

console.log(`Downloading Electron ${version} from:`);
console.log(url);
console.log("Interrupted downloads will resume on the next run.");

const download = spawnSync("curl", [
  "--fail",
  "--location",
  "--continue-at", "-",
  "--retry", "20",
  "--retry-all-errors",
  "--connect-timeout", "20",
  "--output", archivePath,
  url,
], { stdio: "inherit" });

if (download.status !== 0) {
  process.exit(download.status ?? 1);
}

rmSync(distPath, { recursive: true, force: true });
mkdirSync(distPath, { recursive: true });

const extract = spawnSync("unzip", ["-q", archivePath, "-d", distPath], {
  stdio: "inherit",
});

if (extract.status !== 0) {
  process.exit(extract.status ?? 1);
}

writeFileSync(join(electronDirectory, "path.txt"), executablePath);

const executable = join(distPath, executablePath);
if (!existsSync(executable)) {
  throw new Error(`Electron executable was not found at ${executable}`);
}

console.log(`Electron ${version} installed successfully.`);
