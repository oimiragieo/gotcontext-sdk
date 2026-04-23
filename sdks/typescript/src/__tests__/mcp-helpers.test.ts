import { describe, expect, it } from 'vitest';
import { metaForCall } from '../mcp-helpers.js';

describe('metaForCall', () => {
  it('includes model when provided', () => {
    expect(metaForCall({ model: 'claude-opus-4.6' })).toEqual({ model: 'claude-opus-4.6' });
  });

  it('returns empty when nothing provided', () => {
    expect(metaForCall()).toEqual({});
  });

  it('passes extra fields through', () => {
    expect(metaForCall({ model: 'x', traceId: 'abc' })).toEqual({ model: 'x', traceId: 'abc' });
  });

  it('filters out null and undefined values (v0.2.0 convention)', () => {
    expect(metaForCall({ model: undefined, traceId: undefined })).toEqual({});
    expect(metaForCall({ model: 'x', traceId: null as unknown as undefined })).toEqual({
      model: 'x',
    });
  });

  it('preserves falsy-but-meaningful values like 0, false, empty string', () => {
    expect(metaForCall({ count: 0, enabled: false, note: '' })).toEqual({
      count: 0,
      enabled: false,
      note: '',
    });
  });
});
