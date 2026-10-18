/* Planning Assistant: sign-in (Amazon Cognito, SRP) and chat, native to this site.
   Sign-in covers every step the user pool can ask for: new password on first sign-in, authenticator
   enrollment (MFA_SETUP, with a QR code), the authenticator code (SOFTWARE_TOKEN_MFA) and password reset.
   The chat posts to the same assistant API as the earlier site, with the same request shape and limits. */
(function () {
  'use strict';

  var CONFIG = Object.freeze({
    api: 'https://zale82q9w3.execute-api.us-east-1.amazonaws.com/chat',
    userPoolId: 'us-east-1_mKrwfQTkg',
    clientId: '1to2nea9si42s5a0g5rn7ag52g',
    issuer: 'EV Site Readiness'
  });
  var MAX_HISTORY_TURNS = 6;
  var MAX_HISTORY_CHARS_PER_TURN = 900;
  var MAX_MESSAGE_LENGTH = 2000;

  var $ = function (id) { return document.getElementById(id); };
  var esc = FC.esc;
  var Cog = window.AmazonCognitoIdentity;
  var storage = (function () {
    try { var k = '__fc'; sessionStorage.setItem(k, '1'); sessionStorage.removeItem(k); return sessionStorage; } catch (e) { return undefined; }
  })();
  var pool = Cog ? new Cog.CognitoUserPool({ UserPoolId: CONFIG.userPoolId, ClientId: CONFIG.clientId, Storage: storage }) : null;

  var gate = $('as-gate'), chat = $('as-chat'), intro = $('as-intro');
  var views = Array.prototype.slice.call(document.querySelectorAll('[data-view]'));
  var activeUser = null, resetUser = null, pendingEmail = '';
  var sessionId = window.crypto && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2) + Date.now().toString(36);
  var history = [];
  var busy = false;

  /* ---------- Sign-in views ---------- */
  function show(view, focusSel) {
    views.forEach(function (v) { v.hidden = v.getAttribute('data-view') !== view; });
    message('');
    var el = document.querySelector('[data-view="' + view + '"] ' + (focusSel || 'input'));
    if (el) el.focus();
  }
  function message(text, kind) {
    var m = $('as-auth-msg');
    m.textContent = text || '';
    m.hidden = !text;
    m.className = 'as-msg' + (kind === 'ok' ? ' as-msg--ok' : '');
  }
  function busyButton(btn, label) {
    var old = btn.innerHTML;
    btn.disabled = true; btn.setAttribute('aria-busy', 'true');
    btn.innerHTML = '<span class="as-spinner" aria-hidden="true"></span><span class="hig-button__label">' + esc(label) + '</span>';
    return function () { btn.disabled = false; btn.removeAttribute('aria-busy'); btn.innerHTML = old; };
  }
  function authError(err) {
    var code = (err && (err.code || err.name)) || '';
    var map = {
      NotAuthorizedException: 'The email or password is incorrect. Check both and try again.',
      UserNotFoundException: 'The email or password is incorrect. Check both and try again.',
      UserNotConfirmedException: 'This account is not confirmed yet. Contact the project team to finish setting it up.',
      PasswordResetRequiredException: 'This account needs a new password. Choose Forgot Password to set one.',
      CodeMismatchException: 'That code is not correct. Check the code in your authenticator app and try again.',
      EnableSoftwareTokenMFAException: 'That code is not correct. Enter the current 6-digit code from your authenticator app.',
      ExpiredCodeException: 'That code has expired. Request a new one and try again.',
      InvalidPasswordException: 'That password does not meet the requirements. Use at least 8 characters with upper and lower case letters, a number and a symbol.',
      LimitExceededException: 'Too many attempts. Wait a few minutes, then try again.',
      TooManyRequestsException: 'Too many attempts. Wait a few minutes, then try again.',
      TooManyFailedAttemptsException: 'Too many attempts. Wait a few minutes, then try again.',
      InvalidParameterException: 'Some information is missing or not in the expected format. Check the form and try again.',
      NetworkError: 'The sign-in service could not be reached. Check your connection and try again.'
    };
    if (map[code]) return map[code];
    if (err && /session is expired|Invalid session/i.test(err.message || '')) return 'The sign-in session expired. Start again from your email and password.';
    if (err && /network|fetch/i.test(err.message || '')) return map.NetworkError;
    return 'Sign-in did not complete. Try again, and contact the project team if it keeps happening.';
  }

  /* One callback set for every step of authenticateUser, so a challenge that follows another
     (new password, then authenticator enrollment) lands in the right view. */
  function callbacks(restore) {
    var done = function () { if (restore) restore(); restore = null; };
    return {
      onSuccess: function () { done(); clearSecrets(); signedIn(); },
      onFailure: function (err) { done(); clearSecrets(); message(authError(err)); },
      newPasswordRequired: function () { done(); show('new-password'); message('Create a new password to finish signing in.', 'ok'); },
      mfaSetup: function () { done(); startEnrollment(); },
      totpRequired: function () { done(); show('code'); },
      mfaRequired: function () { done(); message('This account asks for a text-message code, which this page does not support. Contact the project team.'); },
      selectMFAType: function () { activeUser.sendMFASelectionAnswer('SOFTWARE_TOKEN_MFA', callbacks()); }
    };
  }
  function clearSecrets() {
    document.querySelectorAll('#as-gate input[type="password"], #as-gate input[autocomplete="one-time-code"]').forEach(function (i) { i.value = ''; });
  }

  function startEnrollment() {
    show('enroll', 'button, input');
    $('as-qr').innerHTML = '<span class="as-spinner" aria-hidden="true"></span>';
    activeUser.associateSoftwareToken({
      associateSecretCode: function (secret) {
        var label = encodeURIComponent(CONFIG.issuer + ':' + pendingEmail);
        var uri = 'otpauth://totp/' + label + '?secret=' + secret + '&issuer=' + encodeURIComponent(CONFIG.issuer);
        $('as-secret').textContent = secret.replace(/(.{4})/g, '$1 ').trim();
        $('as-secret').setAttribute('data-secret', secret);
        $('as-otpauth').href = uri;
        $('as-qr').innerHTML = qrSvg(uri);
        $('as-enroll-code').focus();
      },
      onFailure: function (err) { message(authError(err)); }
    });
  }
  function qrSvg(text) {
    if (typeof window.qrcode !== 'function') return '<p class="footnote">Enter the setup key below in your authenticator app.</p>';
    var qr = window.qrcode(0, 'M'); qr.addData(text); qr.make();
    var n = qr.getModuleCount(), q = 4, size = n + q * 2, d = '';
    for (var r = 0; r < n; r++) for (var c = 0; c < n; c++) if (qr.isDark(r, c)) d += 'M' + (c + q) + ' ' + (r + q) + 'h1v1h-1z';
    return '<svg viewBox="0 0 ' + size + ' ' + size + '" role="img" aria-label="QR code for adding this account to an authenticator app" shape-rendering="crispEdges">' +
      '<rect width="' + size + '" height="' + size + '" fill="#fff"/><path d="' + d + '" fill="#000"/></svg>';
  }

  function bindForms() {
    $('as-signin-form').addEventListener('submit', function (e) {
      e.preventDefault();
      var email = $('as-email').value.trim(), pw = $('as-password').value;
      if (!email || !pw) { message('Enter your email and password.'); return; }
      if (!pool) { message('The sign-in library did not load. Reload the page and try again.'); return; }
      pendingEmail = email;
      var restore = busyButton($('as-signin-btn'), 'Signing In');
      activeUser = new Cog.CognitoUser({ Username: email, Pool: pool, Storage: storage });
      activeUser.authenticateUser(new Cog.AuthenticationDetails({ Username: email, Password: pw }), callbacks(restore));
    });
    $('as-newpw-form').addEventListener('submit', function (e) {
      e.preventDefault();
      var a = $('as-newpw').value, b = $('as-newpw2').value;
      if (a !== b) { message('The two passwords do not match.'); return; }
      var restore = busyButton($('as-newpw-btn'), 'Saving');
      // Send no attributes back: Cognito returns read-only ones (email_verified) that it would reject.
      activeUser.completeNewPasswordChallenge(a, {}, callbacks(restore));
    });
    $('as-enroll-form').addEventListener('submit', function (e) {
      e.preventDefault();
      var code = $('as-enroll-code').value.replace(/\s+/g, '');
      if (!/^\d{6}$/.test(code)) { message('Enter the 6-digit code your authenticator app shows.'); return; }
      var restore = busyButton($('as-enroll-btn'), 'Verifying');
      activeUser.verifySoftwareToken(code, 'Authenticator', {
        onSuccess: function () { restore(); clearSecrets(); signedIn(); },
        onFailure: function (err) { restore(); clearSecrets(); message(authError(err)); }
      });
    });
    $('as-code-form').addEventListener('submit', function (e) {
      e.preventDefault();
      var code = $('as-code').value.replace(/\s+/g, '');
      if (!/^\d{6}$/.test(code)) { message('Enter the 6-digit code your authenticator app shows.'); return; }
      var restore = busyButton($('as-code-btn'), 'Verifying');
      activeUser.sendMFACode(code, callbacks(restore), 'SOFTWARE_TOKEN_MFA');
    });
    $('as-copy-secret').addEventListener('click', function () {
      var s = $('as-secret').getAttribute('data-secret') || '';
      var ok = function () { message('Setup key copied.', 'ok'); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(s).then(ok, function () { message('Copy did not work. Select the key and copy it by hand.'); });
      else message('Copy is not available here. Select the key and copy it by hand.');
    });
    $('as-forgot-link').addEventListener('click', function () {
      $('as-forgot-email').value = $('as-email').value.trim();
      show('forgot');
    });
    document.querySelectorAll('[data-back-to-signin]').forEach(function (b) {
      b.addEventListener('click', function () { activeUser = null; show('signin'); });
    });
    $('as-forgot-form').addEventListener('submit', function (e) {
      e.preventDefault();
      var email = $('as-forgot-email').value.trim();
      if (!email) { message('Enter the email for your account.'); return; }
      var restore = busyButton($('as-forgot-btn'), 'Sending');
      resetUser = new Cog.CognitoUser({ Username: email, Pool: pool, Storage: storage });
      resetUser.forgotPassword({
        onSuccess: function () { restore(); },
        onFailure: function (err) { restore(); message(authError(err)); },
        inputVerificationCode: function () { restore(); show('reset'); message('If an account exists for that email, a reset code is on its way.', 'ok'); }
      });
    });
    $('as-reset-form').addEventListener('submit', function (e) {
      e.preventDefault();
      var code = $('as-reset-code').value.trim(), a = $('as-reset-pw').value, b = $('as-reset-pw2').value;
      if (a !== b) { message('The two passwords do not match.'); return; }
      var restore = busyButton($('as-reset-btn'), 'Saving');
      resetUser.confirmPassword(code, a, {
        onSuccess: function () { restore(); clearSecrets(); show('signin'); message('Password changed. Sign in with the new password.', 'ok'); },
        onFailure: function (err) { restore(); clearSecrets(); message(authError(err)); }
      });
    });
  }

  /* ---------- Session ---------- */
  function currentEmail(cb) {
    var u = pool && pool.getCurrentUser();
    if (!u) { cb(null); return; }
    u.getSession(function (err, session) {
      if (err || !session || !session.isValid()) { cb(null); return; }
      var p = session.getIdToken().payload || {};
      activeUser = u;
      cb(p.email || u.getUsername());
    });
  }
  function signedIn() {
    currentEmail(function (email) {
      if (!email) { signedOut(); return; }
      gate.hidden = true; intro.hidden = true; chat.hidden = false;
      document.body.classList.add('as-chatting');
      $('as-who').textContent = email;
      if (!$('as-log').children.length) $('as-empty').hidden = false;
      $('as-input').focus();
    });
  }
  function signedOut() {
    chat.hidden = true; gate.hidden = false; intro.hidden = false;
    document.body.classList.remove('as-chatting');
    show('signin', '#as-email');
  }
  $('as-signout').addEventListener('click', function () {
    var u = pool && pool.getCurrentUser();
    if (u) u.signOut();
    activeUser = null; history = []; $('as-log').textContent = ''; $('as-empty').hidden = false;
    signedOut();
    message('Signed out.', 'ok');
  });
  $('as-new').addEventListener('click', function () {
    history = []; $('as-log').textContent = ''; $('as-empty').hidden = false;
    sessionId = window.crypto && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2) + Date.now().toString(36);
    $('as-input').focus();
  });

  /* ---------- Chat ---------- */
  function inline(text) {
    var out = esc(text);
    out = out.replace(/\[([^\]]+)\]\((https:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    out = out.replace(/`([^`]+)`/g, '<code>$1</code>');
    out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    out = out.replace(/(^|\s)\*([^*\n]+)\*(?=\s|$|[.,;:!?])/g, '$1<em>$2</em>');
    return out;
  }
  function markdown(src) {
    var lines = String(src == null ? '' : src).replace(/\r\n/g, '\n').split('\n');
    var html = [], para = [], list = null, items = [], code = null;
    function flushPara() { if (para.length) { html.push('<p>' + para.map(inline).join('<br>') + '</p>'); para = []; } }
    function flushList() { if (list) { html.push('<' + list + '>' + items.map(function (i) { return '<li>' + inline(i) + '</li>'; }).join('') + '</' + list + '>'); list = null; items = []; } }
    lines.forEach(function (raw) {
      var line = raw.replace(/\s+$/, '');
      if (code !== null) {
        if (/^```/.test(line.trim())) { html.push('<pre><code>' + esc(code.join('\n')) + '</code></pre>'); code = null; } else code.push(raw);
        return;
      }
      if (/^```/.test(line.trim())) { flushPara(); flushList(); code = []; return; }
      var h = line.match(/^#{1,6}\s+(.*)$/);
      var ul = line.match(/^\s*[-*•]\s+(.*)$/), ol = line.match(/^\s*\d+[.)]\s+(.*)$/);
      if (!line.trim()) { flushPara(); flushList(); return; }
      if (h) { flushPara(); flushList(); html.push('<p class="as-md-h">' + inline(h[1]) + '</p>'); return; }
      if (ul || ol) {
        flushPara();
        var t = ul ? 'ul' : 'ol';
        if (list && list !== t) flushList();
        list = t; items.push((ul || ol)[1]); return;
      }
      flushList(); para.push(line);
    });
    if (code !== null) html.push('<pre><code>' + esc(code.join('\n')) + '</code></pre>');
    flushPara(); flushList();
    return html.join('');
  }
  var seq = 0;
  function append(role, text, sources) {
    $('as-empty').hidden = true;
    var li = document.createElement('li');
    li.className = 'as-turn as-turn--' + role;
    var who = role === 'user' ? 'You' : 'Assistant';
    var body = role === 'user' ? '<p>' + esc(text).replace(/\n/g, '<br>') + '</p>' : markdown(text);
    var html = '<span class="hig-visually-hidden">' + who + ' said:</span><div class="as-bubble">' + body + '</div>';
    if (role === 'assistant' && Array.isArray(sources)) {
      var id = 'as-src-' + (++seq);
      html += sources.length
        ? '<details class="as-sources"><summary class="hig-focus">' + FC.icon('doc', { size: 15 }) + '<span>Sources Checked (' + sources.length + ')</span>' + FC.icon('chevron.down', { size: 13, className: 'as-sources__chev' }) + '</summary>' +
          '<ul id="' + id + '">' + sources.map(function (s) { return '<li>' + esc(s) + '</li>'; }).join('') + '</ul></details>'
        : '<p class="as-sources as-sources--none">No project files were checked for this answer.</p>';
    }
    li.innerHTML = html;
    $('as-log').appendChild(li);
    scrollToEnd();
    return li;
  }
  function system(text, retry) {
    var li = document.createElement('li');
    li.className = 'as-turn as-turn--system';
    li.innerHTML = '<div class="as-note" role="alert">' + FC.icon('exclamationmark.triangle', { size: 17 }) + '<span>' + esc(text) + '</span></div>';
    if (retry) {
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'hig-button hig-focus hig-pressable hig-button--ios hig-button--bordered hig-button--small as-retry';
      b.innerHTML = '<span class="hig-button__label">Try Again</span>';
      b.addEventListener('click', function () { li.remove(); retry(); });
      li.querySelector('.as-note').appendChild(b);
    }
    $('as-log').appendChild(li);
    scrollToEnd();
  }
  function scrollToEnd() {
    var end = $('as-end');
    if (end) end.scrollIntoView({ block: 'end', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  }
  function trimTurn(v) {
    var t = String(v || '').replace(/\s+/g, ' ').trim();
    return t.length > MAX_HISTORY_CHARS_PER_TURN ? t.slice(0, MAX_HISTORY_CHARS_PER_TURN) + '…' : t;
  }
  function remember(role, content) {
    var c = trimTurn(content);
    if (!c) return;
    history.push({ role: role, content: c });
    if (history.length > MAX_HISTORY_TURNS * 2) history = history.slice(-MAX_HISTORY_TURNS * 2);
  }
  function apiError(status, data) {
    var answer = data && (data.answer || data.message || data.error);
    if (status === 429) return answer || 'You have reached the assistant’s message limit. Try again later.';
    if (status === 401 || status === 403) return 'The assistant did not accept this request. Sign out, sign in again, and retry.';
    if (status >= 500) return 'The assistant service had a problem answering. Try again in a moment.';
    return answer || 'The assistant could not complete that request (HTTP ' + status + '). Try again.';
  }
  function setBusy(on) {
    busy = on;
    $('as-send').disabled = on || !$('as-input').value.trim();
    $('as-input').setAttribute('aria-busy', on ? 'true' : 'false');
    $('as-thinking').hidden = !on;
    if (on) scrollToEnd();
  }
  function send(text) {
    if (busy) return;
    text = String(text || '').trim();
    if (!text) return;
    if (text.length > MAX_MESSAGE_LENGTH) { system('That message is too long. Shorten it to ' + MAX_MESSAGE_LENGTH.toLocaleString('en-US') + ' characters or fewer.'); return; }
    append('user', text);
    $('as-input').value = ''; resize(); count();
    ask(text);
  }
  function ask(text) {
    setBusy(true);
    fetch(CONFIG.api, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, sessionId: sessionId, history: history.slice(-MAX_HISTORY_TURNS) })
    }).then(function (res) {
      return res.text().then(function (raw) {
        var data = null;
        try { data = raw ? JSON.parse(raw) : null; } catch (e) { data = { answer: raw }; }
        if (!res.ok) throw new Error(apiError(res.status, data));
        if (data && data.ok === false) throw new Error(data.answer || 'The assistant could not complete that request. Try again.');
        return data || {};
      });
    }).then(function (data) {
      setBusy(false);
      var answer = data.answer || 'The assistant returned an empty answer. Try asking in a different way.';
      append('assistant', answer, data.sources || []);
      remember('user', text); remember('assistant', answer);
      $('as-input').focus();
    }).catch(function (err) {
      setBusy(false);
      var msg = err instanceof TypeError ? 'The assistant service could not be reached. Check your connection and try again.' : err.message;
      system(msg, function () { ask(text); });
    });
  }

  var input = $('as-input');
  function resize() { input.style.height = 'auto'; input.style.height = Math.min(input.scrollHeight, 168) + 'px'; }
  function count() {
    var n = input.value.length, c = $('as-count');
    c.hidden = n < MAX_MESSAGE_LENGTH - 200;
    c.textContent = n.toLocaleString('en-US') + ' of ' + MAX_MESSAGE_LENGTH.toLocaleString('en-US');
    $('as-send').disabled = busy || !input.value.trim();
  }
  input.addEventListener('input', function () { resize(); count(); });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(input.value); }
  });
  $('as-composer').addEventListener('submit', function (e) { e.preventDefault(); send(input.value); });
  document.querySelectorAll('[data-ask]').forEach(function (b) {
    b.addEventListener('click', function () { send(b.getAttribute('data-ask')); });
  });

  /* ---------- Start ---------- */
  bindForms();
  if (!Cog) { message('The sign-in library did not load. Reload the page and try again.'); return; }
  currentEmail(function (email) { if (email) signedIn(); else views.forEach(function (v) { v.hidden = v.getAttribute('data-view') !== 'signin'; }); });
})();
