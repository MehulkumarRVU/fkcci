# Production Readiness Checklist

Assessment date: 2026-11-08. This is a gate matrix, not a launch approval.

| Area | Status | Evidence | Remaining work |
|---|---|---|---|
| PostgreSQL fresh schema | PASS | Compose database initialized repeatedly; 10 tables inspected. | Continue migration discipline. |
| PostgreSQL upgrade | PARTIAL | Synthetic previous schema and user/session compatibility smoke test; lock-timeout failure rolled back partial DDL, then retry succeeded. | Production-like sanitized upgrade and formal versioned migration chain. |
| Backup/restore | PARTIAL | Current checksum scripts restored user/password hash, adaptive profile, completed session/history; tampered dump rejected before target creation. | Secure off-host copy, schedule/alert verification, production-sized restore and measured RTO. |
| SMTP | PARTIAL | Production validation requires host/from, STARTTLS, paired credentials; SMTP timeout added. | Configure provider and test reset delivery/error handling. |
| HTTPS/TLS | PARTIAL | TLS Nginx Compose override and redirect/HSTS configuration syntax-checked. | Supply valid certificate, verify public TLS/renewal and camera access. |
| CORS | PARTIAL | Wildcard rejected in production. | Verify explicit deployed origins and preflight. |
| Secrets | PARTIAL | Compose requires signing/database secrets; default/short production key rejected. | Connect secret manager, document and rehearse rotation. |
| Monitoring | PARTIAL | Readiness endpoint, request IDs/structured request logs, service health checks. | Configure dashboards, metrics, alerts, retention, test delivery. |
| Security assessment | PARTIAL | Internal focused review and regression/live checks. | Independent assessment and dependency scan. |
| Authenticated load testing | PARTIAL | Synthetic API workflows completed at 10/25/50/100 concurrent users; 0 HTTP errors, latency degraded markedly at 100. | Capture authoritative resource/DB metrics, improve bottlenecks, then run sustained/real-video tests. |
| Android testing | NOT TESTED | Device checklist prepared. | Run on physical Android Chrome. |
| iOS/iPad testing | NOT TESTED | Device checklist prepared. | Run on physical iPhone/iPad Safari. |
| Desktop camera | NOT TESTED | Device checklist prepared. | Test webcam, permissions, disconnect, and recovery. |
| Athlete pilot | BLOCKED | Consent-first plan only; no users invited. | Approvals, device gate, privacy/retention and support readiness. |
| Multi-sport AI | PARTIAL | Existing experimental classifier: 68.93% accuracy, macro-F1 60.65%; model plan and source catalog exist. | No local videos found in the prior inventory; verify licenses, collect/annotate consented temporal data, split by athlete, evaluate independent models. |

## Decision

**PARTIAL — not production-ready for external public access.** Do not launch
publicly or invite athletes until recoverability, production infrastructure,
independent security, authenticated load, and physical-device gates are
completed. The database backup-and-restore test is the highest-priority
recovery gate.

## Milestones

1. Infrastructure: representative PostgreSQL upgrade; checksum-verified,
   off-host backup/restore; SMTP; TLS; managed secrets.
2. Operations: dashboards, alert delivery, independent security assessment,
   authenticated and sustained load.
3. Product: real-device camera matrix, privacy approval, then a small,
   consenting Boxing/Table Tennis/Badminton pilot.
4. AI: licensed multi-sport video, consent and annotation pipeline, temporal
   landmark features, athlete-independent splits, versioned models, and
   independent evaluation. Keep experimental models out of live coaching.
