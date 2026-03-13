# SUPT Inbox Upgrade Standards

This repository is not currently an inbox platform. The code in `/opt/uniforma` is a single-tenant product administration system with product, sync, and diagnostics flows. It does not contain conversations, cases, tenant-scoped inbox objects, Redis inbox orchestration, or AI inbox agents. These standards define the target bar for any future SUPT inbox implementation and document the vendor patterns researched on March 13, 2026.

## Vendor Baseline

### Thread model

- Zendesk, Intercom, Freshdesk, and Help Scout all center work around a durable conversation or ticket thread that aggregates channel messages, attachments, metadata, assignee, status, tags, and audit history.
- Common production requirement: keep one canonical thread identifier, one participant model, append-only message events, and derived state projections for views and SLA timers.

### SLA handling

- All four support response-time tracking with timers derived from policy, business hours, and priority.
- Production rule: persist SLA policy evaluation results on the conversation, emit breach and warning events, and recompute on assignment/state changes.

### Assignment logic

- Vendor patterns include manual assignment, round-robin/team routing, load balancing, skill-based routing, and reopen-to-last-owner behaviors.
- Production rule: separate assignment rules from execution, log each decision, and make AI recommendations advisory unless explicitly configured to auto-assign.

### Triggers and automations

- All four expose event-driven rules such as "on create", "on reply", "on status change", and time-based automations.
- Production rule: triggers must be idempotent, tenant-scoped, auditable, and protected from infinite loops.

### Macros

- Macros combine canned replies with state updates, tags, assignee changes, and follow-up actions.
- Production rule: macros are versioned tenant assets with RBAC, preview, dry-run validation, and audit logs.

### Routing

- Routing typically uses channel, team, language, customer segment, priority, and intent.
- Production rule: routing inputs are normalized first, decisions are deterministic, and fallback queues always exist.

### Email channel management

- Inbox platforms support shared addresses, aliases, forwarding/SMTP configuration, signatures, reply-from alias selection, and threading by message IDs.
- Production rule: channel credentials are encrypted, reply address selection is explicit, and inbound/outbound message IDs are stored for dedupe and threading.

### Conversation states

- Common states: open, pending, snoozed/on hold, solved/closed, spam/junk, deleted/archived.
- Production rule: state transitions are explicit, validated, and generate timeline events.

### Filters and views

- Shared/team/personal views are first-class in each product.
- Production rule: filter expressions are validated server-side, saved views are tenant-owned, and counts are derived from indexed projections.

### Audit logging

- All products keep actor, action, before/after changes, timestamps, and often automation source.
- Production rule: every state mutation, assignment change, macro execution, trigger execution, and AI action writes an immutable audit event.

### Merge and split conversations

- Zendesk, Freshdesk, and Help Scout expose merge flows; split/fork is more selective but the pattern is common in modern inbox tooling.
- Production rule: merges must preserve source thread lineage; splits create a new thread linked back to the origin event/message range.

## Architecture Standards

- Use a canonical `conversation_threads` aggregate with append-only `conversation_events`.
- Persist derived tables for inbox views, SLA timers, routing state, unread counts, and AI recommendations.
- Keep channel adapters isolated from domain logic.
- Every tenant-owned table must have `tenant_id NOT NULL` plus composite indexes matching read patterns.
- No cross-tenant joins without an explicit tenant predicate on every joined table.

## Multi-Tenant Enforcement Rules

- Every API request resolves one tenant context before touching data.
- Every repository method accepts tenant context and applies it in SQL, not in memory.
- Background jobs, triggers, AI workers, and webhooks must carry tenant context end-to-end.
- Unique constraints must be tenant-scoped unless the field is globally unique by design.

## RBAC Requirements

- Minimum roles: `platform_admin`, `tenant_admin`, `supervisor`, `agent`, `viewer`, `ai_service`.
- Write paths require server-side role checks and tenant membership checks.
- Macros, triggers, channel configuration, and AI autonomy settings require elevated roles.
- Audit logs must record both the authenticated actor and the effective role used for authorization.

## Code Conventions

- Domain services own workflows; repositories own persistence; routers stay thin.
- Prefer explicit DTOs/schemas over raw ORM payloads.
- Mutations must be transactional and emit audit events in the same unit of work.
- Frontend data access goes through a single typed API layer with no mock fallbacks in production code.
- Error states must be visible to the user; no silent `catch` blocks that discard failures.

## Deployment Policy

- Schema migrations ship before feature flags are enabled.
- Inbox automation defaults to safe mode until verification passes.
- Rebuild and health-check API, workers, Redis connectivity, and frontend before promotion.
- Production deploys require endpoint sweep, RBAC matrix checks, tenant isolation checks, and queue health validation.

## Git Policy

- One logical feature per commit when feasible.
- Do not mix schema changes, unrelated refactors, and UI restyling without a direct runtime reason.
- Commit messages should name the inbox capability or integrity fix being shipped.

## Verification Pipeline

- API health and auth smoke tests
- Tenant isolation tests
- RBAC matrix tests
- Conversation lifecycle tests
- Trigger idempotency tests
- SLA countdown and breach tests
- Routing determinism tests
- Merge/split lineage tests
- AI action audit-log tests
- Frontend production build plus runtime error-boundary coverage

## Inbox Feature Checklist

- Conversation thread model with message/event timeline
- Assignment engine with manual and rule-based routing
- SLA policies, timers, warnings, and breach tracking
- Trigger engine with audit trails and loop protection
- Macros with preview and versioning
- Email inbox and alias management
- Internal notes and collision detection
- Merge/split conversations with lineage
- Advanced filters and saved views
- Immutable audit log for user, automation, and AI actions
