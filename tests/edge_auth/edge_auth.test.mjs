/**
 * The edge authoriser, exercised as the real thing.
 *
 * What makes this test worth trusting
 * -----------------------------------
 * It imports and calls the **actual handler** that gets deployed, with **real RSA keys** and
 * real signature verification. Only the network is stubbed — the JWKS endpoint and Cognito's
 * token endpoint — because those are the only parts that cannot run locally. Nothing about the
 * verification logic is reimplemented here, so a bug in the authoriser cannot be papered over
 * by a matching bug in the test.
 *
 * The pool identifiers below are duplicated from the module on purpose. If someone changes the
 * client id or issuer in `index.mjs` without changing them here, these tests **fail loudly** —
 * which is the direction a drift failure should point.
 *
 * The bar being tested is one sentence: **no request reaches the S3 origin unless it carries a
 * signature-verified, unexpired Cognito id_token for the one granted account.** Everything
 * else — expired, wrong audience, wrong pool, an access token, a forged algorithm, a duplicate
 * cookie, an unreachable JWKS — must deny.
 *
 * Run: node --test tests/edge_auth/
 */

import test from "node:test";
import assert from "node:assert/strict";
import { generateKeyPairSync, createSign } from "node:crypto";
import { pathToFileURL } from "node:url";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const MODULE = resolve(HERE, "../../infra/edge-auth/index.mjs");

// ---------------------------------------------------------------- keys and config

const KID = "fcf-test-key";
const { publicKey, privateKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
const FOREIGN = generateKeyPairSync("rsa", { modulusLength: 2048 });

const JWK = { ...publicKey.export({ format: "jwk" }), kid: KID, alg: "RS256", use: "sig" };

const ISSUER = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_mKrwfQTkg";
const CLIENT_ID = "1b9ab91m46pr3m2n74qapq3ls5";
const GRANTED_SUB = "00000000-0000-4000-8000-000000000003";
const GRANTED_EMAIL = "redacted-3@example.org";
const GRANTED2_SUB = "00000000-0000-4000-8000-000000000004";
const GRANTED2_EMAIL = "redacted-6@example.org";

// ---------------------------------------------------------------- network stub

let jwksDown = false;
let tokenPayload = null;
let tokenHttpOk = true;

globalThis.fetch = async (url) => {
  const target = String(url);
  if (target.includes("jwks.json")) {
    if (jwksDown) throw new Error("simulated network failure");
    return { ok: true, status: 200, json: async () => ({ keys: [JWK] }) };
  }
  if (target.includes("/oauth2/token")) {
    if (!tokenHttpOk) return { ok: false, status: 400, json: async () => ({}) };
    return { ok: true, status: 200, json: async () => tokenPayload };
  }
  throw new Error(`unexpected fetch: ${target}`);
};

const { handler } = await import(pathToFileURL(MODULE).href);

// ---------------------------------------------------------------- helpers

function signJwt(payload, { key = privateKey, kid = KID, alg = "RS256" } = {}) {
  const header = Buffer.from(JSON.stringify({ alg, kid, typ: "JWT" })).toString("base64url");
  const body = Buffer.from(JSON.stringify(payload)).toString("base64url");
  if (alg === "none") return `${header}.${body}.`;
  const signer = createSign("RSA-SHA256");
  signer.update(`${header}.${body}`);
  signer.end();
  return `${header}.${body}.${signer.sign(key).toString("base64url")}`;
}

function idToken(overrides = {}, signOpts = {}) {
  const now = Math.floor(Date.now() / 1000);
  return signJwt({
    iss: ISSUER, aud: CLIENT_ID, token_use: "id",
    sub: GRANTED_SUB, email: GRANTED_EMAIL,
    exp: now + 3600, iat: now, ...overrides,
  }, signOpts);
}

function ev(uri, { qs = "", cookies = [] } = {}) {
  const headers = {};
  if (cookies.length) headers.cookie = cookies.map((value) => ({ key: "Cookie", value }));
  return { Records: [{ cf: { request: { uri, querystring: qs, headers, method: "GET" } } }] };
}

const session = (jwt) => `__Host-fcf_session=${jwt}`;
const isAllow = (r) => r !== null && typeof r === "object" && !("status" in r) && "uri" in r;
const locationOf = (r) => r.headers?.location?.[0]?.value;
const cookiesOf = (r) => (r.headers?.["set-cookie"] || []).map((c) => c.value);

// ================================================================ the one thing that must hold

test("a valid granted token is the ONLY thing that reaches the origin", async () => {
  const r = await handler(ev("/platform/index.html", { cookies: [session(idToken())] }));
  assert.ok(isAllow(r), "a correctly signed, unexpired, granted token must pass through");
  assert.equal(r.uri, "/platform/index.html");
});

test("no cookie at all -> redirected to Cognito, never served", async () => {
  const r = await handler(ev("/platform/index.html"));
  assert.equal(r.status, "302");
  assert.match(locationOf(r), /^https:\/\/us-east-1mkrwfqtkg\.auth\.us-east-1\.amazoncognito\.com\/oauth2\/authorize\?/);
  assert.match(locationOf(r), /code_challenge_method=S256/, "PKCE must be used");
  assert.ok(cookiesOf(r).some((c) => c.startsWith("__Host-fcf_pkce=")));
});

// ---------------------------------------------------------------- token forgery

const FORGERIES = [
  ["expired an hour ago", () => idToken({ exp: Math.floor(Date.now() / 1000) - 3600 })],
  ["audience is a different app client", () => idToken({ aud: "someotherclientid00000000x" })],
  ["issuer is a different user pool", () => idToken({ iss: "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_someOther" })],
  ["an ACCESS token, not an id token", () => idToken({ token_use: "access" })],
  ["alg: none with no signature", () => idToken({}, { alg: "none" })],
  ["signed by a key that is not the pool's", () => idToken({}, { key: FOREIGN.privateKey })],
  ["unknown kid", () => idToken({}, { kid: "not-a-real-kid" })],
  ["right email, wrong sub", () => idToken({ sub: "00000000-0000-0000-0000-000000000000" })],
  ["right sub, wrong email", () => idToken({ email: "someone-else@example.com" })],
  ["no email claim at all", () => idToken({ email: undefined })],
  ["not a JWT at all", () => "garbage"],
  ["only two segments", () => "aaa.bbb"],
  ["empty string", () => ""],
];

for (const [name, make] of FORGERIES) {
  test(`DENIED: ${name}`, async () => {
    const r = await handler(ev("/platform/index.html", { cookies: [session(make())] }));
    assert.ok(!isAllow(r), `${name} must NOT reach the origin`);
    assert.equal(r.status, "302", "denial should restart the sign-in flow");
  });
}

test("DENIED: payload tampered after signing (signature covers the payload)", async () => {
  const good = idToken();
  const [h, , s] = good.split(".");
  const forged = Buffer.from(JSON.stringify({
    iss: ISSUER, aud: CLIENT_ID, token_use: "id", sub: GRANTED_SUB,
    email: GRANTED_EMAIL, exp: Math.floor(Date.now() / 1000) + 99999,
  })).toString("base64url");
  const r = await handler(ev("/platform/index.html", { cookies: [session(`${h}.${forged}.${s}`)] }));
  assert.ok(!isAllow(r), "a re-encoded payload must invalidate the signature");
});

test("DENIED: two session cookies (shadowing) is refused, not resolved", async () => {
  const r = await handler(ev("/platform/index.html", {
    cookies: [`__Host-fcf_session=${idToken()}`, "__Host-fcf_session=attacker-supplied"],
  }));
  assert.ok(!isAllow(r), "a duplicated session cookie must fail closed, not pick a winner");
});

// ---------------------------------------------------------------- fail closed

test("JWKS unreachable -> DENY, never allow", async () => {
  // Force a cold cache so the failure is actually exercised.
  const mod = await import(`${pathToFileURL(MODULE).href}?nocache=${Math.random()}`);
  jwksDown = true;
  try {
    const r = await mod.handler(ev("/platform/index.html", { cookies: [session(idToken())] }));
    assert.ok(!isAllow(r), "a network failure must lock the door, not open it");
  } finally {
    jwksDown = false;
  }
});

// ---------------------------------------------------------------- routing

test("/platform redirects to /platform/ (relative assets would otherwise break)", async () => {
  const r = await handler(ev("/platform"));
  assert.equal(r.status, "302");
  assert.equal(locationOf(r), "/platform/");
});

test("a directory URI is rewritten to a real S3 key, for authorised callers only", async () => {
  const r = await handler(ev("/platform/", { cookies: [session(idToken())] }));
  assert.ok(isAllow(r));
  assert.equal(r.uri, "/platform/index.html");
});

test("the signed-out page is public by design and grants nothing", async () => {
  const r = await handler(ev("/platform/_auth/signed-out"));
  assert.equal(r.status, "200");
  assert.ok(!isAllow(r), "it is a generated page, never a pass-through to the origin");
  assert.ok(cookiesOf(r).some((c) => c.startsWith("__Host-fcf_session=") && c.includes("Max-Age=0")),
    "it must actively clear the session");
});

test("a provenance deep link survives the sign-in round trip", async () => {
  const r = await handler(ev("/platform/index.html", { qs: "number=PWC003|2036|base|starter_ports" }));
  const stash = cookiesOf(r).find((c) => c.startsWith("__Host-fcf_pkce="));
  const value = stash.split("=")[1].split(";")[0];
  const saved = JSON.parse(Buffer.from(value, "base64url").toString("utf8"));
  assert.equal(saved.p, "/platform/index.html");
  assert.equal(saved.q, "number=PWC003|2036|base|starter_ports");
});

// ---------------------------------------------------------------- cookie hygiene

test("every cookie satisfies the __Host- prefix rules a browser enforces", async () => {
  const r = await handler(ev("/platform/index.html"));
  assert.ok(cookiesOf(r).length > 0);
  for (const cookie of cookiesOf(r)) {
    assert.match(cookie, /^__Host-/, `${cookie} must carry the __Host- prefix`);
    assert.match(cookie, /HttpOnly/, cookie);
    assert.match(cookie, /Secure/, cookie);
    assert.match(cookie, /SameSite=Lax/, cookie);
    // A browser REJECTS a __Host- cookie unless Path=/ and there is no Domain. Getting either
    // wrong means the cookie is silently dropped and sign-in loops forever.
    assert.match(cookie, /Path=\//, cookie);
    assert.ok(!/Path=\/platform/.test(cookie), `${cookie}: __Host- requires exactly Path=/`);
    assert.ok(!/Domain=/i.test(cookie), `${cookie}: __Host- forbids a Domain attribute`);
  }
});

test("a sibling subdomain cannot shadow the session (this is what __Host- buys)", () => {
  // Not assertable from inside the handler — it is a browser rule. Pinned here so that
  // renaming the cookies without the prefix is a test failure rather than a silent
  // reintroduction of the permanent-lockout attack.
  for (const name of ["__Host-fcf_session", "__Host-fcf_pkce"]) {
    assert.match(name, /^__Host-/);
  }
});

test("SameSite is Lax, not Strict — Strict would break the Cognito callback", async () => {
  const r = await handler(ev("/platform/index.html"));
  assert.ok(!cookiesOf(r).some((c) => /SameSite=Strict/.test(c)));
});

// ---------------------------------------------------------------- the callback

/** Craft the (unauthenticated) PKCE stash the way an attacker could. */
const stashCookie = (obj) =>
  `__Host-fcf_pkce=${Buffer.from(JSON.stringify(obj), "utf8").toString("base64url")}`;

test("callback: a state that does not match the browser's cookie is refused", async () => {
  const r = await handler(ev("/platform/_auth/callback", {
    qs: "code=abc&state=attacker-chosen",
    cookies: [stashCookie({ v: "verifier", n: "the-real-nonce", p: "/platform/", q: "" })],
  }));
  assert.equal(r.status, "403");
});

test("callback: no stash cookie restarts the flow rather than erroring", async () => {
  const r = await handler(ev("/platform/_auth/callback", { qs: "code=abc&state=xyz" }));
  assert.equal(r.status, "302");
  assert.match(locationOf(r), /oauth2\/authorize/);
});

const OPEN_REDIRECTS = [
  "//evil.example.com/",
  "https://evil.example.com/",
  "/platform/../../secrets",
  "/etc/passwd",
  "/t/FFX001",
  "/platform/\r\nSet-Cookie: x=y",
  "/platform//evil.example.com",
];

for (const hostile of OPEN_REDIRECTS) {
  test(`callback: return target ${JSON.stringify(hostile)} cannot escape /platform`, async () => {
    tokenPayload = { id_token: idToken() };
    const r = await handler(ev("/platform/_auth/callback", {
      qs: "code=abc&state=nonce-1",
      cookies: [stashCookie({ v: "verifier", n: "nonce-1", p: hostile, q: "" })],
    }));
    assert.equal(r.status, "302");
    const to = locationOf(r);
    assert.ok(to.startsWith("/platform"), `redirected to ${to}`);
    assert.ok(!to.startsWith("//"), "protocol-relative redirect");
    assert.ok(!/[\r\n]/.test(to), "CR/LF in a Location header");
    assert.ok(!to.includes("evil.example.com"), `off-site redirect to ${to}`);
  });
}

test("callback: a signed-in but NOT granted account gets a clear 403, not access", async () => {
  tokenPayload = { id_token: idToken({ sub: "11111111-1111-1111-1111-111111111111", email: "stranger@example.com" }) };
  const r = await handler(ev("/platform/_auth/callback", {
    qs: "code=abc&state=nonce-2",
    cookies: [stashCookie({ v: "v", n: "nonce-2", p: "/platform/", q: "" })],
  }));
  assert.equal(r.status, "403");
  assert.match(r.body, /does not have access/);
  assert.ok(!cookiesOf(r).some((c) => c.startsWith("__Host-fcf_session=") && !c.includes("Max-Age=0")),
    "a refused account must not be handed a session");
});

test("callback: a granted account is handed a session and sent to its target", async () => {
  tokenPayload = { id_token: idToken() };
  const r = await handler(ev("/platform/_auth/callback", {
    qs: "code=abc&state=nonce-3",
    cookies: [stashCookie({ v: "v", n: "nonce-3", p: "/platform/index.html", q: "number=FFX001|2026|base|starter_ports" })],
  }));
  assert.equal(r.status, "302");
  assert.equal(locationOf(r), "/platform/index.html?number=FFX001|2026|base|starter_ports");
  assert.ok(cookiesOf(r).some((c) => c.startsWith("__Host-fcf_session=") && c.includes("HttpOnly")));
});

test("callback: token endpoint failure denies and grants nothing", async () => {
  tokenHttpOk = false;
  try {
    const r = await handler(ev("/platform/_auth/callback", {
      qs: "code=abc&state=nonce-4",
      cookies: [stashCookie({ v: "v", n: "nonce-4", p: "/platform/", q: "" })],
    }));
    assert.equal(r.status, "502");
    assert.ok(!cookiesOf(r).some((c) => c.startsWith("__Host-fcf_session=") && !c.includes("Max-Age=0")));
  } finally {
    tokenHttpOk = true;
  }
});

// ---------------------------------------------------------------- injection

test("Cognito's error parameter is escaped, not reflected", async () => {
  const payload = '<img src=x onerror=alert(1)>';
  const r = await handler(ev("/platform/_auth/callback", {
    qs: `error=${encodeURIComponent(payload)}`,
  }));
  assert.equal(r.status, "403");
  assert.ok(!r.body.includes("<img"), "reflected XSS: the error parameter reached the DOM raw");
  assert.ok(r.body.includes("&lt;img"), "it should appear escaped");
});

test("an unrecognised account's email is escaped in the refusal page", async () => {
  tokenPayload = { id_token: idToken({ sub: "22222222-2222-2222-2222-222222222222", email: '<script>alert(1)</script>' }) };
  const r = await handler(ev("/platform/_auth/callback", {
    qs: "code=abc&state=nonce-5",
    cookies: [stashCookie({ v: "v", n: "nonce-5", p: "/platform/", q: "" })],
  }));
  assert.ok(!r.body.includes("<script>alert"), "email reflected into HTML unescaped");
});

// ---------------------------------------------------------------- caching

test("generated responses are never cacheable", async () => {
  for (const uri of ["/platform/index.html", "/platform/_auth/signed-out", "/platform"]) {
    const r = await handler(ev(uri));
    const cc = r.headers["cache-control"]?.[0]?.value || "";
    assert.match(cc, /no-store/, `${uri} must not be cacheable — it carries per-user state`);
  }
});

// ---------------------------------------------------------------- the NFC guarantee

test("the authoriser is only ever reasoned about for /platform paths", async () => {
  // The real guarantee is the CloudFront path pattern, asserted in the deploy script's
  // verification. This test pins the assumption the code makes, so that if someone ever
  // attaches this function to the default behaviour the NFC breakage is at least loud.
  const source = await import("node:fs").then((fs) => fs.readFileSync(MODULE, "utf8"));
  assert.match(source, /const PREFIX = "\/platform"/);
  const r = await handler(ev("/t/FFX001"));
  assert.ok(!isAllow(r),
    "attached to the wrong behaviour this WOULD gate the NFC tags — the deploy script must " +
    "scope it to /platform*, and does");
});

// ---------------------------------------------------------------- forced sign-out

/** A CloudFront event with a Sec-Fetch-Dest header, as a real browser sends. */
function evFetchDest(uri, dest) {
  const e = ev(uri);
  e.Records[0].cf.request.headers["sec-fetch-dest"] = [{ key: "Sec-Fetch-Dest", value: dest }];
  return e;
}

for (const path of ["/platform/_auth/logout", "/platform/_auth/signed-out"]) {
  test(`${path} cannot be triggered from a third-party <img>`, async () => {
    const r = await handler(evFetchDest(path, "image"));
    assert.equal(r.status, "403");
    assert.equal(cookiesOf(r).length, 0,
      "a forged subresource request must not clear the session");
  });

  test(`${path} still works as a real navigation`, async () => {
    const r = await handler(evFetchDest(path, "document"));
    assert.ok(["200", "302"].includes(r.status));
    assert.ok(cookiesOf(r).some((c) => c.includes("Max-Age=0")),
      "a genuine sign-out must clear the session");
  });
}

test("a client that sends no Sec-Fetch-Dest is not blocked (curl is not a forgery risk)", async () => {
  const r = await handler(ev("/platform/_auth/signed-out"));
  assert.equal(r.status, "200");
});

// ---------------------------------------------------------------- the second granted account

test("the second granted account also reaches the origin", async () => {
  const r = await handler(ev("/platform/index.html", {
    cookies: [session(idToken({ sub: GRANTED2_SUB, email: GRANTED2_EMAIL }))],
  }));
  assert.ok(isAllow(r), "redacted-6@example.org is on the allowlist and must pass");
});

test("DENIED: one account's sub paired with the other's email", async () => {
  // The allowlist requires both fields to match the SAME entry. Checking them independently
  // ("is this sub known?" and "is this email known?") would let a token that mixes two real
  // accounts through — and with two entries that stops being hypothetical.
  for (const [sub, email] of [[GRANTED_SUB, GRANTED2_EMAIL], [GRANTED2_SUB, GRANTED_EMAIL]]) {
    const r = await handler(ev("/platform/index.html", { cookies: [session(idToken({ sub, email }))] }));
    assert.ok(!isAllow(r), `sub ${sub.slice(0, 8)} + ${email} must be refused`);
  }
});

test("DENIED: a third pool member who is not on the allowlist", async () => {
  // redacted-1@example.org exists in the same Cognito pool. Being able to authenticate is not the
  // same as being granted, and the gate must keep those separate.
  const r = await handler(ev("/platform/index.html", {
    cookies: [session(idToken({ sub: "00000000-0000-4000-8000-000000000008", email: "redacted-1@example.org" }))],
  }));
  assert.ok(!isAllow(r), "a valid pool member who is not allowlisted must still be refused");
});

test("email_verified is deliberately NOT required (the granted account lacks it)", async () => {
  // Requiring it would have produced a gate that could never open. Pinned so a well-meaning
  // 'hardening' change fails loudly rather than locking the owner out.
  const r = await handler(ev("/platform/index.html", {
    cookies: [session(idToken({ email_verified: undefined }))],
  }));
  assert.ok(isAllow(r), "a token with no email_verified claim must still be accepted");
});
