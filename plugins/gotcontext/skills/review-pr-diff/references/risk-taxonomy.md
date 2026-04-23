# PR diff risk taxonomy

Reference material for `review-pr-diff`. When a hunk touches any of
these areas, flag it explicitly in the **Risk flags** section and do
NOT compress at `balanced` (use `detailed` instead).

## Security-sensitive

- **Auth** — JWT signing / verification, password hashing, session
  handling, OAuth redirect URIs, PKCE, refresh token rotation
- **Crypto** — new cipher suites, key rotation, HMAC secrets, IV
  generation, random source
- **Access control** — RBAC role checks, ACL changes, permission
  middlewares, `@require_admin` decorators
- **SQL string building** — any raw SQL concatenation, format, or
  `%s`-style interpolation. Prefer parameterized queries.

## Data-sensitive

- **Migrations** — any DB schema change; especially `DROP`,
  `ALTER COLUMN`, or `NOT NULL` added on an existing table
- **Webhook handlers** — signature verification changes; replay
  protection
- **Cron / scheduled** — new recurring jobs, changed schedules
- **Billing** — Polar/Stripe integrations, subscription lifecycle,
  metering, quota enforcement
- **Deletion paths** — GDPR, account removal, data purges

## Operational

- **Environment variables** — new secrets, default changes,
  required-vs-optional
- **Dockerfile / CI** — base image changes, new RUN commands,
  secret exposure
- **Dependency bumps** — major version jumps; check changelogs
- **Public API surface** — new routes, auth changes to existing
  routes, breaking request/response schema changes

## Lockfile-in-risk-zone

Lockfile bumps are usually ignorable, EXCEPT when the diff also
touches one of the above categories — then re-examine the lockfile
hunk for added dependencies, not just version bumps.
