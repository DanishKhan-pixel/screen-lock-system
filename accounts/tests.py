from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.forms import PIN_FORMAT_ERROR, ScreenLockForm
from accounts.middleware import _has_asset_prefix
from accounts.services import (
    SESSION_FAILED_ATTEMPTS,
    SESSION_LOCKED,
    SESSION_RETURN_URL,
)


class ScreenLockTestCase(TestCase):
    PIN = "123456"
    PASSWORD = "password123"

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password=self.PASSWORD)
        self.user.profile.set_pin(self.PIN)
        self.user.profile.save()
        self.client.login(username="alice", password=self.PASSWORD)

    def lock(self, next_url="/reports/?status=active&page=3"):
        return self.client.post(reverse("accounts:activate_lock"), {"next": next_url})

    def unlock(self, pin, **kwargs):
        return self.client.post(reverse("accounts:lock_screen"), {"pin": pin}, **kwargs)

    def is_authenticated(self):
        return "_auth_user_id" in self.client.session


class UnauthenticatedAccessTests(ScreenLockTestCase):
    def setUp(self):
        super().setUp()
        self.client.logout()

    def test_unauthenticated_user_cannot_access_lock_screen(self):
        response = self.client.get(reverse("accounts:lock_screen"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_unauthenticated_user_cannot_unlock(self):
        response = self.unlock(self.PIN)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_unauthenticated_user_cannot_activate_lock(self):
        response = self.lock()
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)


class LockingTests(ScreenLockTestCase):
    def test_authenticated_user_can_lock_from_dashboard(self):
        response = self.lock(reverse("pages:dashboard"))
        self.assertRedirects(response, reverse("accounts:lock_screen"))
        self.assertTrue(self.client.session[SESSION_LOCKED])

    def test_can_lock_from_each_authenticated_page(self):
        pages = [
            reverse("pages:dashboard"),
            reverse("pages:reports") + "?status=active&page=3",
            reverse("pages:users"),
            reverse("pages:profile"),
            reverse("pages:settings"),
        ]
        for url in pages:
            response = self.lock(url)
            self.assertRedirects(response, reverse("accounts:lock_screen"))
            self.assertTrue(self.client.session[SESSION_LOCKED])
            self.assertTrue(self.is_authenticated())
            self.unlock(self.PIN)

    def test_lock_state_is_stored_server_side(self):
        self.lock()
        self.assertTrue(self.client.session.get(SESSION_LOCKED))
        self.assertEqual(
            self.client.session.get(SESSION_RETURN_URL),
            "/reports/?status=active&page=3",
        )

    def test_lock_keeps_authenticated_session(self):
        self.lock()
        self.assertTrue(self.is_authenticated())
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_original_url_is_preserved(self):
        self.lock("/reports/?status=active&page=3")
        self.assertEqual(
            self.client.session[SESSION_RETURN_URL],
            "/reports/?status=active&page=3",
        )

    def test_lock_does_not_require_get(self):
        response = self.client.get(reverse("accounts:activate_lock"))
        self.assertEqual(response.status_code, 405)


class PinValidationTests(TestCase):
    def assert_invalid(self, pin):
        form = ScreenLockForm(data={"pin": pin})
        self.assertFalse(form.is_valid())
        self.assertIn("pin", form.errors)

    def test_exactly_six_digits_are_valid(self):
        form = ScreenLockForm(data={"pin": "123456"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["pin"], "123456")

    def test_five_digits_rejected(self):
        self.assert_invalid("12345")

    def test_seven_digits_rejected(self):
        self.assert_invalid("1234567")

    def test_alphabetic_input_rejected(self):
        self.assert_invalid("abcdef")

    def test_alphanumeric_input_rejected(self):
        self.assert_invalid("12a456")

    def test_special_characters_rejected(self):
        self.assert_invalid("12@456")

    def test_empty_pin_rejected(self):
        self.assert_invalid("")

    def test_validation_error_message_is_generic(self):
        form = ScreenLockForm(data={"pin": "12345"})
        form.is_valid()
        self.assertIn(PIN_FORMAT_ERROR, form.errors["pin"])


class SuccessfulUnlockTests(ScreenLockTestCase):
    def test_correct_pin_unlocks(self):
        self.lock()
        response = self.unlock(self.PIN)
        self.assertFalse(self.client.session.get(SESSION_LOCKED, False))
        self.assertRedirects(
            response,
            "/reports/?status=active&page=3",
            fetch_redirect_response=True,
        )

    def test_session_remains_authenticated_after_unlock(self):
        self.lock()
        self.unlock(self.PIN)
        self.assertTrue(self.is_authenticated())
        response = self.client.get(reverse("pages:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_failed_counter_resets_on_success(self):
        self.lock()
        self.unlock("000000")
        self.unlock("111111")
        self.unlock(self.PIN)
        self.assertEqual(self.client.session.get(SESSION_FAILED_ATTEMPTS), 0)

    def test_query_parameters_are_preserved(self):
        self.lock("/reports/?status=active&page=3")
        response = self.unlock(self.PIN)
        self.assertEqual(response.url, "/reports/?status=active&page=3")

    def test_open_redirect_is_rejected(self):
        self.lock("https://evil.example/phish")
        response = self.unlock(self.PIN)
        self.assertRedirects(response, reverse("pages:dashboard"))

    def test_protocol_relative_redirect_is_rejected(self):
        self.lock("//evil.example/phish")
        response = self.unlock(self.PIN)
        self.assertRedirects(response, reverse("pages:dashboard"))


class FailedAttemptTests(ScreenLockTestCase):
    def test_first_incorrect_pin_stays_locked(self):
        self.lock()
        response = self.unlock("000000")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "incorrect")
        self.assertTrue(self.client.session[SESSION_LOCKED])
        self.assertTrue(self.is_authenticated())
        self.assertEqual(self.client.session[SESSION_FAILED_ATTEMPTS], 1)

    def test_second_incorrect_pin_stays_locked(self):
        self.lock()
        self.unlock("000000")
        response = self.unlock("111111")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.client.session[SESSION_LOCKED])
        self.assertTrue(self.is_authenticated())
        self.assertEqual(self.client.session[SESSION_FAILED_ATTEMPTS], 2)

    def test_third_incorrect_pin_logs_out(self):
        self.lock()
        self.unlock("000000")
        self.unlock("111111")
        response = self.unlock("222222")
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertFalse(self.is_authenticated())
        self.assertIsNone(self.client.session.get(SESSION_LOCKED))

    def test_third_failure_requires_standard_login(self):
        self.lock()
        self.unlock("000000")
        self.unlock("111111")
        self.unlock("222222")
        response = self.client.get(reverse("pages:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_invalid_format_does_not_count_as_failed_attempt(self):
        self.lock()
        self.unlock("12345")
        self.assertEqual(self.client.session.get(SESSION_FAILED_ATTEMPTS), 0)
        self.assertTrue(self.client.session[SESSION_LOCKED])

    def test_missing_pin_is_treated_as_incorrect_without_leak(self):
        self.user.profile.pin_hash = ""
        self.user.profile.save()
        self.lock()
        response = self.unlock(self.PIN)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "incorrect")
        self.assertNotContains(response, "not configured")
        self.assertTrue(self.client.session[SESSION_LOCKED])


class CounterResetTests(ScreenLockTestCase):
    def test_correct_pin_after_two_failures_unlocks_and_resets(self):
        self.lock()
        self.unlock("000000")
        self.unlock("111111")
        self.unlock(self.PIN)
        self.assertFalse(self.client.session.get(SESSION_LOCKED, False))
        self.assertEqual(self.client.session.get(SESSION_FAILED_ATTEMPTS), 0)
        self.assertTrue(self.is_authenticated())

    def test_next_lock_starts_failed_attempts_at_zero(self):
        self.lock()
        self.unlock("000000")
        self.unlock("111111")
        self.unlock(self.PIN)
        self.lock()
        self.unlock("000000")
        self.assertTrue(self.is_authenticated())
        self.assertTrue(self.client.session[SESSION_LOCKED])
        self.assertEqual(self.client.session[SESSION_FAILED_ATTEMPTS], 1)


class BypassProtectionTests(ScreenLockTestCase):
    def test_refresh_lock_screen_stays_locked(self):
        self.lock()
        first = self.client.get(reverse("accounts:lock_screen"))
        second = self.client.get(reverse("accounts:lock_screen"))
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertContains(second, "Application locked")
        self.assertTrue(self.client.session[SESSION_LOCKED])
        self.assertTrue(self.is_authenticated())

    def test_get_original_url_while_locked_redirects(self):
        self.lock("/reports/?status=active&page=3")
        response = self.client.get("/reports/?status=active&page=3")
        self.assertRedirects(response, reverse("accounts:lock_screen"))

    def test_direct_dashboard_url_while_locked_redirects(self):
        self.lock()
        response = self.client.get(reverse("pages:dashboard"))
        self.assertRedirects(response, reverse("accounts:lock_screen"))

    def test_different_authenticated_page_while_locked_redirects(self):
        self.lock()
        response = self.client.get(reverse("pages:users"))
        self.assertRedirects(response, reverse("accounts:lock_screen"))

    def test_settings_and_profile_while_locked_redirect(self):
        self.lock()
        for name in ("pages:settings", "pages:profile"):
            response = self.client.get(reverse(name))
            self.assertRedirects(response, reverse("accounts:lock_screen"))

    def test_admin_while_locked_redirects(self):
        self.lock()
        response = self.client.get("/admin/")
        self.assertRedirects(
            response,
            reverse("accounts:lock_screen"),
            fetch_redirect_response=False,
        )

    def test_post_to_protected_endpoint_while_locked_redirects(self):
        self.lock()
        response = self.client.post(reverse("pages:update_profile"))
        self.assertRedirects(
            response,
            reverse("accounts:lock_screen"),
            fetch_redirect_response=False,
        )

    def test_api_request_while_locked_returns_403(self):
        self.lock()
        response = self.client.get(reverse("pages:api_status"))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Screen is locked.")

    def test_ajax_request_while_locked_returns_403(self):
        self.lock()
        response = self.client.get(
            reverse("pages:dashboard"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 403)

    def test_lock_screen_is_allowed_while_locked(self):
        self.lock()
        response = self.client.get(reverse("accounts:lock_screen"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "id_pin")
        self.assertContains(response, "Unlock")

    def test_unlock_route_is_allowed_while_locked(self):
        self.lock()
        response = self.unlock(self.PIN)
        self.assertEqual(response.status_code, 302)

    def test_logout_is_allowed_while_locked(self):
        self.lock()
        response = self.client.post(reverse("accounts:logout"))
        self.assertFalse(self.is_authenticated())
        self.assertRedirects(response, reverse("accounts:login"))

    def test_lock_screen_does_not_redirect_to_itself(self):
        self.lock()
        response = self.client.get(reverse("accounts:lock_screen"))
        self.assertEqual(response.status_code, 200)

    def test_unlocked_lock_screen_does_not_loop(self):
        response = self.client.get(reverse("accounts:lock_screen"))
        self.assertRedirects(response, reverse("pages:dashboard"))


class SessionIsolationTests(ScreenLockTestCase):
    def test_lock_does_not_affect_another_user_session(self):
        other = User.objects.create_user(username="bob", password=self.PASSWORD)
        other.profile.set_pin("654321")
        other.profile.save()
        other_client = Client()
        other_client.login(username="bob", password=self.PASSWORD)

        self.lock()
        response = other_client.get(reverse("pages:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(other_client.session.get(SESSION_LOCKED, False))

    def test_pin_is_hashed_in_storage(self):
        self.user.profile.refresh_from_db()
        self.assertNotEqual(self.user.profile.pin_hash, self.PIN)
        self.assertTrue(self.user.profile.check_pin(self.PIN))

    def test_pin_and_hash_are_not_in_lock_screen(self):
        self.lock()
        response = self.client.get(reverse("accounts:lock_screen"))
        self.assertNotContains(response, self.PIN)
        self.assertNotContains(response, self.user.profile.pin_hash)
        self.assertNotContains(response, SESSION_FAILED_ATTEMPTS)

    def test_unlock_without_lock_does_not_check_out(self):
        response = self.unlock(self.PIN)
        self.assertRedirects(response, reverse("pages:dashboard"))
        self.assertTrue(self.is_authenticated())


class PinSetupTests(ScreenLockTestCase):
    def test_user_can_set_pin_from_settings(self):
        self.user.profile.pin_hash = ""
        self.user.profile.save()
        response = self.client.post(
            reverse("pages:settings"),
            {"pin": "654321", "confirm_pin": "654321"},
        )
        self.assertRedirects(response, reverse("pages:settings"))
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.check_pin("654321"))

    def test_changing_pin_requires_current_pin(self):
        response = self.client.post(
            reverse("pages:settings"),
            {"pin": "654321", "confirm_pin": "654321"},
        )
        self.assertEqual(response.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.check_pin(self.PIN))


class AssetPrefixTests(TestCase):
    def test_root_media_url_is_not_treated_as_prefix(self):
        self.assertFalse(_has_asset_prefix("/dashboard/", "/"))
        self.assertFalse(_has_asset_prefix("/dashboard/", ""))
        self.assertTrue(_has_asset_prefix("/static/app.css", "static/"))
        self.assertTrue(_has_asset_prefix("/media/file.png", "/media/"))


class CsrfTests(ScreenLockTestCase):
    def test_unlock_requires_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username="alice", password=self.PASSWORD)
        session = csrf_client.session
        session[SESSION_LOCKED] = True
        session[SESSION_RETURN_URL] = reverse("pages:dashboard")
        session.save()
        response = csrf_client.post(reverse("accounts:lock_screen"), {"pin": self.PIN})
        self.assertEqual(response.status_code, 403)


class LockTimestampTests(ScreenLockTestCase):
    """Tests verifying that a UTC timestamp is stored on lock and cleared on unlock."""

    def test_lock_stores_timestamp(self):
        self.lock()
        ts = self.client.session.get("screen_lock_timestamp")
        self.assertIsNotNone(ts, "Expected a timestamp to be stored in the session on lock.")

    def test_unlock_clears_timestamp(self):
        self.lock()
        self.unlock(self.PIN)
        ts = self.client.session.get("screen_lock_timestamp")
        self.assertIsNone(ts, "Expected the timestamp to be cleared after unlock.")

    def test_timestamp_is_iso_format(self):
        import datetime
        self.lock()
        ts = self.client.session.get("screen_lock_timestamp")
        try:
            dt = datetime.datetime.fromisoformat(ts)
        except (TypeError, ValueError):
            self.fail(f"Timestamp {ts!r} is not a valid ISO-8601 string.")
        self.assertIsNotNone(dt.tzinfo, "Timestamp should be timezone-aware.")


class UserProfilePropertyTests(ScreenLockTestCase):
    """Tests for avatar_initials and pin_configured model properties."""

    def test_pin_configured_true_when_pin_set(self):
        self.assertTrue(self.user.profile.pin_configured)

    def test_pin_configured_false_when_no_pin(self):
        profile = self.user.profile
        profile.pin_hash = ""
        profile.save()
        self.assertFalse(profile.pin_configured)

    def test_avatar_initials_from_full_name(self):
        self.user.first_name = "Jane"
        self.user.last_name = "Doe"
        self.user.save()
        self.assertEqual(self.user.profile.avatar_initials, "JD")

    def test_avatar_initials_fallback_to_username(self):
        self.user.first_name = ""
        self.user.last_name = ""
        self.user.save()
        self.assertEqual(self.user.profile.avatar_initials, "AL")

    def test_avatar_initials_max_two_chars(self):
        self.user.first_name = "Alice"
        self.user.last_name = "Bob"
        self.user.save()
        self.assertLessEqual(len(self.user.profile.avatar_initials), 2)


class ClearPinViewTests(ScreenLockTestCase):
    """Tests for the clear_pin view endpoint and model integration."""

    def test_unauthenticated_clear_pin_redirects_to_login(self):
        self.client.logout()
        response = self.client.post(reverse("accounts:clear_pin"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_get_method_not_allowed(self):
        response = self.client.get(reverse("accounts:clear_pin"))
        self.assertEqual(response.status_code, 405)

    def test_post_clears_pin_and_redirects_to_settings(self):
        self.assertTrue(self.user.profile.pin_configured)
        response = self.client.post(reverse("accounts:clear_pin"))
        self.assertRedirects(response, reverse("pages:settings"))

        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.pin_configured)
        self.assertEqual(self.user.profile.pin_hash, "")

    def test_model_clear_pin_directly(self):
        profile = self.user.profile
        self.assertTrue(profile.pin_configured)
        profile.clear_pin()
        profile.save()
        profile.refresh_from_db()
        self.assertFalse(profile.pin_configured)
        self.assertEqual(profile.pin_hash, "")


class AutoLockTimeoutTests(ScreenLockTestCase):
    """Tests for inactivity timeout auto-locking behavior."""

    def test_activity_recorded_on_request(self):
        from accounts.services import SESSION_LAST_ACTIVITY
        response = self.client.get(reverse("pages:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(SESSION_LAST_ACTIVITY, self.client.session)

    @override_settings(SCREEN_LOCK_TIMEOUT_SECONDS=300)
    def test_auto_lock_triggers_after_timeout(self):
        import datetime
        from accounts.services import SESSION_LAST_ACTIVITY, SESSION_LOCKED

        # Establish session activity in past (> 300 seconds ago)
        past_time = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(seconds=400)
        session = self.client.session
        session[SESSION_LAST_ACTIVITY] = past_time.isoformat()
        session.save()

        # Next request should trigger auto-lock redirect
        response = self.client.get(reverse("pages:dashboard"))
        self.assertRedirects(response, reverse("accounts:lock_screen"))
        self.assertTrue(self.client.session.get(SESSION_LOCKED))

    @override_settings(SCREEN_LOCK_TIMEOUT_SECONDS=300)
    def test_no_auto_lock_before_timeout(self):
        import datetime
        from accounts.services import SESSION_LAST_ACTIVITY, SESSION_LOCKED

        recent_time = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(seconds=100)
        session = self.client.session
        session[SESSION_LAST_ACTIVITY] = recent_time.isoformat()
        session.save()

        response = self.client.get(reverse("pages:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.session.get(SESSION_LOCKED, False))

    @override_settings(SCREEN_LOCK_TIMEOUT_SECONDS=300)
    def test_no_auto_lock_if_user_has_no_pin(self):
        import datetime
        from accounts.services import SESSION_LAST_ACTIVITY, SESSION_LOCKED

        self.user.profile.clear_pin()
        self.user.profile.save()

        past_time = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(seconds=500)
        session = self.client.session
        session[SESSION_LAST_ACTIVITY] = past_time.isoformat()
        session.save()

        response = self.client.get(reverse("pages:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.session.get(SESSION_LOCKED, False))
