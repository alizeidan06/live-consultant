import { createMcpHandler } from "mcp-handler";

import { registerLiveConsultantTools } from "../../lib/live-consultant-tools.js";

const handler = createMcpHandler(
  registerLiveConsultantTools,
  {
    serverInfo: {
      name: "live-consultant",
      version: "1.1.0"
    },
    capabilities: {
      tools: {}
    }
  },
  {
    basePath: "/",
    maxDuration: 60,
    verboseLogs: false,
    disableSse: true,
    redisUrl: undefined
  }
);

export const dynamic = "force-dynamic";
export const maxDuration = 60;
export { handler as GET, handler as POST, handler as DELETE };
