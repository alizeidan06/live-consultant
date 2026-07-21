import { liveConsultantStatus } from "../../lib/live-consultant-knowledge.js";
import { assertLiveConsultantRuntimeReady } from "../../lib/live-consultant-runtime.js";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const [, status] = await Promise.all([
      assertLiveConsultantRuntimeReady(),
      liveConsultantStatus()
    ]);
    return Response.json(
      { ok: true, ...status },
      { headers: { "cache-control": "no-store" } }
    );
  } catch {
    return Response.json(
      { ok: false, error: "Live Consultant runtime is unavailable" },
      { status: 503, headers: { "cache-control": "no-store" } }
    );
  }
}
