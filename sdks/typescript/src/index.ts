export {
  applyAnthropicBreakpoints,
  type AnthropicContentBlock,
  type AnthropicMessage,
  type CacheBreakpoint,
} from './cache-helpers.js';
export { GotContext, type GotContextOptions } from './client.js';
export { ApiError } from './errors.js';
export { metaForCall, type ToolMeta } from './mcp-helpers.js';
export type {
  BatchCompressResponse,
  BatchDocument,
  BatchItemResult,
  CompressCodeRequest,
  CompressCodeResponse,
  CompressRequest,
  CompressResponse,
  CompressStats,
  Fidelity,
  HitSourceBreakdown,
  RankedContextItem,
  SemanticCacheThresholdResponse,
  StructuralCompressRequest,
  StructuralCompressResponse,
  StructuralCompressStats,
  StructuralFile,
  UsageResponse,
} from './types.js';

export const VERSION = '0.5.2';
