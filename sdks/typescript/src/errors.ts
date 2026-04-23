/**
 * Structured error thrown by {@link GotContext} for non-2xx HTTP responses.
 *
 * Mirrors the Python SDK's exception hierarchy (AuthError | RateLimitError |
 * ValidationError | ServerError) but flattened — inspect `status` to branch.
 */
export class ApiError extends Error {
  readonly name = 'ApiError';
  readonly status: number;
  readonly detail: unknown;

  constructor(status: number, message: string, detail: unknown = null) {
    super(message);
    this.status = status;
    this.detail = detail;
  }

  /** 401 / 403. */
  get isAuth(): boolean {
    return this.status === 401 || this.status === 403;
  }

  /** 429. */
  get isRateLimited(): boolean {
    return this.status === 429;
  }

  /** 400 / 422. */
  get isValidation(): boolean {
    return this.status === 400 || this.status === 422;
  }

  /** 5xx. */
  get isServer(): boolean {
    return this.status >= 500 && this.status < 600;
  }
}
