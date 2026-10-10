#!/bin/sh
# Send ONE real sign-in-code email through Brevo to check the sending setup (ADR-0014). Needs .env.brevo (git-ignored) with
#   BREVO_API_KEY=...            a Brevo API key (SMTP & API -> API keys), NOT the SMTP password
#   CHIT_MAIL_FROM=hello@chithome.de
# Usage: scripts/mail-test.sh you@example.org
# Prints only the outcome, never the key. Then open the message and check the headers: SPF, DKIM and DMARC should all say PASS
# (Gmail: three dots -> Show original), and the message should land in the inbox, not spam.
set -eu
cd "$(dirname "$0")/.."
[ $# -eq 1 ] || { echo "usage: scripts/mail-test.sh recipient@example.org"; exit 2; }
[ -f .env.brevo ] || { echo "create .env.brevo first (see the comment at the top of this script)"; exit 1; }
set -a; . ./.env.brevo; set +a
export SSL_CERT_FILE="${SSL_CERT_FILE:-/etc/ssl/cert.pem}"
[ -x .venv/bin/python3 ] && PATH="$PWD/.venv/bin:$PATH"
PYTHONPATH=core/store python3 - "$1" <<'EOF'
import os, sys
from chit_store import mailer

to = sys.argv[1]
sender = mailer.BrevoMailer(os.environ.get("BREVO_API_KEY", ""), os.environ.get("CHIT_MAIL_FROM", ""), os.environ.get("CHIT_MAIL_FROM_NAME", "Chit"))
try:
    sender.send_code(to, "login", "123456")      # a dummy code: this is only a delivery test
except mailer.MailError as error:
    print("NOT SENT:", error)
    sys.exit(1)
print("Accepted by Brevo for delivery to %s from %s. Now check your inbox (and spam)." % (to, sender.sender))
EOF
