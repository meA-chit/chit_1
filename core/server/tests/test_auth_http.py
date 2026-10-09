"""Accounts and sign-in over real HTTP (ADR-0014): invitation, Terms, email codes, sessions, households, owner rules.

Runs the hub with sign-in on, through the restricted application role (so row-level security is in force), with a movable
clock and a mailbox that records the codes. Postgres only.
"""
from datetime import datetime, timedelta, timezone
from http.client import HTTPConnection
import json
import tempfile
from pathlib import Path
import threading
import unittest

from chit_store import EncryptedHouseholdStore
from chit_store.testing import POSTGRES

if POSTGRES:
    import os

    from chit_server.app import make_server
    from chit_server.auth_gate import AuthGate, AuthSettings
    from chit_store import mailer
    from chit_store.accounts import Accounts

T0 = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)
TERMS = "2026-10-beta-1"


class Client:
    """A browser stand-in: keeps the session cookie."""

    def __init__(self, address):
        self.address, self.cookie = address, None

    def call(self, method, path, body=None, headers=None):
        connection = HTTPConnection(self.address[0], self.address[1], timeout=20)
        sent = dict(headers or {})
        if self.cookie:
            sent["Cookie"] = "chit_session=" + self.cookie
        payload = None
        if body is not None:
            payload = json.dumps(body)
            sent["Content-Type"] = "application/json"
        connection.request(method, path, payload, sent)
        response = connection.getresponse()
        raw = response.read()
        cookie = response.getheader("Set-Cookie")
        if cookie:
            name_value = cookie.split(";")[0]
            value = name_value.split("=", 1)[1]
            self.cookie = value or None
        self.last_cookie_header = cookie
        connection.close()
        return response.status, (json.loads(raw) if raw else None)

    def get(self, path, **kw):
        return self.call("GET", path, **kw)

    def post(self, path, body=None, **kw):
        return self.call("POST", path, {} if body is None else body, **kw)


@unittest.skipUnless(POSTGRES, "accounts need the Postgres backend")
class AuthHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.owner_store = EncryptedHouseholdStore(Path(cls.temp.name) / "auth.db")
        cls.app_store = cls.owner_store.with_role(os.environ["CHIT_PG_TEST_APP_URL"])
        cls.mail = mailer.ConsoleMailer()
        cls.now = T0
        clock = lambda: cls.now
        cls.operator = Accounts(cls.owner_store, cls.mail, TERMS, clock=clock)           # the operator tool: owner role
        cls.accounts = Accounts(cls.app_store, cls.mail, TERMS, clock=clock)             # what the server uses
        cls.operator.async_mail = cls.accounts.async_mail = False
        cls.gate = AuthGate(cls.accounts, AuthSettings(cookie_secure=False))
        cls.server = make_server(cls.app_store, "127.0.0.1", 0, auth=cls.gate)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.address = cls.server.server_address

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.temp.cleanup()

    def setUp(self):
        type(self).now = T0
        type(self).accounts.terms_version = type(self).operator.terms_version = TERMS
        self.mail.outbox.clear()
        with self.owner_store._connection() as c:
            c.execute("DELETE FROM auth_events")
        self.created = 0

    # ------------------------------------------------------------------ fixtures
    def client(self):
        return Client(self.address)

    def household(self, name, adults=("Owner",)):
        """A household with these adults and a child. Returns (household_id, [member ids of the adults])."""
        made = self.owner_store.create_household(name, adults[0])
        ids = [made["owner_member_id"]]
        for extra in adults[1:]:
            ids.append(self.owner_store.add_member(made["household_id"], "adult", extra))
        self.owner_store.add_member(made["household_id"], "child", "Kid of " + name)
        return made["household_id"], ids

    def enrol(self, household, member, email, role="owner", client=None):
        """Walk the whole invitation: link + code, Terms, email code. Returns the signed-in client."""
        client = client or self.client()
        pairing = self.operator.issue_pairing(household, member, role, "operator")
        status, body = client.post("/api/auth/pairing/redeem", {"link": pairing["link"], "code": pairing["code"]})
        self.assertEqual(status, 200, body)
        enrolment = body["enrolment"]
        self.assertEqual(client.post("/api/auth/enrol/email", {"enrolment": enrolment, "email": email, "accept_terms": True, "terms_version": TERMS})[0], 202)
        status, body = client.post("/api/auth/enrol/verify", {"enrolment": enrolment, "email": email, "code": self.mail.last_code(email, "enrol")})
        self.assertEqual(status, 200, body)
        return client

    def login(self, email, client=None):
        client = client or self.client()
        self.assertEqual(client.post("/api/auth/login/start", {"email": email})[0], 202)
        status, body = client.post("/api/auth/login/verify", {"email": email, "code": self.mail.last_code(email, "login")})
        self.assertEqual(status, 200, body)
        return client

    def advance(self, **delta):
        type(self).now = type(self).now + timedelta(**delta)

    def unique(self, label):
        self.created += 1
        return "%s%d-%s@example.org" % (label, self.created, id(self) % 10000)

    # ------------------------------------------------------------------ enrolment
    def test_a_person_enrols_with_invitation_terms_and_email_and_is_then_signed_in(self):
        hid, (owner,) = self.household("Fam Enrol")
        email = self.unique("nina")
        client = self.enrol(hid, owner, email)
        status, me = client.get("/api/auth/me")
        self.assertEqual((status, me["email"], me["role"], me["household_id"]), (200, email, "owner", hid))
        self.assertTrue(me["terms"]["accepted"])
        status, summary = client.get("/api/household/summary")
        self.assertEqual(status, 200)
        self.assertIn("Fam Enrol", json.dumps(summary))

    def test_without_a_session_nothing_but_the_public_routes_answer(self):
        anon = self.client()
        self.assertEqual(anon.get("/api/health")[0], 200)
        self.assertEqual(anon.get("/api/auth/terms")[1]["version"], TERMS)
        for path in ("/api/household/summary", "/api/shell?surface=web", "/api/planner/chores/today", "/api/kids/phone/settings", "/api/auth/me"):
            self.assertEqual(anon.get(path)[0], 401, path)
        junk = self.client()
        junk.cookie = "not-a-real-session"
        self.assertEqual(junk.get("/api/household/summary")[0], 401)

    def test_the_invitation_works_once_and_only_with_its_code(self):
        hid, (owner,) = self.household("Fam Once")
        pairing = self.operator.issue_pairing(hid, owner, "owner", "operator")
        self.assertEqual(self.client().post("/api/auth/pairing/redeem", {"link": "x" * 32, "code": pairing["code"]})[0], 410)     # unknown link
        for left in (4, 3, 2, 1):
            status, body = self.client().post("/api/auth/pairing/redeem", {"link": pairing["link"], "code": "000000"})
            self.assertEqual((status, body["error"], body["attempts_left"]), (403, "wrong_code", left))
        status, body = self.client().post("/api/auth/pairing/redeem", {"link": pairing["link"], "code": "000000"})
        self.assertEqual((status, body["error"]), (423, "pairing_locked"))
        self.assertEqual(self.client().post("/api/auth/pairing/redeem", {"link": pairing["link"], "code": pairing["code"]})[0], 410)   # locked for good

    def test_a_finished_invitation_cannot_be_used_again(self):
        hid, (owner,) = self.household("Fam Reuse")
        pairing = self.operator.issue_pairing(hid, owner, "owner", "operator")
        first = self.client()
        enrolment = first.post("/api/auth/pairing/redeem", {"link": pairing["link"], "code": pairing["code"]})[1]["enrolment"]
        email = self.unique("a")
        first.post("/api/auth/enrol/email", {"enrolment": enrolment, "email": email, "accept_terms": True, "terms_version": TERMS})
        self.assertEqual(first.post("/api/auth/enrol/verify", {"enrolment": enrolment, "email": email, "code": self.mail.last_code(email)})[0], 200)
        self.assertEqual(self.client().post("/api/auth/pairing/redeem", {"link": pairing["link"], "code": pairing["code"]})[0], 410)
        replay = self.mail.last_code(email)                                       # even the genuine, already-used code gets nowhere
        for code in ("123456", replay):
            self.assertIn(self.client().post("/api/auth/enrol/verify", {"enrolment": enrolment, "email": email, "code": code})[0], (403, 410))
        with self.owner_store._connection() as c:
            self.assertEqual(c.execute("SELECT count(*) FROM auth_accounts WHERE lower(email) = ?", (email,)).fetchone()[0], 1)

    def test_an_invitation_expires_after_thirty_minutes(self):
        hid, (owner,) = self.household("Fam Expire")
        pairing = self.operator.issue_pairing(hid, owner, "owner", "operator")
        self.advance(minutes=31)
        self.assertEqual(self.client().post("/api/auth/pairing/redeem", {"link": pairing["link"], "code": pairing["code"]})[0], 410)

    def test_the_terms_must_be_accepted_and_must_be_the_current_version(self):
        hid, (owner,) = self.household("Fam Terms")
        pairing = self.operator.issue_pairing(hid, owner, "owner", "operator")
        client = self.client()
        enrolment = client.post("/api/auth/pairing/redeem", {"link": pairing["link"], "code": pairing["code"]})[1]["enrolment"]
        email = self.unique("t")
        for accept, version in ((False, TERMS), (None, TERMS), ("true", TERMS), (True, "an-old-version"), (True, None)):
            status, body = client.post("/api/auth/enrol/email", {"enrolment": enrolment, "email": email, "accept_terms": accept, "terms_version": version})
            self.assertEqual((status, body["error"]), (400, "terms_required"), (accept, version))
        self.assertEqual(self.mail.outbox, [])
        self.assertEqual(client.post("/api/auth/enrol/email", {"enrolment": enrolment, "email": email, "accept_terms": True, "terms_version": TERMS})[0], 202)

    def test_a_bad_email_address_is_refused(self):
        hid, (owner,) = self.household("Fam Mail")
        pairing = self.operator.issue_pairing(hid, owner, "owner", "operator")
        client = self.client()
        enrolment = client.post("/api/auth/pairing/redeem", {"link": pairing["link"], "code": pairing["code"]})[1]["enrolment"]
        for bad in ("", "nina", "a@b", "a b@c.de", "@x.de", "x" * 300 + "@example.org", None, 5):
            status, body = client.post("/api/auth/enrol/email", {"enrolment": enrolment, "email": bad, "accept_terms": True, "terms_version": TERMS})
            self.assertEqual((status, body["error"]), (400, "invalid_email"), bad)

    # ------------------------------------------------------------------ email codes
    def test_a_code_works_once_and_not_after_fifteen_minutes(self):
        hid, (owner,) = self.household("Fam Code")
        email = self.unique("c")
        self.enrol(hid, owner, email)
        client = self.client()
        client.post("/api/auth/login/start", {"email": email})
        code = self.mail.last_code(email, "login")
        self.advance(minutes=16)
        self.assertEqual(client.post("/api/auth/login/verify", {"email": email, "code": code})[0], 403)         # expired
        client.post("/api/auth/login/start", {"email": email})
        code = self.mail.last_code(email, "login")
        self.assertEqual(client.post("/api/auth/login/verify", {"email": email, "code": code})[0], 200)
        self.assertEqual(self.client().post("/api/auth/login/verify", {"email": email, "code": code})[0], 403)  # replay

    def test_five_wrong_guesses_burn_the_code_even_if_the_next_guess_is_right(self):
        hid, (owner,) = self.household("Fam Guess")
        email = self.unique("g")
        self.enrol(hid, owner, email)
        client = self.client()
        client.post("/api/auth/login/start", {"email": email})
        right = self.mail.last_code(email, "login")
        wrong = "000000" if right != "000000" else "111111"
        for _ in range(5):
            self.assertEqual(client.post("/api/auth/login/verify", {"email": email, "code": wrong})[0], 403)
        self.assertEqual(client.post("/api/auth/login/verify", {"email": email, "code": right})[0], 403)
        self.advance(seconds=31)
        client.post("/api/auth/login/start", {"email": email})                   # a new code starts clean
        self.assertEqual(client.post("/api/auth/login/verify", {"email": email, "code": self.mail.last_code(email, "login")})[0], 200)

    def test_asking_again_invalidates_the_earlier_code_and_is_throttled(self):
        hid, (owner,) = self.household("Fam Again")
        email = self.unique("r")
        self.enrol(hid, owner, email)
        client = self.client()
        client.post("/api/auth/login/start", {"email": email})
        first = self.mail.last_code(email, "login")
        client.post("/api/auth/login/start", {"email": email})                   # within 30 seconds: no second mail
        self.assertEqual(len([m for m in self.mail.outbox if m.purpose == "login"]), 1)
        self.advance(seconds=31)
        client.post("/api/auth/login/start", {"email": email})
        second = self.mail.last_code(email, "login")
        self.assertNotEqual(first, second)
        if first != second:
            self.assertEqual(client.post("/api/auth/login/verify", {"email": email, "code": first})[0], 403)
        self.assertEqual(client.post("/api/auth/login/verify", {"email": email, "code": second})[0], 200)

    def test_sign_in_does_not_reveal_whether_an_address_has_an_account(self):
        hid, (owner,) = self.household("Fam Enum")
        known, unknown = self.unique("known"), self.unique("unknown")
        self.enrol(hid, owner, known)
        self.mail.outbox.clear()
        a = self.client().post("/api/auth/login/start", {"email": known})
        b = self.client().post("/api/auth/login/start", {"email": unknown})
        self.assertEqual(a, b)                                                  # identical status and body
        self.assertEqual([m.to for m in self.mail.outbox], [known])             # only the real account got a mail
        wrong_known = self.client().post("/api/auth/login/verify", {"email": known, "code": "000000"})
        wrong_unknown = self.client().post("/api/auth/login/verify", {"email": unknown, "code": "000000"})
        self.assertEqual(wrong_known, wrong_unknown)

    def test_requests_for_codes_are_rate_limited(self):
        hid, (owner,) = self.household("Fam Rate")
        email = self.unique("limit")
        self.enrol(hid, owner, email)
        client, statuses = self.client(), []
        for _ in range(7):
            self.advance(seconds=31)
            statuses.append(client.post("/api/auth/login/start", {"email": email})[0])
        self.assertEqual(statuses[:4], [202, 202, 202, 202])
        self.assertIn(429, statuses)

    # ------------------------------------------------------------------ sessions
    def test_the_session_cookie_is_locked_down_and_the_session_slides_and_expires(self):
        hid, (owner,) = self.household("Fam Session")
        client = self.enrol(hid, owner, self.unique("s"))
        header = client.last_cookie_header
        self.assertIn("HttpOnly", header)
        self.assertIn("SameSite=Lax", header)
        self.assertIn("Path=/", header)
        self.assertIn("Max-Age=2592000", header)
        self.assertNotIn("Secure", header)                                      # this test server runs without TLS
        self.assertIn("Secure", AuthGate(self.accounts, AuthSettings(cookie_secure=True)).cookie_header("t")[1])
        self.advance(days=20)
        self.assertEqual(client.get("/api/auth/me")[0], 200)                    # still valid, and renewed by this use
        self.advance(days=20)
        self.assertEqual(client.get("/api/auth/me")[0], 200)                    # 40 days after sign-in, 20 after the renewal
        self.advance(days=31)
        self.assertEqual(client.get("/api/auth/me")[0], 401)

    def test_sessions_can_be_listed_and_revoked_and_logout_ends_one(self):
        hid, (owner,) = self.household("Fam Sessions")
        email = self.unique("m")
        phone = self.enrol(hid, owner, email)
        laptop = self.login(email)
        sessions = phone.get("/api/auth/sessions")[1]["sessions"]
        self.assertEqual(len(sessions), 2)
        other = next(s for s in sessions if not s["current"])
        self.assertEqual(phone.call("DELETE", "/api/auth/sessions/" + other["id"])[0], 200)
        self.assertEqual(laptop.get("/api/auth/me")[0], 401)
        self.assertEqual(phone.call("DELETE", "/api/auth/sessions/" + other["id"])[0], 404)
        self.assertEqual(phone.post("/api/auth/logout")[0], 200)
        self.assertEqual(phone.get("/api/auth/me")[0], 401)

    def test_a_person_cannot_revoke_someone_elses_session(self):
        hid, (owner,) = self.household("Fam Mine")
        hid2, (owner2,) = self.household("Fam Theirs")
        mine, theirs = self.enrol(hid, owner, self.unique("mine")), self.enrol(hid2, owner2, self.unique("theirs"))
        victim = theirs.get("/api/auth/sessions")[1]["sessions"][0]["id"]
        self.assertEqual(mine.call("DELETE", "/api/auth/sessions/" + victim)[0], 404)
        self.assertEqual(theirs.get("/api/auth/me")[0], 200)

    def test_a_request_from_another_website_is_refused(self):
        hid, (owner,) = self.household("Fam Csrf")
        client = self.enrol(hid, owner, self.unique("csrf"))
        host = "%s:%d" % self.address
        self.assertEqual(client.post("/api/auth/logout", headers={"Origin": "https://evil.example", "Host": host})[0], 403)
        self.assertEqual(client.get("/api/auth/me")[0], 200)                    # still signed in: the forged request did nothing
        self.assertEqual(client.post("/api/auth/sessions/none", headers={"Origin": "http://" + host})[0] in (404, 405), True)

    def test_behind_a_trusted_proxy_the_public_hostname_counts_as_the_origin(self):
        from chit_server.auth_gate import _origin_ok
        from chit_server.router import Request
        forwarded = Request("POST", "/api/auth/logout", {}, "application/json", b"{}", headers={
            "origin": "https://app.chithome.de", "host": "10.0.0.5:8080", "x-forwarded-host": "app.chithome.de"})
        forged = Request("POST", "/api/auth/logout", {}, "application/json", b"{}", headers={
            "origin": "https://evil.example", "host": "10.0.0.5:8080", "x-forwarded-host": "app.chithome.de"})
        self.assertFalse(_origin_ok(AuthGate(self.accounts, AuthSettings()), forwarded))                       # header not trusted without a proxy
        self.assertTrue(_origin_ok(AuthGate(self.accounts, AuthSettings(trusted_proxy_hops=1)), forwarded))
        self.assertFalse(_origin_ok(AuthGate(self.accounts, AuthSettings(trusted_proxy_hops=1)), forged))
        self.assertTrue(_origin_ok(AuthGate(self.accounts, AuthSettings(allowed_origins=frozenset({"https://evil.example"}))), forged))   # explicit allow-list

    def test_secrets_are_stored_only_as_hashes(self):
        hid, (owner,) = self.household("Fam Hash")
        email = self.unique("h")
        pairing = self.operator.issue_pairing(hid, owner, "owner", "operator")
        client = self.client()
        enrolment = client.post("/api/auth/pairing/redeem", {"link": pairing["link"], "code": pairing["code"]})[1]["enrolment"]
        client.post("/api/auth/enrol/email", {"enrolment": enrolment, "email": email, "accept_terms": True, "terms_version": TERMS})
        mail_code = self.mail.last_code(email)
        client.post("/api/auth/enrol/verify", {"enrolment": enrolment, "email": email, "code": mail_code})
        with self.owner_store._connection() as c:
            dump = "\n".join(str(row) for t in ("auth_pairings", "auth_enrolments", "auth_email_codes", "auth_sessions", "auth_events")
                             for row in c.execute("SELECT * FROM " + t).fetchall())
        for secret in (pairing["link"], pairing["code"], enrolment, mail_code, client.cookie):
            self.assertNotIn(secret, dump)

    # ------------------------------------------------------------------ terms
    def test_new_terms_must_be_accepted_before_anything_else_works(self):
        hid, (owner,) = self.household("Fam NewTerms")
        client = self.enrol(hid, owner, self.unique("nt"))
        self.assertEqual(client.get("/api/household/summary")[0], 200)
        self.accounts.terms_version = "2027-01-beta-2"
        status, body = client.get("/api/household/summary")
        self.assertEqual((status, body["error"], body["terms_version"]), (403, "terms_required", "2027-01-beta-2"))
        self.assertFalse(client.get("/api/auth/me")[1]["terms"]["accepted"])      # the sign-in screen can still ask
        self.assertEqual(client.post("/api/auth/terms/accept", {"terms_version": TERMS})[0], 400)       # not the current version
        self.assertEqual(client.post("/api/auth/terms/accept", {"terms_version": "2027-01-beta-2"})[0], 200)
        self.assertEqual(client.get("/api/household/summary")[0], 200)

    # ------------------------------------------------------------------ households
    def test_one_person_in_two_households_chooses_which_one_they_serve(self):
        a, (owner_a,) = self.household("Fam Mum")
        b, (owner_b,) = self.household("Fam Dad")
        email = self.unique("both")
        self.enrol(a, owner_a, email)
        self.enrol(b, owner_b, email)                                           # the same account gets a second membership
        client = self.login(email)
        self.assertEqual(client.get("/api/household/summary")[1]["error"], "household_required")
        households = client.get("/api/auth/me")[1]["households"]
        self.assertEqual(sorted(h["name"] for h in households), ["Fam Dad", "Fam Mum"])
        self.assertEqual(client.post("/api/auth/household/select", {"household_id": a})[0], 200)
        body = json.dumps(client.get("/api/household/summary")[1])
        self.assertIn("Fam Mum", body)
        self.assertNotIn("Fam Dad", body)
        client.post("/api/auth/household/select", {"household_id": b})
        body = json.dumps(client.get("/api/household/summary")[1])
        self.assertIn("Fam Dad", body)
        self.assertNotIn("Fam Mum", body)

    def test_a_person_cannot_select_or_see_a_household_they_do_not_belong_to(self):
        a, (owner_a,) = self.household("Fam Mine2")
        b, (owner_b,) = self.household("Fam Stranger")
        client = self.enrol(a, owner_a, self.unique("me"))
        self.enrol(b, owner_b, self.unique("stranger"))
        self.assertEqual(client.post("/api/auth/household/select", {"household_id": b})[0], 403)
        self.assertEqual(client.get("/api/auth/me")[1]["household_id"], a)
        self.assertNotIn("Fam Stranger", json.dumps(client.get("/api/auth/me")[1]))
        self.assertNotIn("Fam Stranger", json.dumps(client.get("/api/household/summary")[1]))

    # ------------------------------------------------------------------ owner rules
    def test_the_owner_invites_another_adult_who_cannot_do_owner_things(self):
        hid, (owner, partner) = self.household("Fam Two", adults=("Owner", "Partner"))
        owner_client = self.enrol(hid, owner, self.unique("own"))
        members = owner_client.get("/api/auth/members")[1]["members"]
        self.assertEqual({m["name"]: m["has_account"] for m in members if m["role"] == "adult"}, {"Owner": True, "Partner": False})
        status, invite = owner_client.post("/api/auth/invites", {"member_id": partner})
        self.assertEqual(status, 201)
        partner_email = self.unique("partner")
        partner_client = self.client()
        enrolment = partner_client.post("/api/auth/pairing/redeem", {"link": invite["link"], "code": invite["code"]})[1]["enrolment"]
        partner_client.post("/api/auth/enrol/email", {"enrolment": enrolment, "email": partner_email, "accept_terms": True, "terms_version": TERMS})
        self.assertEqual(partner_client.post("/api/auth/enrol/verify", {"enrolment": enrolment, "email": partner_email, "code": self.mail.last_code(partner_email)})[0], 200)
        me = partner_client.get("/api/auth/me")[1]
        self.assertEqual((me["role"], me["household_id"]), ("adult", hid))
        self.assertIn("Fam Two", json.dumps(partner_client.get("/api/household/summary")[1]))      # shares the household
        for call in (lambda: partner_client.get("/api/auth/members"), lambda: partner_client.post("/api/auth/invites", {"member_id": owner}),
                     lambda: partner_client.post("/api/auth/owner/transfer", {"member_id": partner})):
            status, body = call()
            self.assertEqual((status, body["error"]), (403, "owner_only"))
        self.assertEqual(owner_client.post("/api/auth/invites", {"member_id": owner})[1]["error"], "is_owner")
        kid = next(m["id"] for m in members if m["role"] == "child")
        self.assertEqual(owner_client.post("/api/auth/invites", {"member_id": kid})[0], 404)       # children get no accounts

    def test_ownership_moves_only_after_a_fresh_email_confirmation(self):
        hid, (owner, partner) = self.household("Fam Transfer", adults=("Owner", "Partner"))
        owner_email, partner_email = self.unique("o"), self.unique("p")
        owner_client = self.enrol(hid, owner, owner_email)
        partner_client = self.enrol(hid, partner, partner_email, role="adult")
        status, body = owner_client.post("/api/auth/owner/transfer", {"member_id": partner})
        self.assertEqual((status, body["error"]), (403, "reauth_required"))
        owner_client.post("/api/auth/reauth/start")
        self.assertEqual(owner_client.post("/api/auth/reauth/verify", {"code": "000000"})[0], 403)
        self.assertEqual(owner_client.post("/api/auth/reauth/verify", {"code": self.mail.last_code(owner_email, "reauth")})[0], 200)
        self.advance(minutes=11)                                                # the confirmation has gone stale
        self.assertEqual(owner_client.post("/api/auth/owner/transfer", {"member_id": partner})[1]["error"], "reauth_required")
        self.advance(seconds=31)
        owner_client.post("/api/auth/reauth/start")
        owner_client.post("/api/auth/reauth/verify", {"code": self.mail.last_code(owner_email, "reauth")})
        self.assertEqual(owner_client.post("/api/auth/owner/transfer", {"member_id": partner})[0], 200)
        self.assertEqual(owner_client.get("/api/auth/me")[1]["role"], "adult")
        self.assertEqual(partner_client.get("/api/auth/me")[1]["role"], "owner")
        with self.owner_store._connection() as c:
            self.assertEqual(c.execute("SELECT owner_member_id FROM households WHERE id = ?", (hid,)).fetchone()[0], partner)
        self.assertEqual(owner_client.post("/api/auth/owner/transfer", {"member_id": owner})[1]["error"], "owner_only")

    def test_ownership_cannot_go_to_someone_who_has_not_signed_in_or_to_a_child(self):
        hid, (owner, partner) = self.household("Fam NoTransfer", adults=("Owner", "Partner"))
        email = self.unique("ot")
        client = self.enrol(hid, owner, email)
        kid = next(m["id"] for m in client.get("/api/auth/members")[1]["members"] if m["role"] == "child")
        client.post("/api/auth/reauth/start")
        client.post("/api/auth/reauth/verify", {"code": self.mail.last_code(email, "reauth")})
        for target in (partner, kid, "nobody", owner):
            self.assertEqual(client.post("/api/auth/owner/transfer", {"member_id": target})[0], 400, target)
        self.assertEqual(client.get("/api/auth/me")[1]["role"], "owner")

    def test_the_operator_can_replace_a_lost_mailbox_by_pairing_the_member_again(self):
        hid, (owner,) = self.household("Fam Lost")
        old, new = self.unique("old"), self.unique("new")
        old_client = self.enrol(hid, owner, old)
        new_client = self.enrol(hid, owner, new)                                # a new invitation for the same seat
        self.assertEqual(new_client.get("/api/auth/me")[1]["role"], "owner")
        self.assertEqual(old_client.get("/api/household/summary")[0], 409)       # the old account lost the seat (no household any more)
        relogin = self.login(old)
        self.assertEqual(relogin.get("/api/household/summary")[0], 409)
        self.assertEqual(self.login(new).get("/api/household/summary")[0], 200)

    def test_a_disabled_account_cannot_sign_in_and_is_signed_out(self):
        hid, (owner,) = self.household("Fam Disabled")
        email = self.unique("dis")
        client = self.enrol(hid, owner, email)
        with self.owner_store._connection() as c:
            c.execute("UPDATE auth_accounts SET disabled_at = ? WHERE lower(email) = ?", ("2026-10-12T09:00:00.000000+00:00", email))
        self.assertEqual(client.get("/api/household/summary")[0], 401)
        self.mail.outbox.clear()
        self.client().post("/api/auth/login/start", {"email": email})
        self.assertEqual(self.mail.outbox, [])

    # ------------------------------------------------------------------ kid phones keep working beside accounts
    def test_kid_phone_routes_need_a_device_token_not_a_session_and_parent_routes_need_a_session(self):
        hid, (owner,) = self.household("Fam Phone")
        child = [m for m in self.owner_store.list_household(hid)["members"] if m["role"] == "child"][0]["id"]
        self.owner_store.set_phone_settings(hid, child, True)
        pairing = self.owner_store.create_phone_pairing(hid, child)
        device = self.owner_store.complete_phone_pairing(pairing["secret"], pairing["code"])
        anon = self.client()
        status, view = anon.get("/api/kids/phone/device/view", headers={"Authorization": "Bearer " + device["token"]})
        self.assertEqual(status, 200)
        self.assertEqual(anon.get("/api/kids/phone/settings")[0], 401)                                    # parent route: no session
        self.assertEqual(anon.get("/api/kids/phone/settings", headers={"Authorization": "Bearer " + device["token"]})[0], 401)
        parent = self.enrol(hid, owner, self.unique("par"))
        self.assertEqual(parent.get("/api/kids/phone/settings")[0], 200)
        self.assertEqual(parent.get("/api/kids/phone/device/view")[0], 401)                               # a parent session is not a device


if __name__ == "__main__":
    unittest.main()
