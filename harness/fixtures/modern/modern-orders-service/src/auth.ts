/**
 * JWT auth middleware. Verifies an RS256 bearer token against the JWKS and enforces
 * a required role claim. Real authN/authZ — this is NOT one of the fixture's gaps.
 */

import { FastifyReply, FastifyRequest } from 'fastify';
import { createRemoteJWKSet, jwtVerify } from 'jose';

const JWKS = createRemoteJWKSet(new URL(process.env.JWKS_URI ?? 'https://auth.example.com/.well-known/jwks.json'));

export function requireRole(role: string) {
  return async (req: FastifyRequest, reply: FastifyReply): Promise<void> => {
    const header = req.headers.authorization ?? '';
    if (!header.startsWith('Bearer ')) {
      await reply.code(401).send({ code: 'unauthorized', message: 'missing bearer token' });
      return;
    }
    try {
      const { payload } = await jwtVerify(header.slice(7), JWKS, {
        issuer: process.env.JWT_ISSUER,
        audience: 'orders-service',
      });
      const roles = (payload.roles as string[] | undefined) ?? [];
      if (!roles.includes(role)) {
        await reply.code(403).send({ code: 'forbidden', message: `requires role ${role}` });
      }
    } catch {
      await reply.code(401).send({ code: 'unauthorized', message: 'invalid token' });
    }
  };
}
