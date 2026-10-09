// Sign-in page (ADR-0014). Plain JavaScript on purpose: it has no build step and no dependency on the app shell.
// Flow: invitation link (#p=...) + code -> email + Terms -> email code -> signed in.  Returning: email -> email code.
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var sections = ['loading', 'invite', 'terms-email', 'login', 'code', 'new-terms', 'choose'];
  var state = { link: null, enrolment: null, email: null, mode: null, terms: null };

  // The invitation link travels in the URL fragment, so it is never sent to a server or written to a log. Take it out of the
  // address bar as soon as it is read.
  var match = /(?:^|[#&])p=([A-Za-z0-9_-]+)/.exec(window.location.hash);
  if (match) {
    state.link = match[1];
    history.replaceState(null, '', window.location.pathname);
  }

  var MESSAGES = {
    auth_required: 'Please sign in.',
    wrong_code: 'That code is not right or has expired.',
    pairing_invalid: 'This invitation has expired or was already used. Ask for a new one.',
    pairing_locked: 'Too many wrong codes. Ask for a new invitation.',
    enrolment_expired: 'This sign-up expired. Open your invitation link again.',
    rate_limited: 'Too many tries. Please wait a while and try again.',
    invalid_email: 'Please enter a valid email address.',
    terms_required: 'Please accept the Terms of Use to continue.',
    email_in_use: 'This email already belongs to someone else in this household.',
    account_disabled: 'This account is not active.',
    bad_origin: 'This request was blocked. Reload the page and try again.'
  };

  function show(name) {
    sections.forEach(function (id) { $(id).classList.toggle('hidden', id !== name); });
    $('error').textContent = '';
  }
  function fail(error) {
    var text = (error && error.body && (MESSAGES[error.body.error] || error.body.message)) || 'Something went wrong. Please try again.';
    if (error && error.body && error.body.attempts_left) text += ' ' + error.body.attempts_left + ' tries left.';
    $('error').textContent = text;
  }
  function call(method, path, body) {
    return fetch(path, {
      method: method, credentials: 'same-origin',
      headers: body === undefined ? { Accept: 'application/json' } : { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body)
    }).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (data) {
        if (!response.ok) { var error = new Error('http'); error.status = response.status; error.body = data; throw error; }
        return data;
      });
    });
  }
  function busy(form, on) {
    Array.prototype.forEach.call(form.querySelectorAll('button'), function (b) { b.disabled = on; });
  }
  function digits(value) { return String(value || '').replace(/\D/g, ''); }

  function termsLinks(terms) {
    state.terms = terms;
    ['terms-link', 'terms-link-again'].forEach(function (id) { if (terms.url) $(id).href = terms.url; });
  }

  // ---- after sign-in: Terms, household, then on to the app ---------------------------------------------------
  function continueSignedIn() {
    call('GET', '/api/auth/me').then(function (me) {
      $('signout').classList.remove('hidden');
      if (!me.terms.accepted) { show('new-terms'); return; }
      if (!me.household_id) {
        if (me.households.length === 0) { show('choose'); $('households').innerHTML = ''; $('error').textContent = 'You are not part of a household yet. Ask for a new invitation.'; return; }
        var list = $('households'); list.innerHTML = '';
        me.households.forEach(function (household) {
          var item = document.createElement('li'), button = document.createElement('button');
          button.type = 'button'; button.textContent = household.name;
          button.addEventListener('click', function () {
            call('POST', '/api/auth/household/select', { household_id: household.id }).then(function () { window.location.assign('/'); }).catch(fail);
          });
          item.appendChild(button); list.appendChild(item);
        });
        show('choose');
        return;
      }
      window.location.assign('/');
    }).catch(function (error) {
      if (error.status === 401) { start(); } else { fail(error); }
    });
  }

  function askForCode(mode, email) {
    state.mode = mode; state.email = email;
    $('code-target').textContent = email;
    $('email-code').value = '';
    show('code');
    $('email-code').focus();
  }

  // ---- forms ---------------------------------------------------------------------------------------------------------------------
  var handlers = {
    'redeem': function (form) {
      return call('POST', '/api/auth/pairing/redeem', { link: state.link, code: digits($('invite-code').value) }).then(function (data) {
        state.enrolment = data.enrolment; show('terms-email'); $('email').focus();
      });
    },
    'email': function () {
      var email = $('email').value.trim();
      return call('POST', '/api/auth/enrol/email', { enrolment: state.enrolment, email: email, accept_terms: $('accept').checked, terms_version: state.terms.version })
        .then(function () { askForCode('enrol', email); });
    },
    'login-start': function () {
      var email = $('login-email').value.trim();
      return call('POST', '/api/auth/login/start', { email: email }).then(function () { askForCode('login', email); });
    },
    'verify': function () {
      var code = digits($('email-code').value);
      var request = state.mode === 'enrol'
        ? call('POST', '/api/auth/enrol/verify', { enrolment: state.enrolment, email: state.email, code: code })
        : call('POST', '/api/auth/login/verify', { email: state.email, code: code });
      return request.then(continueSignedIn);
    },
    'accept-terms': function () {
      return call('POST', '/api/auth/terms/accept', { terms_version: state.terms.version }).then(continueSignedIn);
    }
  };
  document.addEventListener('submit', function (event) {
    var form = event.target, name = form.getAttribute('data-form');
    if (!name || !handlers[name]) return;
    event.preventDefault();
    $('error').textContent = '';
    busy(form, true);
    handlers[name](form).catch(fail).then(function () { busy(form, false); });
  });

  $('resend').addEventListener('click', function () {
    var again = state.mode === 'enrol'
      ? call('POST', '/api/auth/enrol/email', { enrolment: state.enrolment, email: state.email, accept_terms: true, terms_version: state.terms.version })
      : call('POST', '/api/auth/login/start', { email: state.email });
    again.then(function () { $('error').textContent = ''; $('resend').textContent = 'A new code is on its way.'; }).catch(fail);
  });
  $('signout').addEventListener('click', function () {
    call('POST', '/api/auth/logout', {}).catch(function () {}).then(function () { window.location.assign('/auth/'); });
  });

  // ---- start -----------------------------------------------------------------------------------------------------------------------
  function start() {
    $('signout').classList.add('hidden');
    if (state.link) { show('invite'); $('invite-code').focus(); } else { show('login'); $('login-email').focus(); }
  }
  call('GET', '/api/auth/terms').then(termsLinks).catch(function () { state.terms = { version: '', url: '' }; }).then(function () {
    if (state.link) { start(); return; }                               // an invitation always starts the enrolment flow
    call('GET', '/api/auth/me').then(continueSignedIn).catch(function () { start(); });
  });
})();
