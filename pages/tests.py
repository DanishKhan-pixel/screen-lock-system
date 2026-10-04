from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from pages.models import Report


class WorkspaceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            password="password123",
            first_name="Alice",
            email="alice@aegis.local",
        )
        self.user.profile.job_title = "Operator"
        self.user.profile.department = "Protect"
        self.user.profile.save()
        Report.objects.create(
            title="Privileged session review",
            status=Report.STATUS_ACTIVE,
            severity="high",
            owner="Alice",
            summary="After-hours admin access.",
        )
        Report.objects.create(
            title="Quarterly access recert",
            status=Report.STATUS_CLOSED,
            severity="medium",
            owner="Elena",
        )
        self.client.login(username="alice", password="password123")

    def test_dashboard_shows_workspace_metrics(self):
        response = self.client.get(reverse("pages:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome back, Alice.")
        self.assertContains(response, "Privileged session review")
        self.assertContains(response, "Open incidents")

    def test_reports_filter_by_status(self):
        response = self.client.get(reverse("pages:reports"), {"status": "active", "page": "3"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Privileged session review")
        self.assertNotContains(response, "Quarterly access recert")
        self.assertContains(response, "Filter status:")
        self.assertContains(response, "active")

    def test_users_directory_lists_people(self):
        response = self.client.get(reverse("pages:users"), {"q": "alice"})
        self.assertContains(response, "alice")
        self.assertContains(response, "Operator")

    def test_profile_update_saves_fields(self):
        response = self.client.post(
            reverse("pages:update_profile"),
            {
                "first_name": "Alicia",
                "last_name": "Ng",
                "email": "alicia@aegis.local",
                "job_title": "Lead Operator",
                "department": "Protect",
            },
        )
        self.assertRedirects(response, reverse("pages:profile"))
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alicia")
        self.assertEqual(self.user.profile.job_title, "Lead Operator")


class ReportDetailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bob", password="pass1234")
        self.report = Report.objects.create(
            title="Critical auth bypass",
            status=Report.STATUS_ACTIVE,
            severity="critical",
            owner="Bob",
            summary="JWT secret exposed in logs.",
        )
        self.client.login(username="bob", password="pass1234")

    def test_report_detail_returns_200(self):
        url = reverse("pages:report_detail", args=[self.report.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_report_detail_shows_title(self):
        url = reverse("pages:report_detail", args=[self.report.pk])
        response = self.client.get(url)
        self.assertContains(response, "Critical auth bypass")

    def test_report_detail_404_for_missing_report(self):
        url = reverse("pages:report_detail", args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_report_detail_requires_login(self):
        self.client.logout()
        url = reverse("pages:report_detail", args=[self.report.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class ApiReportsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="carol", password="pass1234")
        Report.objects.create(
            title="Report A", status=Report.STATUS_ACTIVE, severity="low", owner="Carol"
        )
        Report.objects.create(
            title="Report B", status=Report.STATUS_CLOSED, severity="high", owner="Dave"
        )
        self.client.login(username="carol", password="pass1234")

    def test_api_reports_returns_200(self):
        response = self.client.get(reverse("pages:api_reports"))
        self.assertEqual(response.status_code, 200)

    def test_api_reports_content_type_is_json(self):
        response = self.client.get(reverse("pages:api_reports"))
        self.assertEqual(response["Content-Type"], "application/json")

    def test_api_reports_returns_all_reports(self):
        import json
        response = self.client.get(reverse("pages:api_reports"))
        data = json.loads(response.content)
        self.assertIn("reports", data)
        self.assertEqual(len(data["reports"]), 2)

    def test_api_reports_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("pages:api_reports"))
        self.assertEqual(response.status_code, 302)
