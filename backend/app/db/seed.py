import uuid
from datetime import datetime, timezone, timedelta
from app.db.session import SessionLocal
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User
from app.models.service import Service
from app.models.escalation import EscalationPolicy, EscalationRule
from app.models.incident import Incident, IncidentEvent, IncidentAssignment, IncidentUpdate
from app.models.alert import Alert
from app.models.audit import AuditEvent
from app.models.notification import Notification
from app.models.enums import UserRole, ServiceHealth, Severity, IncidentStatus, AlertStatus
from app.services.alert_service import generate_alert_fingerprint

def seed_database():
    db = SessionLocal()
    try:
        print("[SEED] Seeding OpsPulse AI database with realistic enterprise data...")

        # 1. Organization
        org = db.query(Organization).filter(Organization.slug == "acme-cloud").first()
        if not org:
            org = Organization(
                name="Acme Cloud Infrastructure",
                slug="acme-cloud",
                created_at=datetime.now(timezone.utc) - timedelta(days=60)
            )
            db.add(org)
            db.flush()
        print(f"  Organization: {org.name} ({org.id})")

        # 2. Users
        users_data = [
            ("admin@opspulse.local", "Alex Mercer", "admin123", UserRole.ADMIN),
            ("responder@opspulse.local", "Sarah Chen", "responder123", UserRole.RESPONDER),
            ("devops@opspulse.local", "Marcus Brody", "devops123", UserRole.RESPONDER),
            ("lead@opspulse.local", "Elena Rostova", "lead123", UserRole.RESPONDER),
            ("sre@opspulse.local", "David Kim", "sre123", UserRole.RESPONDER),
        ]
        user_map = {}
        for email, full_name, password, role in users_data:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    organization_id=org.id,
                    email=email,
                    full_name=full_name,
                    hashed_password=hash_password(password),
                    role=role,
                    is_active=True,
                    created_at=datetime.now(timezone.utc) - timedelta(days=30)
                )
                db.add(user)
                db.flush()
            user_map[email] = user
            print(f"  User: {full_name} <{email}> [{role.value}]")

        # 3. Escalation Policies
        policy1 = db.query(EscalationPolicy).filter(
            EscalationPolicy.organization_id == org.id,
            EscalationPolicy.name == "Critical Infrastructure SLA"
        ).first()
        if not policy1:
            policy1 = EscalationPolicy(
                organization_id=org.id,
                name="Critical Infrastructure SLA",
                description="Fast-escalation policy for tier-1 customer-facing production services. 2-minute ack timeout.",
                ack_timeout_seconds=120,
                is_active=True,
                created_at=datetime.now(timezone.utc) - timedelta(days=20)
            )
            db.add(policy1)
            db.flush()

            # Rules: Level 1: Sarah, Level 2: Marcus, Level 3: Elena
            r1 = EscalationRule(escalation_policy_id=policy1.id, level_number=1, user_id=user_map["responder@opspulse.local"].id)
            r2 = EscalationRule(escalation_policy_id=policy1.id, level_number=2, user_id=user_map["devops@opspulse.local"].id)
            r3 = EscalationRule(escalation_policy_id=policy1.id, level_number=3, user_id=user_map["lead@opspulse.local"].id)
            db.add_all([r1, r2, r3])
            db.flush()

        policy2 = db.query(EscalationPolicy).filter(
            EscalationPolicy.organization_id == org.id,
            EscalationPolicy.name == "Payments Platform Urgent SLA"
        ).first()
        if not policy2:
            policy2 = EscalationPolicy(
                organization_id=org.id,
                name="Payments Platform Urgent SLA",
                description="Dedicated on-call schedule for payment processing with strict escalation.",
                ack_timeout_seconds=60,
                is_active=True,
                created_at=datetime.now(timezone.utc) - timedelta(days=20)
            )
            db.add(policy2)
            db.flush()

            r1 = EscalationRule(escalation_policy_id=policy2.id, level_number=1, user_id=user_map["devops@opspulse.local"].id)
            r2 = EscalationRule(escalation_policy_id=policy2.id, level_number=2, user_id=user_map["responder@opspulse.local"].id)
            db.add_all([r1, r2])
            db.flush()

        policy3 = db.query(EscalationPolicy).filter(
            EscalationPolicy.organization_id == org.id,
            EscalationPolicy.name == "Staging & Internal Best Effort"
        ).first()
        if not policy3:
            policy3 = EscalationPolicy(
                organization_id=org.id,
                name="Staging & Internal Best Effort",
                description="Low-priority on-call schedule for non-production environments with 15-minute SLA.",
                ack_timeout_seconds=900,
                is_active=True,
                created_at=datetime.now(timezone.utc) - timedelta(days=20)
            )
            db.add(policy3)
            db.flush()

            r1 = EscalationRule(escalation_policy_id=policy3.id, level_number=1, user_id=user_map["sre@opspulse.local"].id)
            db.add(r1)
            db.flush()

        # 4. Services
        services_data = [
            ("Order Processing Pipeline", "Handles core customer cart checkout and order state machines", "Core Commerce", "production", ServiceHealth.FAILING, policy1.id),
            ("Payment Gateway API", "Stripe and PayPal webhook ingestion and transaction settlement", "Payments Team", "production", ServiceHealth.DEGRADED, policy2.id),
            ("Authentication & OAuth Service", "User sessions, SSO, and JWT verification cluster", "Security Platform", "production", ServiceHealth.HEALTHY, policy1.id),
            ("Notification & SMS Dispatcher", "Twilio and SendGrid high-throughput message router", "Communications", "production", ServiceHealth.HEALTHY, policy3.id),
            ("Customer Inventory Service", "Real-time SKU reservation cache and warehouse synchronization", "Logistics", "staging", ServiceHealth.HEALTHY, policy3.id),
            ("Analytics Ingestion Stream", "Kafka real-time telemetry and user behavior stream", "Data Platform", "production", ServiceHealth.HEALTHY, policy1.id),
        ]
        service_map = {}
        for name, desc, team, env, health, pol_id in services_data:
            svc = db.query(Service).filter(
                Service.organization_id == org.id,
                Service.name == name
            ).first()
            if not svc:
                svc = Service(
                    organization_id=org.id,
                    name=name,
                    slug=name.lower().replace(" ", "-"),
                    description=desc,
                    owner_team=team,
                    environment=env,
                    health_status=health,
                    escalation_policy_id=pol_id,
                    is_active=True,
                    created_at=datetime.now(timezone.utc) - timedelta(days=15),
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(svc)
                db.flush()
            service_map[name] = svc
            print(f"  Service: {name} [{health.value}]")

        now = datetime.now(timezone.utc)

        # 5. Incidents & Alerts & Timelines
        # Only create sample incidents if count is low
        inc_count = db.query(Incident).filter(Incident.organization_id == org.id).count()
        if inc_count < 4:
            # Incident 1: TRIGGERED (Critical) - Order Processing Pipeline
            svc1 = service_map["Order Processing Pipeline"]
            fp1 = generate_alert_fingerprint(svc1.id, "Database connection pool exhaustion on primary replica", "Datadog")
            inc1 = Incident(
                incident_number=1001,
                organization_id=org.id,
                service_id=svc1.id,
                title="Database connection pool exhaustion on primary replica",
                description="Max connections (500/500) reached. API requests timing out with 504 Gateway Timeout during checkout spikes.",
                severity=Severity.CRITICAL,
                status=IncidentStatus.TRIGGERED,
                assigned_responder_id=user_map["responder@opspulse.local"].id,
                escalation_policy_id=policy1.id,
                current_escalation_level=1,
                ack_deadline=now + timedelta(minutes=2),
                alert_count=3,
                fingerprint=fp1,
                created_at=now - timedelta(minutes=6),
                updated_at=now - timedelta(minutes=1)
            )
            db.add(inc1)
            db.flush()

            # Timeline events for Inc 1
            db.add_all([
                IncidentEvent(
                    incident_id=inc1.id,
                    event_type="TRIGGERED",
                    actor_name="Datadog Alert Webhook",
                    message="Incident triggered by alert: ConnectionPoolExhausted: Pool at 100% capacity.",
                    metadata_json={"source": "Datadog", "metric": "pg.connections.pct", "value": 100},
                    created_at=now - timedelta(minutes=6)
                ),
                IncidentEvent(
                    incident_id=inc1.id,
                    event_type="ASSIGNED",
                    actor_name="OpsPulse SLA Engine",
                    message=f"Assigned to Level 1 Responder {user_map['responder@opspulse.local'].full_name}.",
                    created_at=now - timedelta(minutes=6)
                ),
                IncidentEvent(
                    incident_id=inc1.id,
                    event_type="ALERT_GROUPED",
                    actor_name="OpsPulse Deduplication Engine",
                    message="Grouped correlated alert: HTTP 504 elevated error rate on /checkout/pay.",
                    metadata_json={"source": "CloudWatch", "http_status": 504},
                    created_at=now - timedelta(minutes=3)
                )
            ])

            # Alerts for Inc 1
            db.add_all([
                Alert(
                    organization_id=org.id,
                    service_id=svc1.id,
                    incident_id=inc1.id,
                    fingerprint=fp1,
                    title="Database connection pool exhaustion on primary replica",
                    description="Active connections exceeded threshold (500 > 450).",
                    severity=Severity.CRITICAL,
                    source="Datadog",
                    status=AlertStatus.PROCESSED,
                    payload={"host": "pg-primary-01.internal", "region": "us-east-1"},
                    received_at=now - timedelta(minutes=6)
                ),
                Alert(
                    organization_id=org.id,
                    service_id=svc1.id,
                    incident_id=inc1.id,
                    fingerprint=fp1,
                    title="HTTP 504 elevated error rate on /checkout/pay",
                    description="504 error rate exceeded 5% in 3 consecutive 1-minute windows.",
                    severity=Severity.CRITICAL,
                    source="CloudWatch",
                    status=AlertStatus.DEDUPLICATED,
                    payload={"latency_p99_ms": 3200},
                    received_at=now - timedelta(minutes=3)
                ),
                Alert(
                    organization_id=org.id,
                    service_id=svc1.id,
                    incident_id=inc1.id,
                    fingerprint=fp1,
                    title="Database connection timeout queue depth > 50",
                    description="Query wait queue backed up.",
                    severity=Severity.HIGH,
                    source="Prometheus",
                    status=AlertStatus.DEDUPLICATED,
                    payload={"queue_depth": 72},
                    received_at=now - timedelta(minutes=1)
                )
            ])

            # Incident 2: ACKNOWLEDGED (High) - Payment Gateway API
            svc2 = service_map["Payment Gateway API"]
            fp2 = generate_alert_fingerprint(svc2.id, "High Latency Spikes on Stripe Webhook Endpoint", "Prometheus")
            inc2 = Incident(
                incident_number=1002,
                organization_id=org.id,
                service_id=svc2.id,
                title="High Latency Spikes on Stripe Webhook Endpoint",
                description="P99 response time increased from 180ms to 2400ms. Ingestion delay causing delayed payment confirmations.",
                severity=Severity.HIGH,
                status=IncidentStatus.ACKNOWLEDGED,
                assigned_responder_id=user_map["devops@opspulse.local"].id,
                escalation_policy_id=policy2.id,
                current_escalation_level=1,
                acknowledged_at=now - timedelta(minutes=20),
                ack_deadline=None,
                alert_count=2,
                fingerprint=fp2,
                created_at=now - timedelta(minutes=35),
                updated_at=now - timedelta(minutes=5)
            )
            db.add(inc2)
            db.flush()

            db.add_all([
                IncidentEvent(
                    incident_id=inc2.id,
                    event_type="TRIGGERED",
                    actor_name="Prometheus Alertmanager",
                    message="Incident triggered by alert: StripeWebhookLatencyHigh (p99 > 2000ms).",
                    created_at=now - timedelta(minutes=35)
                ),
                IncidentEvent(
                    incident_id=inc2.id,
                    event_type="ACKNOWLEDGED",
                    actor_id=user_map["devops@opspulse.local"].id,
                    actor_name=user_map["devops@opspulse.local"].full_name,
                    message="Incident acknowledged by Marcus Brody. Investigating downstream Redis worker congestion.",
                    created_at=now - timedelta(minutes=20)
                ),
                IncidentEvent(
                    incident_id=inc2.id,
                    event_type="UPDATE_POSTED",
                    actor_id=user_map["devops@opspulse.local"].id,
                    actor_name=user_map["devops@opspulse.local"].full_name,
                    message="Identified slow query in settlement reconciliation. Deploying hotfix config.",
                    created_at=now - timedelta(minutes=5)
                )
            ])

            db.add(IncidentUpdate(
                incident_id=inc2.id,
                user_id=user_map["devops@opspulse.local"].id,
                message="Confirmed Stripe retry requests are queuing safely. Scaling up webhook worker pods from 4 to 12.",
                created_at=now - timedelta(minutes=5)
            ))

            db.add(Alert(
                organization_id=org.id,
                service_id=svc2.id,
                incident_id=inc2.id,
                fingerprint=fp2,
                title="High Latency Spikes on Stripe Webhook Endpoint",
                description="Webhook latency breached threshold (> 2000ms).",
                severity=Severity.HIGH,
                source="Prometheus",
                status=AlertStatus.PROCESSED,
                payload={"endpoint": "/v1/webhooks/stripe", "latency_p99": 2420},
                received_at=now - timedelta(minutes=35)
            ))

            # Incident 3: MITIGATED (Medium) - Authentication Service
            svc3 = service_map["Authentication & OAuth Service"]
            fp3 = generate_alert_fingerprint(svc3.id, "Session Cache Invalidation Delay in Redis Cluster", "Grafana")
            inc3 = Incident(
                incident_number=1003,
                organization_id=org.id,
                service_id=svc3.id,
                title="Session Cache Invalidation Delay in Redis Cluster",
                description="Replica synchronization lag caused stale session read after password changes.",
                severity=Severity.MEDIUM,
                status=IncidentStatus.MITIGATED,
                assigned_responder_id=user_map["lead@opspulse.local"].id,
                escalation_policy_id=policy1.id,
                current_escalation_level=1,
                acknowledged_at=now - timedelta(hours=2),
                mitigated_at=now - timedelta(minutes=30),
                ack_deadline=None,
                alert_count=1,
                fingerprint=fp3,
                created_at=now - timedelta(hours=2, minutes=10),
                updated_at=now - timedelta(minutes=30)
            )
            db.add(inc3)
            db.flush()

            db.add_all([
                IncidentEvent(
                    incident_id=inc3.id,
                    event_type="TRIGGERED",
                    actor_name="Grafana Alertmanager",
                    message="Triggered by alert: RedisReplicaLagCritical.",
                    created_at=now - timedelta(hours=2, minutes=10)
                ),
                IncidentEvent(
                    incident_id=inc3.id,
                    event_type="ACKNOWLEDGED",
                    actor_id=user_map["lead@opspulse.local"].id,
                    actor_name=user_map["lead@opspulse.local"].full_name,
                    message="Acknowledged by Elena Rostova.",
                    created_at=now - timedelta(hours=2)
                ),
                IncidentEvent(
                    incident_id=inc3.id,
                    event_type="MITIGATED",
                    actor_id=user_map["lead@opspulse.local"].id,
                    actor_name=user_map["lead@opspulse.local"].full_name,
                    message="Mitigated by failover to healthy secondary replica node in us-east-1b.",
                    created_at=now - timedelta(minutes=30)
                )
            ])

            db.add(Alert(
                organization_id=org.id,
                service_id=svc3.id,
                incident_id=inc3.id,
                fingerprint=fp3,
                title="Session Cache Invalidation Delay in Redis Cluster",
                description="Replication lag exceeded 500ms on shard 3.",
                severity=Severity.MEDIUM,
                source="Grafana",
                status=AlertStatus.PROCESSED,
                payload={"shard": 3, "lag_ms": 780},
                received_at=now - timedelta(hours=2, minutes=10)
            ))

            # Incident 4: RESOLVED (High) - Order Processing Pipeline
            fp4 = generate_alert_fingerprint(svc1.id, "Kafka Consumer Group Lag Exceeded Threshold on checkout.orders", "Datadog")
            inc4 = Incident(
                incident_number=1004,
                organization_id=org.id,
                service_id=svc1.id,
                title="Kafka Consumer Group Lag Exceeded Threshold on checkout.orders",
                description="Consumer group order-indexer fell 120,000 messages behind partition heads.",
                severity=Severity.HIGH,
                status=IncidentStatus.RESOLVED,
                assigned_responder_id=user_map["sre@opspulse.local"].id,
                escalation_policy_id=policy1.id,
                current_escalation_level=1,
                acknowledged_at=now - timedelta(hours=5),
                mitigated_at=now - timedelta(hours=4),
                resolved_at=now - timedelta(hours=3, minutes=30),
                ack_deadline=None,
                alert_count=2,
                fingerprint=fp4,
                created_at=now - timedelta(hours=5, minutes=15),
                updated_at=now - timedelta(hours=3, minutes=30)
            )
            db.add(inc4)
            db.flush()

            db.add_all([
                IncidentEvent(
                    incident_id=inc4.id,
                    event_type="TRIGGERED",
                    actor_name="Datadog Alert Webhook",
                    message="Incident triggered by alert: KafkaConsumerLagCritical.",
                    created_at=now - timedelta(hours=5, minutes=15)
                ),
                IncidentEvent(
                    incident_id=inc4.id,
                    event_type="ACKNOWLEDGED",
                    actor_id=user_map["sre@opspulse.local"].id,
                    actor_name=user_map["sre@opspulse.local"].full_name,
                    message="Acknowledged by David Kim.",
                    created_at=now - timedelta(hours=5)
                ),
                IncidentEvent(
                    incident_id=inc4.id,
                    event_type="MITIGATED",
                    actor_id=user_map["sre@opspulse.local"].id,
                    actor_name=user_map["sre@opspulse.local"].full_name,
                    message="Scaled consumer worker replicas from 6 to 18.",
                    created_at=now - timedelta(hours=4)
                ),
                IncidentEvent(
                    incident_id=inc4.id,
                    event_type="RESOLVED",
                    actor_id=user_map["sre@opspulse.local"].id,
                    actor_name=user_map["sre@opspulse.local"].full_name,
                    message="Lag drained to 0. Partition processing normalized.",
                    created_at=now - timedelta(hours=3, minutes=30)
                )
            ])

            db.add(Alert(
                organization_id=org.id,
                service_id=svc1.id,
                incident_id=inc4.id,
                fingerprint=fp4,
                title="Kafka Consumer Group Lag Exceeded Threshold on checkout.orders",
                description="Lag > 100k messages.",
                severity=Severity.HIGH,
                source="Datadog",
                status=AlertStatus.PROCESSED,
                payload={"consumer_group": "order-indexer", "total_lag": 128450},
                received_at=now - timedelta(hours=5, minutes=15)
            ))

            # Incident 5: RESOLVED (Medium) - Notification Service
            svc4 = service_map["Notification & SMS Dispatcher"]
            fp5 = generate_alert_fingerprint(svc4.id, "Twilio SMS 5xx Upstream Delivery Failure Spike", "CloudWatch")
            inc5 = Incident(
                incident_number=1005,
                organization_id=org.id,
                service_id=svc4.id,
                title="Twilio SMS 5xx Upstream Delivery Failure Spike",
                description="Transient gateway error on carrier route. Failover to AWS SNS completed.",
                severity=Severity.MEDIUM,
                status=IncidentStatus.RESOLVED,
                assigned_responder_id=user_map["responder@opspulse.local"].id,
                escalation_policy_id=policy3.id,
                current_escalation_level=1,
                acknowledged_at=now - timedelta(days=1),
                resolved_at=now - timedelta(days=1, hours=-1),
                ack_deadline=None,
                alert_count=1,
                fingerprint=fp5,
                created_at=now - timedelta(days=1, minutes=10),
                updated_at=now - timedelta(days=1, hours=-1)
            )
            db.add(inc5)
            db.flush()

            db.add(Alert(
                organization_id=org.id,
                service_id=svc4.id,
                incident_id=inc5.id,
                fingerprint=fp5,
                title="Twilio SMS 5xx Upstream Delivery Failure Spike",
                description="Upstream API error rate > 3%.",
                severity=Severity.MEDIUM,
                source="CloudWatch",
                status=AlertStatus.PROCESSED,
                payload={"carrier": "Twilio-US"},
                received_at=now - timedelta(days=1, minutes=10)
            ))

            # 6. Audit Trail Events
            audit_records = [
                ("ORGANIZATION_INITIALIZED", "ORGANIZATION", org.id, "Acme Cloud Infrastructure workspace provisioned."),
                ("USER_CREATED", "USER", user_map["admin@opspulse.local"].id, "Administrator Alex Mercer provisioned."),
                ("SERVICE_CREATED", "SERVICE", svc1.id, "Order Processing Pipeline registered."),
                ("SERVICE_CREATED", "SERVICE", svc2.id, "Payment Gateway API registered."),
                ("POLICY_CREATED", "POLICY", policy1.id, "Critical Infrastructure SLA policy configured."),
                ("INCIDENT_TRIGGERED", "INCIDENT", inc1.id, "Incident #1001 triggered by Datadog alert."),
                ("INCIDENT_ACKNOWLEDGED", "INCIDENT", inc2.id, "Incident #1002 acknowledged by Marcus Brody."),
                ("INCIDENT_RESOLVED", "INCIDENT", inc4.id, "Incident #1004 resolved by David Kim.")
            ]
            for evt_type, tgt_type, tgt_id, det in audit_records:
                db.add(AuditEvent(
                    organization_id=org.id,
                    actor_id=user_map["admin@opspulse.local"].id,
                    actor_email=user_map["admin@opspulse.local"].email,
                    event_type=evt_type,
                    target_type=tgt_type,
                    target_id=tgt_id,
                    details=det,
                    created_at=now - timedelta(hours=2)
                ))

        db.commit()
        print("[SUCCESS] Database seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error during database seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
