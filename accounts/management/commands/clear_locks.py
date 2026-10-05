"""
Management command to force-unlock all locked sessions in the database.

Useful during development or when a deployment wipes session-dependent state.
Only works with database-backed session engines.
"""
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.services import SESSION_LOCKED


class Command(BaseCommand):
    help = "Clear the screen-lock flag from every active database session."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report how many sessions would be unlocked without modifying them.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()
        sessions = Session.objects.filter(expire_date__gt=now)

        unlocked = 0
        for session_obj in sessions:
            data = session_obj.get_decoded()
            if data.get(SESSION_LOCKED):
                unlocked += 1
                if not dry_run:
                    store = SessionStore(session_key=session_obj.session_key)
                    store[SESSION_LOCKED] = False
                    store.save()

        label = "Would unlock" if dry_run else "Unlocked"
        self.stdout.write(
            self.style.SUCCESS(f"{label} {unlocked} session(s).")
        )
