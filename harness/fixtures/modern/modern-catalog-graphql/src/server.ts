/**
 * Apollo Server entrypoint. Schema-first; the JWT scopes are extracted from the
 * API Gateway authorizer context and handed to resolvers.
 *
 * GAP (see README.md): no query depth/complexity limit is installed yet. A production
 * hardening pass should add `graphql-depth-limit` + a cost analysis plugin.
 */

import { readFileSync } from 'node:fs';
import { ApolloServer } from '@apollo/server';
import { startServerAndCreateLambdaHandler, handlers } from '@as-integrations/aws-lambda';
import { DynamoDBDocument } from '@aws-sdk/lib-dynamodb';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { resolvers } from './resolvers/catalog.js';

const typeDefs = readFileSync(new URL('../schema/catalog.graphql', import.meta.url), 'utf8');
const db = DynamoDBDocument.from(new DynamoDBClient({}));

const server = new ApolloServer({ typeDefs, resolvers });

export const handler = startServerAndCreateLambdaHandler(
  server,
  handlers.createAPIGatewayProxyEventV2RequestHandler(),
  {
    context: async ({ event }) => {
      const claims = (event.requestContext as any).authorizer?.jwt?.claims ?? {};
      return {
        db,
        scopes: new Set<string>((claims.scope ?? '').split(' ').filter(Boolean)),
        now: () => new Date().toISOString(),
      };
    },
  },
);
