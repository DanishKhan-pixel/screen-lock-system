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
