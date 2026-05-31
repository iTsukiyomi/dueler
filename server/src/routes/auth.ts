import { FastifyInstance } from "fastify";
import DiscordOAuth2 from "discord-oauth2";
import { SignJWT } from "jose";
import { config } from "../config.js";
import { getDb } from "../db/mongo.js";
import { authMiddleware } from "../middleware/auth.js";

const oauth = new DiscordOAuth2({
  clientId: config.discord.clientId,
  clientSecret: config.discord.clientSecret,
  redirectUri: config.discord.redirectUri,
});

const jwtSecret = new TextEncoder().encode(config.jwt.secret);

export async function authRoutes(app: FastifyInstance): Promise<void> {
  app.get("/api/auth/login", async (_request, reply) => {
    const url = oauth.generateAuthUrl({
      scope: ["identify"],
      responseType: "code",
    });
    reply.redirect(url);
  });

  app.get("/api/auth/callback", async (request, reply) => {
    const { code } = request.query as { code?: string };
    if (!code) {
      reply.status(400).send({ error: "Missing authorization code" });
      return;
    }

    try {
      const tokenData = await oauth.tokenRequest({
        code,
        scope: ["identify"],
        grantType: "authorization_code",
      });

      const discordUser = await oauth.getUser(tokenData.access_token);

      const db = getDb();
      const now = new Date();
      await db.collection("players").updateOne(
        { _id: discordUser.id as any },
        {
          $setOnInsert: {
            wins: 0,
            losses: 0,
            elo: 1000,
            wallet: 0,
            active_party_name: null,
            theme: "firered",
            gen: 5,
            moveset_img: true,
            created_at: now,
          },
          $set: {
            username: discordUser.username,
            updated_at: now,
          },
        },
        { upsert: true },
      );

      const avatarHash = discordUser.avatar ?? "";
      const token = await new SignJWT({
        username: discordUser.username,
        avatar: avatarHash,
      })
        .setProtectedHeader({ alg: "HS256" })
        .setSubject(discordUser.id)
        .setIssuedAt()
        .setExpirationTime("7d")
        .sign(jwtSecret);

      reply
        .setCookie("session", token, {
          path: "/",
          httpOnly: true,
          sameSite: "lax",
          secure: false,
          maxAge: 7 * 24 * 60 * 60,
        })
        .redirect(`${config.server.frontendUrl}/dashboard`);
    } catch (err) {
      console.error("[auth] OAuth callback error:", err);
      reply.status(500).send({ error: "Authentication failed" });
    }
  });

  app.get(
    "/api/auth/me",
    { preHandler: authMiddleware },
    async (request, reply) => {
      const user = request.user!;
      const avatarUrl = user.avatar
        ? `https://cdn.discordapp.com/avatars/${user.userId}/${user.avatar}.png?size=128`
        : `https://cdn.discordapp.com/embed/avatars/${parseInt(user.userId) % 5}.png`;

      reply.send({
        id: user.userId,
        username: user.username,
        avatar: user.avatar,
        avatarUrl,
      });
    },
  );

  app.post("/api/auth/logout", async (_request, reply) => {
    reply
      .clearCookie("session", { path: "/" })
      .send({ success: true });
  });
}
