export const dynamic = "force-dynamic";

export function GET() {
  const challenge = process.env.OPENAI_APPS_CHALLENGE?.trim();
  if (!challenge) {
    return new Response("OpenAI Apps challenge is not configured", {
      status: 503,
      headers: {
        "cache-control": "no-store",
        "content-type": "text/plain; charset=utf-8"
      }
    });
  }
  return new Response(challenge, {
    status: 200,
    headers: {
      "cache-control": "no-store",
      "content-type": "text/plain; charset=utf-8"
    }
  });
}
