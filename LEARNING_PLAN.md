# Learning Plan: Production-Style Clinic Microservices

Goal: learn FastAPI, Postgres, Redis, RabbitMQ, Elasticsearch, Docker and Kubernetes by building a clinic app (doctor, patient, appointment, notification) the way a production system is built. Each stage adds one technology for a real reason and ends with something you can run and check.

## Target architecture
```
Browser -> nginx/Ingress -> auth-svc ──┐
                         -> clinic-svc  │
                         -> doctor-svc  │ (Postgres each)
                         -> patient-svc │
                         -> appointment-svc (Postgres + Redis lock/cache)
                                 │ publish events
                              RabbitMQ
                         ┌───────┴────────┐
                 notification-svc     search-indexer
                 (email via SMTP)     (-> Elasticsearch)
```

## Stage 0: Clean up the foundation (1–2 days)
- Untrack `.env`, `__pycache__` and venvs; add `.gitignore` and `.env.example`; rotate the JWT secret.
- Pin `requirements.txt`; add a `/health` endpoint to each service.
- Add pytest with a test database for the patient service (ownership tests).
- Learn: FastAPI dependencies, Pydantic settings, testing with `TestClient`.

## Stage 1: Auth service and Postgres depth (3–4 days)
- Extract login and registration into `auth-svc` with a `role` claim. (No `clinic_id` claim: memberships live in the clinic service, which checks them on every request so changes apply immediately.)
- Auth owns identity only (accounts, credentials, tokens); doctor and patient services keep profiles and reference the auth `user_id`.
- Build order: skeleton and health, `users` table with register/login, RS256 tokens and JWKS endpoint, refresh tokens with rotation and logout, password reset (emits an event), tests, then switch doctor and patient to validate auth's tokens. **Status:** users, register/login, RS256 + JWKS, refresh rotation and logout are done in auth; clinic, doctor and patient verify auth's tokens (doctor is now profile-only, linked by `user_id`). Remaining: frontend login against auth, root compose/nginx wiring.
- Switch to RS256 with `iss`/`aud` claims and a `type: "access"` claim; services get only the public key.
- Add refresh tokens, stored in Postgres.
- Postgres topics: indexes (`EXPLAIN ANALYZE`), unique constraints, safe Alembic migrations, connection pooling.
- Check: a patient-service token cannot be used to forge anything.

## Stage 1b: Clinic service (3–4 days)
- Clinic owns clinics, staff memberships (which user belongs to which clinic, with what role) and clinic settings or opening hours.
- Clinic checks membership per request (`require_clinic_role`). Other services that need clinic scoping ask the clinic service whether the caller (forwarding their token) is a member of `clinic_id`, instead of trusting a claim.
- Change patient records from `doctor_id` ownership to `clinic_id`; appointments link a patient to a specific doctor.
- Learn: multi-tenancy (scoping every query by clinic), role-based access checks as a reusable dependency.
- Check: a doctor in clinic A cannot read or edit clinic B's patients.

## Stage 2: Redis (2–3 days)
1. Rate limiting on `/login` (counter with TTL) to stop brute force.
2. Caching the patient list or doctor profile, with invalidation on update.
3. Token revocation: a denylist of logged-out `jti` values with the token's TTL.
- Learn: TTLs, cache-aside, why invalidation is hard.
- Check: watch hits and misses with `redis-cli MONITOR`.

## Stage 3: Appointment service (4–5 days)
- Model doctor schedules and slots. Double-booking must be impossible, enforced by a Postgres unique constraint; try to break it with concurrent requests.
- Optional short Redis lock while a user holds a slot.
- Store only IDs from other services (`clinic_id`, `doctor_id`, `patient_id`); no cross-DB foreign keys.
- Learn: transactions, isolation, idempotency keys, async SQLAlchemy.

## Stage 4: RabbitMQ and the notification service (4–5 days)
- Appointment service publishes `AppointmentBooked` to a topic exchange.
- Notification service consumes it and sends the email (move the existing SMTP code here; use Mailpit locally).
- Add manual acks, retries, a dead-letter queue and an idempotent consumer.
- Use the outbox pattern so a DB commit and a publish cannot disagree.
- Libraries: start with `aio-pika` to see the primitives.
- Check: stop the consumer, book appointments, restart and watch the queue drain; poison a message and find it in the DLQ.

## Stage 5: Elasticsearch (3–4 days)
- A search indexer consumes patient, doctor and clinic events and writes to Elasticsearch.
- Expose `GET /search/patients?q=` with fuzzy matching and filters.
- Learn: mappings, analyzers, index time vs query time, search as a read model (Postgres stays the source of truth).
- Check: rebuild the index from scratch from Postgres (reindex job).

## Stage 6: Docker, properly (2–3 days)
- Multi-stage builds, `.dockerignore`, slim images, healthchecks, non-root users.
- One compose file with profiles (infra only vs everything).
- Serve the frontend through nginx with relative `/api/v1` URLs instead of baked-in localhost URLs.
- Run migrations as a one-shot init job, not at container start.

## Stage 7: Kubernetes (1–2 weeks)
Use `kind` or `minikube`. In order:
1. Deployment and Service for one API with readiness and liveness probes.
2. ConfigMaps and Secrets.
3. StatefulSets (or Helm charts) for Postgres, Redis, RabbitMQ.
4. Ingress replaces nginx.
5. Migration Job, resource requests and limits, HPA, rolling updates with a deliberately broken image to practise rollback.
6. Optional: Helm or Kustomize for per-environment config.

## Stage 8: Observability (alongside stages 4–7)
- Structured JSON logs with a request ID that travels through events.
- Prometheus metrics and a Grafana dashboard.
- OpenTelemetry tracing to follow one booking across services.

## Production habits
- Every service has tests and a health endpoint.
- Every change comes with a migration.
- Configuration comes only from environment variables.
- Test every failure mode: kill a container and see what happens.
- Write a short ADR (a few lines) for each decision.

## Progress checklist
- [ ] Stage 0: foundation cleanup
- [ ] Stage 1: auth service, RS256, Postgres depth
- [ ] Stage 1b: clinic service, multi-tenancy
- [ ] Stage 2: Redis
- [ ] Stage 3: appointment service
- [ ] Stage 4: RabbitMQ and notification service
- [ ] Stage 5: Elasticsearch
- [ ] Stage 6: Docker
- [ ] Stage 7: Kubernetes
- [ ] Stage 8: Observability
