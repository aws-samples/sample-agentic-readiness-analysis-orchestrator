/**
 * Orders API routes.
 *
 * The service is modern and well-typed, but three of these operations are
 * irreversible and run with NO human-in-the-loop confirmation and NO idempotency.
 * That is the deliberate risk this fixture encodes: safe for a human operator,
 * unsafe to hand to an autonomous agent until the gaps in SAFETY.md are closed.
 */

import { FastifyInstance, FastifyReply, FastifyRequest } from 'fastify';
import { OrderService } from './services/order-service';
import { requireRole } from './auth';

export async function registerRoutes(app: FastifyInstance, orders: OrderService): Promise<void> {
  // ---- Reads: safe, no side effects -------------------------------------------------
  app.get('/orders/:id', { preHandler: requireRole('orders:read') }, async (req, reply) => {
    const order = await orders.get((req.params as { id: string }).id);
    if (!order) return reply.code(404).send({ code: 'not_found', message: 'order not found' });
    return order;
  });

  app.post('/orders', { preHandler: requireRole('orders:write') }, async (req, reply) => {
    const order = await orders.create(req.body as Record<string, unknown>);
    return reply.code(201).send(order);
  });

  // ---- Irreversible: hard delete of customer PII, no confirmation, no audit ----------
  // RISK: an agent retrying a timed-out call destroys the row permanently. There is no
  // soft-delete and no audit record of who deleted what.
  app.delete('/orders/:id', { preHandler: requireRole('orders:write') }, async (req, reply) => {
    await orders.hardDelete((req.params as { id: string }).id);
    return reply.code(204).send();
  });

  // ---- Irreversible: real money movement, NO idempotency key -------------------------
  // RISK: a duplicate POST double-refunds. There is no Idempotency-Key and no approval gate.
  app.post('/orders/:id/refund', { preHandler: requireRole('orders:write') }, async (req, reply) => {
    const { amount } = req.body as { amount: number };
    const refund = await orders.refund((req.params as { id: string }).id, amount);
    return reply.code(200).send(refund);
  });

  // ---- Irreversible downstream side effect: warehouse dispatch cancellation ----------
  // RISK: cancels a physical shipment with no dry-run and no human confirmation.
  app.post('/orders/:id/cancel', { preHandler: requireRole('orders:write') }, async (req, reply) => {
    const result = await orders.cancelAndRecallShipment((req.params as { id: string }).id);
    return reply.code(200).send(result);
  });
}
