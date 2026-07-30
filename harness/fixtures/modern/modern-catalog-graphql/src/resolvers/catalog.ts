/**
 * Catalog resolvers.
 *
 * Reads are open to any authenticated client; mutations require `catalog:write`.
 * upsertProduct is idempotent (upsert by SKU) and deleteProduct is a soft-delete,
 * so there is no irreversible destructive path here. The two known gaps are a
 * missing query-depth limit and a missing audit event on delete (see README.md).
 */

import { DynamoDBDocument } from '@aws-sdk/lib-dynamodb';

interface Context {
  db: DynamoDBDocument;
  scopes: Set<string>;
  now: () => string;
}

function requireScope(ctx: Context, scope: string): void {
  if (!ctx.scopes.has(scope)) {
    throw new Error(`forbidden: requires scope ${scope}`);
  }
}

export const resolvers = {
  Query: {
    async product(_: unknown, { sku }: { sku: string }, ctx: Context) {
      const { Item } = await ctx.db.get({ TableName: process.env.TABLE!, Key: { sku } });
      return Item ?? null;
    },
    async products(_: unknown, { limit, cursor }: { limit: number; cursor?: string }, ctx: Context) {
      const res = await ctx.db.scan({
        TableName: process.env.TABLE!,
        Limit: limit,
        ExclusiveStartKey: cursor ? JSON.parse(Buffer.from(cursor, 'base64').toString()) : undefined,
        FilterExpression: 'active = :a',
        ExpressionAttributeValues: { ':a': true },
      });
      return {
        items: res.Items ?? [],
        nextCursor: res.LastEvaluatedKey
          ? Buffer.from(JSON.stringify(res.LastEvaluatedKey)).toString('base64')
          : null,
      };
    },
  },
  Mutation: {
    // Idempotent: PutItem on the same SKU overwrites rather than duplicating.
    async upsertProduct(_: unknown, { input }: { input: Record<string, unknown> }, ctx: Context) {
      requireScope(ctx, 'catalog:write');
      const item = { ...input, active: true, updatedAt: ctx.now() };
      await ctx.db.put({ TableName: process.env.TABLE!, Item: item });
      return item;
    },
    // Soft-delete: recoverable. GAP: should emit an audit event capturing who/when.
    async deleteProduct(_: unknown, { sku }: { sku: string }, ctx: Context) {
      requireScope(ctx, 'catalog:write');
      const { Attributes } = await ctx.db.update({
        TableName: process.env.TABLE!,
        Key: { sku },
        UpdateExpression: 'SET active = :f, updatedAt = :t',
        ExpressionAttributeValues: { ':f': false, ':t': ctx.now() },
        ReturnValues: 'ALL_NEW',
      });
      return Attributes;
    },
  },
};
