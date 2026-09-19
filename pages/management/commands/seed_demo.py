from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from pages.models import Report

MAIN_USERNAME = "danish"

REPORTS = [
    ("Privileged session review", "active", "high", "Danish Khan", "After-hours admin access on Karachi finance hosts."),
    ("Failed unlock cluster", "review", "medium", "Ahmed Malik", "Repeated lock-screen failures in Lahore office."),
    ("Vendor laptop inventory", "active", "low", "Fatima Siddiqui", "Unencrypted endpoints still in circulation in Islamabad."),
    ("Quarterly access recert", "closed", "medium", "Usman Ali", "Completed for engineering and support in Peshawar."),
    ("Shared mailbox exposure", "active", "critical", "Danish Khan", "External forwarding rule on executive mailbox."),
    ("Backup restore drill", "review", "high", "Hassan Raza", "RPO missed during regional failover in Multan."),
    ("Contractor offboarding", "closed", "medium", "Ayesha Qureshi", "Tokens revoked and devices collected."),
    ("SSO device posture", "active", "high", "Fatima Siddiqui", "Unmanaged browsers passing MFA."),
    ("Audit log retention", "review", "low", "Usman Ali", "90-day gap on legacy file shares."),
    ("Branch office Wi-Fi", "closed", "low", "Hassan Raza", "Guest VLAN isolated in Faisalabad branch."),
]

PEOPLE = [
    ("danish", "Danish", "Khan", "Security Lead", "Protect", True),
    ("ahmed", "Ahmed", "Malik", "IAM Analyst", "Identity", False),
    ("fatima", "Fatima", "Siddiqui", "Endpoint Engineer", "IT", False),
    ("usman", "Usman", "Ali", "Compliance", "Risk", False),
    ("ayesha", "Ayesha", "Qureshi", "SOC Analyst", "Protect", False),
    ("hassan", "Hassan", "Raza", "Network Engineer", "IT", False),
]

REMOVE_USERNAMES = ("alice", "morgan", "priya", "chris", "elena")


class Command(BaseCommand):
    help = "Load Pakistani demo people and incident reports."

    def handle(self, *args, **options):
        User.objects.filter(username__in=REMOVE_USERNAMES).delete()

        for username, first, last, title, department, is_main in PEOPLE:
            user, _ = User.objects.get_or_create(username=username)
            user.first_name = first
            user.last_name = last
            user.email = f"{username}@aegis.local"
            user.set_password("password123")
            user.save()
            profile = user.profile
            profile.job_title = title
            profile.department = department
            if is_main:
                profile.set_pin("123456")
            profile.save()

        created = 0
        for title, status, severity, owner, summary in REPORTS:
            _, was_created = Report.objects.update_or_create(
                title=title,
                defaults={
                    "status": status,
                    "severity": severity,
                    "owner": owner,
                    "summary": summary,
                },
            )
            created += int(was_created)
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data ready. Main user is {MAIN_USERNAME}. {created} new reports."
            )
        )
