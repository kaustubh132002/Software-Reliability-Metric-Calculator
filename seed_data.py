"""
Initial seed script for Software Reliability Metric Calculator.
Populates sample users and realistic SEQA software system benchmark records.
"""

import models

SAMPLE_RECORDS = [
    {
        'system_name': 'Cloud Payment Gateway',
        'category': 'FinTech / Payment',
        'operating_time': 2400.0,
        'failures': 2,
        'repair_time': 1.5,
        'notes': 'Stripe & PayPal microservice integration with automated circuit breaker failover.'
    },
    {
        'system_name': 'E-Commerce Checkout API',
        'category': 'Web Application',
        'operating_time': 1200.0,
        'failures': 4,
        'repair_time': 8.0,
        'notes': 'High-traffic seasonal load test. Failures caused by redis lock contention.'
    },
    {
        'system_name': 'Hospital Patient Monitor System',
        'category': 'Safety-Critical Medical',
        'operating_time': 5000.0,
        'failures': 1,
        'repair_time': 0.5,
        'notes': 'Real-time ICU vital telemetry. Strict IEC 62304 medical compliance standards.'
    },
    {
        'system_name': 'Telecom Core Signaling Node',
        'category': 'Telecommunications',
        'operating_time': 8760.0,
        'failures': 3,
        'repair_time': 4.5,
        'notes': 'Annual 24/7 SIP protocol routing with redundant active-active node clustering.'
    },
    {
        'system_name': 'IoT Sensor Ingestion Engine',
        'category': 'IoT / Embedded',
        'operating_time': 720.0,
        'failures': 8,
        'repair_time': 16.0,
        'notes': 'MQTT message broker under high packet drop stress condition.'
    },
    {
        'system_name': 'Banking Transaction Core Hub',
        'category': 'Banking & Financial',
        'operating_time': 3600.0,
        'failures': 2,
        'repair_time': 2.0,
        'notes': 'ACID compliant ledger service with automated disaster recovery standby.'
    },
    {
        'system_name': 'Flight Avionics Navigation Module',
        'category': 'Aerospace & Defense',
        'operating_time': 4380.0,
        'failures': 1,
        'repair_time': 0.25,
        'notes': 'DO-178C Level A verified fly-by-wire navigational waypoint guidance engine.'
    },
    {
        'system_name': 'Warehouse Inventory Microservice',
        'category': 'Supply Chain',
        'operating_time': 960.0,
        'failures': 5,
        'repair_time': 12.5,
        'notes': 'PostgreSQL backend with automated nightly batch reconciliation.'
    }
]


def seed_initial_data(db_path=None):
    """
    Seeds database with initial users and benchmark systems if not already present.
    """
    admin_user = models.get_user_by_email('admin@seqa.edu', db_path)
    if not admin_user:
        admin_id = models.create_user(
            name='SEQA Lead Administrator',
            email='admin@seqa.edu',
            password='admin123',
            role='admin',
            db_path=db_path
        )
        print(" [Seed] Created demo admin user: admin@seqa.edu / admin123")
    else:
        admin_id = admin_user['id']

    student_user = models.get_user_by_email('student@seqa.edu', db_path)
    if not student_user:
        student_id = models.create_user(
            name='Alex Chen (QA Engineer)',
            email='student@seqa.edu',
            password='student123',
            role='user',
            db_path=db_path
        )
        print(" [Seed] Created demo student user: student@seqa.edu / student123")
    else:
        student_id = student_user['id']

    # Check if records already exist
    existing_count = models.count_records(db_path=db_path)
    if existing_count == 0:
        print(f" [Seed] Seeding {len(SAMPLE_RECORDS)} realistic software benchmark systems...")
        for item in SAMPLE_RECORDS:
            # Alternate between admin and student user for multi-user demonstration
            target_user = student_id if 'Safety' not in item['category'] and 'Aerospace' not in item['category'] else admin_id
            models.create_record(
                user_id=target_user,
                system_name=item['system_name'],
                operating_time=item['operating_time'],
                failures=item['failures'],
                repair_time=item['repair_time'],
                notes=item['notes'],
                category=item['category'],
                db_path=db_path
            )
        print(" [Seed] Sample data seeding complete.")


if __name__ == '__main__':
    models.init_db()
    seed_initial_data()
    print("Direct seed script execution finished.")
