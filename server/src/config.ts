import { config as dotenvConfig } from "dotenv";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
dotenvConfig({ path: resolve(__dirname, "../../.env") });

export const config = {
  mongo: {
    uri: process.env.MONGO_URI ?? "",
    dbName: process.env.MONGO_DB_NAME ?? "pokemonduel",
  },
  redis: {
    url: process.env.REDIS_URL ?? "",
  },
  discord: {
    token: process.env.DISCORD_TOKEN ?? "",
    clientId: process.env.DISCORD_CLIENT_ID ?? "",
    clientSecret: process.env.DISCORD_CLIENT_SECRET ?? "",
    redirectUri:
      process.env.DISCORD_REDIRECT_URI ??
      "http://localhost:3001/api/auth/callback",
  },
  jwt: {
    secret: process.env.JWT_SECRET ?? "fallback_dev_secret_change_me",
  },
  server: {
    port: parseInt(process.env.API_PORT ?? "3001", 10),
    frontendUrl: process.env.FRONTEND_URL ?? "http://localhost:5173",
  },
  dataDir: resolve(__dirname, "../../pokemonduel/data"),
  userConfigDir: resolve(__dirname, "../../data/PokemonDuel"),
  geminiApiKey: process.env.GEMINI_API_KEY ?? "",
} as const;
