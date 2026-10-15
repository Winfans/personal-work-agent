import { app, BrowserWindow } from "electron";
import path from "node:path";

const createWindow = (): void => {
  const window = new BrowserWindow({
    width: 1180,
    height: 780,
    minWidth: 760,
    minHeight: 560,
    titleBarStyle: "hiddenInset",
    backgroundColor: "#fbfaf7",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  const developmentUrl = process.env.VITE_DEV_SERVER_URL;
  if (developmentUrl) {
    void window.loadURL(developmentUrl);
  } else {
    void window.loadFile(path.join(__dirname, "../renderer/index.html"));
  }
};

void app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
