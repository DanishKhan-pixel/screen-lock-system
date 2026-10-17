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


class ApiReportDetailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="clara", password="pass1234")
        self.report = Report.objects.create(
            title="Firewall rule leakage",
            status=Report.STATUS_ACTIVE,
            severity="high",
            owner="Clara",
            summary="Unfiltered port 443 inbound",
            note="Reviewed iptables and resolved rule conflict.",
        )
        self.client.login(username="clara", password="pass1234")

    def test_api_report_detail_returns_200(self):
        url = reverse("pages:api_report_detail", args=[self.report.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_api_report_detail_returns_correct_fields(self):
        import json
        url = reverse("pages:api_report_detail", args=[self.report.pk])
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(data["id"], self.report.pk)
        self.assertEqual(data["title"], "Firewall rule leakage")
        self.assertEqual(data["status"], "active")
        self.assertEqual(data["severity"], "high")
        self.assertEqual(data["owner"], "Clara")
        self.assertEqual(data["summary"], "Unfiltered port 443 inbound")
        self.assertEqual(data["note"], "Reviewed iptables and resolved rule conflict.")
        self.assertIsNotNone(data["created_at"])
        self.assertIsNotNone(data["updated_at"])

    def test_api_report_detail_404_for_missing(self):
        url = reverse("pages:api_report_detail", args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_api_report_detail_requires_login(self):
        self.client.logout()
        url = reverse("pages:api_report_detail", args=[self.report.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class ApiMeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="eve",
            password="pass1234",
            first_name="Eve",
            last_name="Smith",
            email="eve@aegis.local",
        )
        self.user.profile.job_title = "Analyst"
        self.user.profile.department = "SOC"
        self.user.profile.phone = "+92-300-1234567"
        self.user.profile.save()
        self.client.login(username="eve", password="pass1234")

    def test_api_me_returns_200(self):
        response = self.client.get(reverse("pages:api_me"))
        self.assertEqual(response.status_code, 200)

    def test_api_me_contains_username(self):
        import json
        response = self.client.get(reverse("pages:api_me"))
        data = json.loads(response.content)
        self.assertEqual(data["username"], "eve")

    def test_api_me_contains_profile_fields(self):
        import json
        response = self.client.get(reverse("pages:api_me"))
        data = json.loads(response.content)
        self.assertEqual(data["job_title"], "Analyst")
        self.assertEqual(data["department"], "SOC")
        self.assertEqual(data["phone"], "+92-300-1234567")

    def test_api_me_avatar_initials(self):
        import json
        response = self.client.get(reverse("pages:api_me"))
        data = json.loads(response.content)
        self.assertEqual(data["avatar_initials"], "ES")

    def test_api_me_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("pages:api_me"))
        self.assertEqual(response.status_code, 302)


class AegisTagsTests(TestCase):
    def test_severity_icon_critical(self):
        from pages.templatetags.aegis_tags import severity_icon
        self.assertEqual(severity_icon("critical"), "🔴")

    def test_severity_icon_low(self):
        from pages.templatetags.aegis_tags import severity_icon
        self.assertEqual(severity_icon("low"), "🔵")

    def test_severity_icon_unknown(self):
        from pages.templatetags.aegis_tags import severity_icon
        self.assertEqual(severity_icon("unknown"), "⚪")

    def test_status_label_active(self):
        from pages.templatetags.aegis_tags import status_label
        self.assertIn("Active", status_label("active"))

    def test_status_label_closed(self):
        from pages.templatetags.aegis_tags import status_label
        self.assertIn("Closed", status_label("closed"))

    def test_initials_filter_with_profile(self):
        from pages.templatetags.aegis_tags import initials
        user = User.objects.create_user(
            username="frank", first_name="Frank", last_name="Green"
        )
        self.assertEqual(initials(user), "FG")

    def test_initials_filter_fallback(self):
        from pages.templatetags.aegis_tags import initials
        user = User.objects.create_user(username="xy", first_name="", last_name="")
        self.assertEqual(initials(user), "XY")


class CreateReportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="grace", password="pass1234")
        self.client.login(username="grace", password="pass1234")

    def test_create_report_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("pages:create_report"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_create_report_get_renders_form(self):
        response = self.client.get(reverse("pages:create_report"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New Incident")
        self.assertContains(response, 'name="title"')
        self.assertContains(response, 'name="status"')
        self.assertContains(response, 'name="severity"')

    def test_create_report_post_valid_creates_and_redirects(self):
        data = {
            "title": "Unauthorized SSH attempt",
            "status": Report.STATUS_ACTIVE,
            "severity": "high",
            "owner": "Grace",
            "summary": "Brute-force detected on port 22",
            "note": "IP blocked via fail2ban.",
        }
        response = self.client.post(reverse("pages:create_report"), data)
        report = Report.objects.filter(title="Unauthorized SSH attempt").first()
        self.assertIsNotNone(report)
        self.assertEqual(report.owner, "Grace")
        self.assertEqual(report.severity, "high")
        self.assertRedirects(response, report.get_absolute_url())

    def test_create_report_post_invalid_shows_errors(self):
        data = {
            "title": "",  # required
            "status": Report.STATUS_ACTIVE,
            "severity": "high",
        }
        response = self.client.post(reverse("pages:create_report"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "title", "This field is required.")
        self.assertEqual(Report.objects.filter(status=Report.STATUS_ACTIVE).count(), 0)


class ReportFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="henry", password="pass1234")
        self.r_crit = Report.objects.create(
            title="Database data dump",
            status=Report.STATUS_ACTIVE,
            severity="critical",
            owner="Henry",
        )
        self.r_med = Report.objects.create(
            title="TLS cert expiration warning",
            status=Report.STATUS_REVIEW,
            severity="medium",
            owner="Alice",
        )
        self.r_low = Report.objects.create(
            title="Minor dependency bump",
            status=Report.STATUS_CLOSED,
            severity="low",
            owner="Bob",
        )
        self.client.login(username="henry", password="pass1234")

    def test_filter_by_status(self):
        response = self.client.get(reverse("pages:reports"), {"status": "active"})
        self.assertEqual(response.status_code, 200)
        reports = list(response.context["page_obj"])
        self.assertIn(self.r_crit, reports)
        self.assertNotIn(self.r_med, reports)
        self.assertNotIn(self.r_low, reports)

    def test_filter_by_severity(self):
        response = self.client.get(reverse("pages:reports"), {"severity": "critical"})
        self.assertEqual(response.status_code, 200)
        reports = list(response.context["page_obj"])
        self.assertIn(self.r_crit, reports)
        self.assertNotIn(self.r_med, reports)

    def test_filter_by_search_query(self):
        response = self.client.get(reverse("pages:reports"), {"q": "expiration"})
        self.assertEqual(response.status_code, 200)
        reports = list(response.context["page_obj"])
        self.assertIn(self.r_med, reports)
        self.assertNotIn(self.r_crit, reports)

    def test_filter_invalid_status_ignored(self):
        response = self.client.get(reverse("pages:reports"), {"status": "invalid_status"})
        self.assertEqual(response.status_code, 200)
        reports = list(response.context["page_obj"])
        self.assertEqual(len(reports), 3)

    def test_filter_invalid_severity_ignored(self):
        response = self.client.get(reverse("pages:reports"), {"severity": "invalid_severity"})
        self.assertEqual(response.status_code, 200)
        reports = list(response.context["page_obj"])
        self.assertEqual(len(reports), 3)
