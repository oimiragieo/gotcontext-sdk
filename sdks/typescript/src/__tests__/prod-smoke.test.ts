import { describe, expect, it } from 'vitest';
import { GotContext } from '../client.js';

// Nightly live-prod smoke for the published @gotcontext/sdk.
//
// Skipped unless PROD_SMOKE_GC_API_KEY is set. The nightly workflow
// injects the secret; PR runs leave it unset. The goal is to catch
// breakage that only surfaces when a published package talks to the
// live API — changed response shapes, default base URL drift, auth
// header rename, etc. Unit coverage for the SDK's own logic lives in
// the other __tests__/ files.

const API_KEY = process.env.PROD_SMOKE_GC_API_KEY ?? '';

describe.skipIf(!API_KEY)('prod smoke', () => {
  it('compress returns compressed body or stats', async () => {
    const gc = new GotContext({ apiKey: API_KEY });
    const res = await gc.compress({ text: 'smoke '.repeat(20), fidelity: 'balanced' });

    const hasShape = 'compressed' in res || 'stats' in res;

    expect(hasShape).toBe(true);
  });
});
