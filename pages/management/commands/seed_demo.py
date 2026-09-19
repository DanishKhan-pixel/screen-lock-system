from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from pages.models import Report

REPORTS = [
    ("Privileged session review", "active", "high", "Morgan Hale", "After-hours admin access on finance hosts."),
    ("Failed unlock cluster", "review", "medium", "Priya Shah", "Repeated lock-screen failures in EMEA."),
    ("Vendor laptop inventory", "active", "low", "Chris Adeyemi", "Unencrypted endpoints still in circulation."),
    ("Quarterly access recert", "closed", "medium", "Elena Voss", "Completed for engineering and support."),
    ("Shared mailbox exposure", "active", "critical", "Morgan Hale", "External forwarding rule on exec mailbox."),
    ("Backup restore drill", "review", "high", "Jonah Park", "RPO missed during regional failover."),
    ("Contractor offboarding", "closed", "medium", "Priya Shah", "Tokens revoked and devices collected."),
    ("SSO device posture", "active", "high", "Chris Adeyemi", "Unmanaged browsers passing MFA."),
    ("Audit log retention", "review", "low", "Elena Voss", "90-day gap on legacy file shares."),
    ("Branch office Wi-Fi", "closed", "low", "Jonah Park", "Guest VLAN isolated and documented."),
]

PEOPLE = [
    ("morgan", "Morgan", "Hale", "Security Lead", "Protect"),
    ("priya", "Priya", "Shah", "IAM Analyst", "Identity"),
    ("chris", "Chris", "Adeyemi", "Endpoint Engineer", "IT"),
    ("elena", "Elena", "Voss", "Compliance", "Risk"),
]


class Command(BaseCommand):
    help = "Load demo people and incident reports."

    def handle(self, *args, **options):
        alice = User.objects.filter(username="alice").first()
        if alice and not alice.first_name:
            alice.first_name = "Alice"
            alice.email = alice.email or "alice@aegis.local"
            alice.save()
            alice.profile.job_title = alice.profile.job_title or "Operator"
            alice.profile.department = alice.profile.department or "Protect"
            alice.profile.save(update_fields=["job_title", "department"])

        for username, first, last, title, department in PEOPLE:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first, "last_name": last, "email": f"{username}@aegis.local"},
            )
            user.first_name = first
            user.last_name = last
            user.email = f"{username}@aegis.local"
            if not user.has_usable_password():
                user.set_password("password123")
            user.save()
            profile = user.profile
            profile.job_title = title
            profile.department = department
            profile.save(update_fields=["job_title", "department"])

        created = 0
        for title, status, severity, owner, summary in REPORTS:
            _, was_created = Report.objects.get_or_create(
                title=title,
                defaults={
                    "status": status,
                    "severity": severity,
                    "owner": owner,
                    "summary": summary,
                },
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Demo data ready ({created} new reports)."))
