import { MongoClient, Db } from "mongodb";
import { config } from "../config.js";

let client: MongoClient | null = null;
let db: Db | null = null;

async function createClient(): Promise<MongoClient> {
  const c = new MongoClient(config.mongo.uri, {
    serverSelectionTimeoutMS: 5000,
    connectTimeoutMS: 5000,
    socketTimeoutMS: 10000,
    maxPoolSize: 20,
    minPoolSize: 2,
    retryWrites: true,
    retryReads: true,
  });
  await c.connect();
  await c.db("admin").command({ ping: 1 });
  return c;
}

export async function connectMongo(): Promise<Db> {
  if (db) return db;

  try {
    client = await createClient();
    db = client.db(config.mongo.dbName);
    console.log(`[mongo] Connected — database=${config.mongo.dbName}`);
  } catch (err) {
    client = null;
    console.warn("[mongo] Initial connection failed:", (err as Error).message);
    throw err;
  }

  return db;
}

/** Return a healthy DB handle. Reconnects automatically on first use if the
 *  initial connection failed, or if the underlying socket went stale between
 *  serverless invocations. */
export async function getDb(): Promise<Db> {
  // Already connected and alive
  if (db) {
    try {
      await db.admin().command({ ping: 1 });
      return db;
    } catch {
      console.warn("[mongo] Connection stale — reconnecting...");
    }
  }

  // Close any leftover dead client before creating a fresh one
  if (client) {
    try { await client.close(); } catch { /* ignore */ }
    client = null;
  }
  db = null;

  client = await createClient();
  db = client.db(config.mongo.dbName);
  console.log("[mongo] Reconnected");
  return db;
}

export async function closeMongo(): Promise<void> {
  if (client) {
    await client.close();
    client = null;
    db = null;
    console.log("[mongo] Connection closed");
  }
}
