import { FastifyInstance } from "fastify";

export function rateLimitConfig(): Parameters<FastifyInstance["register"]>[1] {
  return {
    max: 100,
    timeWindow: "1 minute",
  };
}
