import { MongoClient, Db } from "mongodb";
import { config } from "../config.js";

let client: MongoClient | null = null;
let db: Db | null = null;

export async function connectMongo(): Promise<Db> {
  if (db) return db;

  client = new MongoClient(config.mongo.uri, {
    serverSelectionTimeoutMS: 5000,
    connectTimeoutMS: 5000,
    socketTimeoutMS: 10000,
    maxPoolSize: 20,
    minPoolSize: 2,
    retryWrites: true,
    retryReads: true,
  });

  await client.connect();
  await client.db("admin").command({ ping: 1 });
  db = client.db(config.mongo.dbName);
  console.log(`[mongo] Connected — database=${config.mongo.dbName}`);
  return db;
}

/** Get a healthy DB handle — reconnects automatically if the connection went stale (common on serverless cold/warm transitions). */
export async function getDb(): Promise<Db> {
  if (!db) throw new Error("MongoDB not connected — call connectMongo() first");

  try {
    await db.admin().command({ ping: 1 });
    return db;
  } catch {
    console.warn("[mongo] Connection is stale, reconnecting...");
    db = null;
    client = null;
    return connectMongo();
  }
}

export async function closeMongo(): Promise<void> {
  if (client) {
    await client.close();
    client = null;
    db = null;
    console.log("[mongo] Connection closed");
  }
}
