let app: any = null;

export default async function handler(req: any, res: any) {
  try {
    if (!app) {
      const { initApp } = await import("../server/src/app.js");
      app = await initApp();
      await app.ready();
    }
    app.server.emit("request", req, res);
  } catch (err) {
    console.error("[vercel] Handler error:", err);
    res.statusCode = 500;
    res.end(JSON.stringify({ error: "Internal server error" }));
  }
}
