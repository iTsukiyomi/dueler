export default async function handler(req: any, res: any) {
  const { initApp } = await import("../server/src/app.js");
  const app = await initApp();
  await app.ready();
  app.server.emit("request", req, res);
}
