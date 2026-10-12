import { cp, mkdir } from "node:fs/promises";

await mkdir("dist/renderer", { recursive: true });
await cp("src/renderer/index.html", "dist/renderer/index.html");
