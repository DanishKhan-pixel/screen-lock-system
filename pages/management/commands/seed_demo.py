from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from pages.models import Report

MAIN_USERNAME = "danish"

REPORTS = [
    ("Privileged session review", "active", "high", "Danish Khan",
     "After-hours admin access on Karachi finance hosts.",
     "Two admin accounts logged in between 02:00–04:00 PKT with no change ticket. "
     "Firewall logs confirm lateral movement to the core banking VLAN. Pending forensic image."),
    ("Failed unlock cluster", "review", "medium", "Ahmed Malik",
     "Repeated lock-screen failures in Lahore office.",
     "Twelve consecutive PIN failures across four workstations in 8 minutes. "
     "Possible brute-force attempt or shared-credential misuse. CCTV footage requested."),
    ("Vendor laptop inventory", "active", "low", "Fatima Siddiqui",
     "Unencrypted endpoints still in circulation in Islamabad.",
     "Asset scan reveals 14 vendor-issued laptops without BitLocker enabled. "
     "Vendor has been notified; remediation deadline: end of current quarter."),
    ("Quarterly access recert", "closed", "medium", "Usman Ali",
     "Completed for engineering and support in Peshawar.",
     "All 47 accounts reviewed. 3 stale accounts deprovisioned. "
     "Sign-off obtained from department heads. Closed with no residual findings."),
    ("Shared mailbox exposure", "active", "critical", "Danish Khan",
     "External forwarding rule on executive mailbox.",
     "Auto-forward rule to an external Gmail address discovered during O365 audit. "
     "Rule removed immediately. Scope of data exposure under investigation."),
    ("Backup restore drill", "review", "high", "Hassan Raza",
     "RPO missed during regional failover in Multan.",
     "Last successful backup was 26 hours before the drill; RPO target is 4 hours. "
     "Root cause: backup agent silently failed after a firmware update. Fix in progress."),
    ("Contractor offboarding", "closed", "medium", "Ayesha Qureshi",
     "Tokens revoked and devices collected.",
     "All API keys, VPN certificates, and SSO tokens for the three departing contractors "
     "were revoked within the 2-hour SLA. Devices confirmed wiped and returned."),
    ("SSO device posture", "active", "high", "Fatima Siddiqui",
     "Unmanaged browsers passing MFA.",
     "Conditional Access policy gap allows personal Chrome profiles to complete MFA. "
     "A compliant-device policy update is staged for deployment next maintenance window."),
    ("Audit log retention", "review", "low", "Usman Ali",
     "90-day gap on legacy file shares.",
     "Legacy NAS audit logging was disabled after a storage migration 3 months ago. "
     "Logs from that period are irrecoverable. Retention policy updated going forward."),
    ("Branch office Wi-Fi", "closed", "low", "Hassan Raza",
     "Guest VLAN isolated in Faisalabad branch.",
     "Guest Wi-Fi was bridged to the corporate LAN. VLAN isolation applied and "
     "re-tested. No evidence of exploitation. Change request CR-2041 closed."),
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
        for title, status, severity, owner, summary, note in REPORTS:
            _, was_created = Report.objects.update_or_create(
                title=title,
                defaults={
                    "status": status,
                    "severity": severity,
                    "owner": owner,
                    "summary": summary,
                    "note": note,
                },
            )
            created += int(was_created)
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data ready. Main user is {MAIN_USERNAME}. {created} new reports."
            )
        )
