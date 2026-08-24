"""
Comprehensive Unit & Integration Test Suite for Software Reliability Metric Calculator (SEQA).
Tests mathematical formulas, database CRUD, user authentication, and report exports.
"""

import unittest
import os
import tempfile
import json
from app import create_app
import models
import seed_data


class TestSoftwareReliabilityCalculator(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app({
            'TESTING': True,
            'DATABASE': self.db_path,
            'SECRET_KEY': 'test-secret-key'
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            models.init_db(self.db_path)
            seed_data.seed_initial_data(self.db_path)

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    # -------------------------------------------------------------------------
    # 1. Mathematical Formula & Boundary Tests
    # -------------------------------------------------------------------------
    def test_metrics_calculation_standard(self):
        """
        Standard Test Case:
        Operating Time = 1000 hrs, Failures = 5, Repair Time = 25 hrs
        Expected:
          MTBF = 1000 / 5 = 200.0 hrs
          MTTR = 25 / 5 = 5.0 hrs
          Failure Rate = 5 / 1000 = 0.005 / hr
          Availability = (1000 / (1000 + 25)) * 100 = 97.561%
        """
        metrics = models.calculate_metrics(1000, 5, 25)
        self.assertEqual(metrics['mtbf'], 200.0)
        self.assertEqual(metrics['mttr'], 5.0)
        self.assertAlmostEqual(metrics['failure_rate'], 0.005, places=5)
        self.assertAlmostEqual(metrics['availability'], 97.561, places=2)

    def test_metrics_calculation_zero_failures(self):
        """
        Zero Failures Case (Flawless operation):
        Operating Time = 500 hrs, Failures = 0, Repair Time = 0 hrs
        Expected:
          MTBF = 500.0 hrs
          MTTR = 0.0 hrs
          Failure Rate = 0.0
          Availability = 100.0%
        """
        metrics = models.calculate_metrics(500, 0, 0)
        self.assertEqual(metrics['mtbf'], 500.0)
        self.assertEqual(metrics['mttr'], 0.0)
        self.assertEqual(metrics['failure_rate'], 0.0)
        self.assertEqual(metrics['availability'], 100.0)

    def test_metrics_calculation_invalid_input(self):
        with self.assertRaises(ValueError):
            models.calculate_metrics(-100, 2, 5)

        with self.assertRaises(ValueError):
            models.calculate_metrics(100, -2, 5)

    # -------------------------------------------------------------------------
    # 2. Database Models & Authentication
    # -------------------------------------------------------------------------
    def test_user_creation_and_verification(self):
        user_id = models.create_user("Test User", "test@example.com", "secret123", role="user", db_path=self.db_path)
        self.assertIsNotNone(user_id)

        # Duplicate email prevention
        duplicate_id = models.create_user("Another User", "test@example.com", "password", db_path=self.db_path)
        self.assertIsNone(duplicate_id)

        # Password verification
        verified = models.verify_user("test@example.com", "secret123", db_path=self.db_path)
        self.assertIsNotNone(verified)
        self.assertEqual(verified['name'], "Test User")

        wrong_pwd = models.verify_user("test@example.com", "wrongpwd", db_path=self.db_path)
        self.assertIsNone(wrong_pwd)

    def test_record_crud_operations(self):
        user = models.get_user_by_email("student@seqa.edu", db_path=self.db_path)
        user_id = user['id']

        # Create
        record_id = models.create_record(
            user_id=user_id,
            system_name="Test CI/CD Engine",
            operating_time=1200,
            failures=3,
            repair_time=6,
            notes="Testing unit CRUD",
            category="Web Application",
            db_path=self.db_path
        )
        self.assertIsNotNone(record_id)

        # Read
        rec = models.get_record_by_id(record_id, db_path=self.db_path)
        self.assertEqual(rec['system_name'], "Test CI/CD Engine")
        self.assertEqual(rec['mtbf'], 400.0)
        self.assertEqual(rec['mttr'], 2.0)

        # Update
        updated = models.update_record(
            record_id=record_id,
            user_id=user_id,
            system_name="Test CI/CD Engine v2",
            operating_time=2400,
            failures=2,
            repair_time=2,
            notes="Updated version",
            category="Web Application",
            db_path=self.db_path
        )
        self.assertTrue(updated)
        rec_updated = models.get_record_by_id(record_id, db_path=self.db_path)
        self.assertEqual(rec_updated['system_name'], "Test CI/CD Engine v2")
        self.assertEqual(rec_updated['mtbf'], 1200.0)

        # Delete
        deleted = models.delete_record(record_id, user_id=user_id, db_path=self.db_path)
        self.assertTrue(deleted)
        self.assertIsNone(models.get_record_by_id(record_id, db_path=self.db_path))

    # -------------------------------------------------------------------------
    # 3. Route & View Integration Tests
    # -------------------------------------------------------------------------
    def test_auth_flow(self):
        # Register new user
        reg_response = self.client.post('/register', data={
            'name': 'Grace Hopper',
            'email': 'grace@navy.mil',
            'password': 'compilerqueen',
            'confirm_password': 'compilerqueen'
        }, follow_redirects=True)
        self.assertEqual(reg_response.status_code, 200)
        self.assertIn(b"Registration successful", reg_response.data)

        # Login
        login_response = self.client.post('/login', data={
            'email': 'grace@navy.mil',
            'password': 'compilerqueen'
        }, follow_redirects=True)
        self.assertEqual(login_response.status_code, 200)
        self.assertIn(b"Grace Hopper", login_response.data)

        # Logout
        logout_response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(logout_response.status_code, 200)
        self.assertIn(b"Sign In", logout_response.data)

    def test_protected_routes(self):
        response = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])

    def test_api_calculate_endpoint(self):
        response = self.client.post('/api/calculate', 
            data=json.dumps({
                'operating_time': 2000,
                'failures': 4,
                'repair_time': 10
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['metrics']['mtbf'], 500.0)
        self.assertEqual(data['metrics']['mttr'], 2.5)

    def test_export_csv_and_pdf(self):
        # Log in as admin
        self.client.post('/login', data={
            'email': 'admin@seqa.edu',
            'password': 'admin123'
        }, follow_redirects=True)

        # Test CSV Export
        csv_resp = self.client.get('/export/csv')
        self.assertEqual(csv_resp.status_code, 200)
        self.assertEqual(csv_resp.content_type, 'text/csv; charset=utf-8')
        self.assertIn(b"System Name", csv_resp.data)
        self.assertIn(b"MTBF", csv_resp.data)

        # Test Summary PDF Export
        pdf_resp = self.client.get('/export/pdf/summary')
        self.assertEqual(pdf_resp.status_code, 200)
        self.assertEqual(pdf_resp.content_type, 'application/pdf')
        # Check PDF magic bytes (%PDF)
        self.assertTrue(pdf_resp.data.startswith(b'%PDF'))

        # Test Single System PDF Export
        single_pdf_resp = self.client.get('/export/pdf/1')
        self.assertEqual(single_pdf_resp.status_code, 200)
        self.assertEqual(single_pdf_resp.content_type, 'application/pdf')
        self.assertTrue(single_pdf_resp.data.startswith(b'%PDF'))


if __name__ == '__main__':
    unittest.main()
