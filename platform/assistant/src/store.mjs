// The one storage interface the ledger and the rate limits use, and its DynamoDB form.
//
// A write is a list of operations applied all together or not at all (a DynamoDB transaction).
// Each operation adds numbers to one item, optionally sets a time-to-live, and may carry
// conditions of one shape only: "this attribute is absent or at most N". That shape is enough
// for a cap: reserve r under cap C by adding r on condition "committed <= C - r". DynamoDB checks
// the condition and applies the addition atomically, so two calls cannot both take the last
// cent, whatever their timing.
//
//   op = { key, add: { attr: delta, ... }, ttl?: epochSeconds, atMost?: { attr: limit, ... } }
//
// A failed condition throws ConditionFailed with the index of the first failing operation.
// putNew(key, strings) writes an item only if none exists (the salt in limits.mjs).

export class ConditionFailed extends Error {
  constructor(index) {
    super(`condition failed on operation ${index}`);
    this.name = 'ConditionFailed';
    this.index = index;
  }
}

/** The TransactWriteItems request for these operations (pure, so the translation is tested). */
export function toTransactItems(ops, table) {
  return ops.map((op) => {
    const names = {};
    const values = {};
    const adds = Object.entries(op.add ?? {}).map(([attr, delta], i) => {
      names[`#a${i}`] = attr;
      values[`:a${i}`] = { N: String(delta) };
      return `#a${i} :a${i}`;
    });
    let expr = adds.length ? `ADD ${adds.join(', ')}` : '';
    if (op.ttl) {
      names['#ttl'] = 'expiresAt';
      values[':ttl'] = { N: String(op.ttl) };
      expr += `${expr ? ' ' : ''}SET #ttl = if_not_exists(#ttl, :ttl)`;
    }
    const conds = Object.entries(op.atMost ?? {}).map(([attr, limit], i) => {
      names[`#c${i}`] = attr;
      values[`:c${i}`] = { N: String(limit) };
      return `(attribute_not_exists(#c${i}) OR #c${i} <= :c${i})`;
    });
    const update = {
      TableName: table,
      Key: { pk: { S: op.key } },
      UpdateExpression: expr,
      ExpressionAttributeNames: names,
      ExpressionAttributeValues: values,
    };
    if (conds.length) update.ConditionExpression = conds.join(' AND ');
    return { Update: update };
  });
}

/** Numbers out of a DynamoDB item; strings and other types are left out. */
function plainItem(item) {
  if (!item) return null;
  const out = {};
  for (const [k, v] of Object.entries(item)) {
    if (v && typeof v.N === 'string') out[k] = Number(v.N);
    else if (v && typeof v.S === 'string') out[k] = v.S;
  }
  return out;
}

/**
 * The store over DynamoDB. The AWS SDK for JavaScript v3 ships with the Lambda Node.js runtime,
 * so it is imported here only, and only when the function runs; tests never load it.
 */
export async function dynamoStore(table, region) {
  const ddb = await import('@aws-sdk/client-dynamodb');
  const client = new ddb.DynamoDBClient({ region, maxAttempts: 2 });
  return {
    async write(ops) {
      // A transaction cancelled only because another one touched the same item at the same
      // moment (TransactionConflict) applied nothing, so it is safe to try again, a few times.
      for (let attempt = 1; ; attempt += 1) {
        try {
          await client.send(new ddb.TransactWriteItemsCommand({ TransactItems: toTransactItems(ops, table) }));
          return;
        } catch (e) {
          if (e?.name !== 'TransactionCanceledException') throw e;
          const reasons = e.CancellationReasons ?? [];
          const index = reasons.findIndex((r) => r?.Code === 'ConditionalCheckFailed');
          if (index >= 0) throw new ConditionFailed(index);
          const conflictOnly = reasons.length > 0 && reasons.every((r) => !r?.Code || r.Code === 'None' || r.Code === 'TransactionConflict');
          if (!conflictOnly || attempt >= 4) throw e;
          await new Promise((r) => setTimeout(r, 20 * attempt + Math.floor(Math.random() * 30)));
        }
      }
    },
    async putNew(key, strings) {
      const Item = { pk: { S: key } };
      for (const [k, v] of Object.entries(strings)) Item[k] = { S: String(v) };
      try {
        await client.send(new ddb.PutItemCommand({ TableName: table, Item, ConditionExpression: 'attribute_not_exists(pk)' }));
        return true;
      } catch (e) {
        if (e?.name === 'ConditionalCheckFailedException') return false;
        throw e;
      }
    },
    async read(key) {
      const out = await client.send(new ddb.GetItemCommand({ TableName: table, Key: { pk: { S: key } }, ConsistentRead: true }));
      return plainItem(out.Item);
    },
  };
}

/**
 * The same interface in memory, with DynamoDB's semantics: conditions are checked and additions
 * applied in one step, all operations or none. `delay` lets tests interleave many writers.
 */
export function memoryStore({ delay } = {}) {
  const items = new Map();
  return {
    items,
    async write(ops) {
      if (delay) await delay();
      // Everything below runs without yielding, as one transaction does.
      ops.forEach((op, i) => {
        const item = items.get(op.key) ?? {};
        for (const [attr, limit] of Object.entries(op.atMost ?? {})) {
          if (attr in item && !(item[attr] <= limit)) throw new ConditionFailed(i);
        }
      });
      for (const op of ops) {
        const item = { ...(items.get(op.key) ?? {}) };
        for (const [attr, delta] of Object.entries(op.add ?? {})) item[attr] = (item[attr] ?? 0) + delta;
        if (op.ttl && item.expiresAt === undefined) item.expiresAt = op.ttl;
        items.set(op.key, item);
      }
    },
    async putNew(key, strings) {
      if (delay) await delay();
      if (items.has(key)) return false;
      items.set(key, { ...strings });
      return true;
    },
    async read(key) {
      if (delay) await delay();
      const item = items.get(key);
      return item ? { ...item } : null;
    },
  };
}
