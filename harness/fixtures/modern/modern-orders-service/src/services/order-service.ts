/**
 * Order domain service. Clean, typed, testable — but note the irreversible
 * operations (hardDelete, refund, cancelAndRecallShipment) run with no idempotency
 * key and no approval gate. See SAFETY.md.
 */

import { Pool } from 'pg';

export interface Order {
  id: string;
  customerId: string;
  status: 'placed' | 'shipped' | 'cancelled' | 'refunded';
  totalCents: number;
}

export class OrderService {
  constructor(private readonly db: Pool, private readonly warehouse: WarehouseClient) {}

  async get(id: string): Promise<Order | null> {
    const { rows } = await this.db.query('SELECT * FROM orders WHERE id = $1', [id]);
    return rows[0] ?? null;
  }

  async create(input: Record<string, unknown>): Promise<Order> {
    const { rows } = await this.db.query(
      'INSERT INTO orders (customer_id, total_cents, status) VALUES ($1, $2, $3) RETURNING *',
      [input.customerId, input.totalCents, 'placed'],
    );
    return rows[0];
  }

  /** IRREVERSIBLE: removes the row and its PII. No soft-delete, no audit trail. */
  async hardDelete(id: string): Promise<void> {
    await this.db.query('DELETE FROM orders WHERE id = $1', [id]);
  }

  /** IRREVERSIBLE: issues a real refund. No Idempotency-Key => a retry double-refunds. */
  async refund(id: string, amountCents: number): Promise<{ id: string; amountCents: number }> {
    await this.db.query('UPDATE orders SET status = $1 WHERE id = $2', ['refunded', id]);
    // Calls the payment processor directly; no idempotency, no approval threshold.
    const refundId = await this.warehouse.issueRefund(id, amountCents);
    return { id: refundId, amountCents };
  }

  /** IRREVERSIBLE downstream side effect: recalls a physical shipment. No dry-run. */
  async cancelAndRecallShipment(id: string): Promise<{ cancelled: boolean }> {
    await this.db.query('UPDATE orders SET status = $1 WHERE id = $2', ['cancelled', id]);
    await this.warehouse.recallDispatch(id);
    return { cancelled: true };
  }
}

export interface WarehouseClient {
  issueRefund(orderId: string, amountCents: number): Promise<string>;
  recallDispatch(orderId: string): Promise<void>;
}
