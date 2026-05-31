import { FastifyRequest, FastifyReply } from "fastify";
import { jwtVerify } from "jose";
import { config } from "../config.js";

export interface AuthUser {
  userId: string;
  username: string;
  avatar: string;
}

declare module "fastify" {
  interface FastifyRequest {
    user?: AuthUser;
  }
}

const secret = new TextEncoder().encode(config.jwt.secret);

export async function authMiddleware(
  request: FastifyRequest,
  reply: FastifyReply,
): Promise<void> {
  const token = request.cookies?.session;
  if (!token) {
    reply.status(401).send({ error: "Not authenticated" });
    return;
  }

  try {
    const { payload } = await jwtVerify(token, secret);
    request.user = {
      userId: payload.sub as string,
      username: payload.username as string,
      avatar: payload.avatar as string,
    };
  } catch {
    reply.status(401).send({ error: "Invalid or expired session" });
  }
}
