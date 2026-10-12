declare global {
  interface Window {
    electronAPI: {
      platform: string;
    };
  }
}

const platform = document.querySelector<HTMLElement>("#platform");

if (platform) {
  platform.textContent = window.electronAPI.platform;
}

export {};
