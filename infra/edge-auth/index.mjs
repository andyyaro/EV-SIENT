/**
 * Lambda@Edge viewer-request authoriser for /platform*.
 *
 * Why this exists at the edge rather than in the page
 * ---------------------------------------------------
 * The platform is a *static bundle*. Its bytes are the asset - there is no server behind it
 * that could enforce anything. A browser-side sign-in over static files cannot protect them;
 * it can only hide what CloudFront has already delivered. Viewer-request runs on every
 * request **before the cache is consulted**, so an unauthenticated caller never receives a
 * byte, cached or not. That is the one property this design needs. (DEC-017.)
 *
 * Why there is no secret in this file
 * -----------------------------------
 * Lambda@Edge cannot use environment variables, so any secret would have to be baked into the
 * deployed bundle - which the program's standing rules forbid outright. So the design removes
 * the secret rather than hiding it:
 *
 *   * the Cognito app client is **public** and the flow uses **PKCE**, so no client secret
 *     exists to store;
 *   * the session cookie holds the Cognito `id_token`, verified on each request against the
 *     pool's **public** JWKS.
 *
 * Every constant below is a public identifier - a user-pool id, a public app-client id, a
 * hosted-UI hostname. None is a credential. There is no AWS account id or ARN here,
 * deliberately, and no person: who may enter is read from `granted.mjs` (see `GRANTED`).
 *
 * Fail-closed, everywhere
 * -----------------------
 * Every path that cannot positively establish "this is the granted user" denies. That
 * includes the boring failures: JWKS unreachable, token endpoint down, a malformed cookie, a
 * duplicated cookie. A transient network blip therefore locks the page rather than opening
 * it. For a private planning page that is the correct trade, and it matches the fail-closed
 * capacity guard the rest of this project already runs on.
 *
 * Node 22 (Lambda@Edge's newest runtime), zero dependencies - `node:crypto` and global
 * `fetch` only. Nothing here needs `npm install`, so there is no lockfile to drift and no
 * transitive dependency inside a security boundary.
 */

import { createHash, createPublicKey, createVerify, randomBytes, timingSafeEqual } from "node:crypto";
import { GRANTED } from "./granted.mjs";

// ---------------------------------------------------------------- configuration (public)

const REGION = "us-east-1";
const USER_POOL_ID = "us-east-1_mKrwfQTkg";
const CLIENT_ID = "1b9ab91m46pr3m2n74qapq3ls5";        // public client, no secret
const HOSTED_UI = "https://us-east-1mkrwfqtkg.auth.us-east-1.amazoncognito.com";
const SITE = "https://futurecityfellowship.andyyaro.com";

const ISSUER = `https://cognito-idp.${REGION}.amazonaws.com/${USER_POOL_ID}`;
const JWKS_URL = `${ISSUER}/.well-known/jwks.json`;
const TOKEN_URL = `${HOSTED_UI}/oauth2/token`;

const PREFIX = "/platform";
const CALLBACK_PATH = `${PREFIX}/_auth/callback`;
const LOGOUT_PATH = `${PREFIX}/_auth/logout`;
const SIGNED_OUT_PATH = `${PREFIX}/_auth/signed-out`;
const CALLBACK_URL = `${SITE}${CALLBACK_PATH}`;
const LANDING = `${PREFIX}/index.html`;

/**
 * Cookie names carry the `__Host-` prefix, which is load-bearing rather than decorative.
 *
 * A browser will only accept a `__Host-` cookie when it is `Secure`, has `Path=/`, and has
 * **no `Domain` attribute** - which means it can be set only by this exact host. A sibling
 * host under `andyyaro.com` therefore cannot write one, and that closes a real attack:
 * without the prefix, any other subdomain could set a second `fcf_session` for the parent
 * domain, and since duplicate cookies are refused (see `oneCookie`, which fails closed) that
 * would be a permanent lockout the platform could not clear. The same prefix also blocks
 * planting a forged PKCE stash to force a sign-in into someone else's account.
 *
 * The cost of `__Host-` is `Path=/`: the cookie rides along on requests to the public NFC
 * pages too, rather than being scoped to `/platform`. That is acceptable - the cache policy
 * does not forward cookies to the origin, so they are never seen by S3 or written to its logs,
 * and `HttpOnly` keeps them away from page scripts. A narrower path that a sibling host can
 * poison is the worse trade.
 */
const SESSION_COOKIE = "__Host-fcf_session";
const PKCE_COOKIE = "__Host-fcf_pkce";
const COOKIE_ATTRS = "Path=/; HttpOnly; Secure; SameSite=Lax";

/**
 * Who may read the platform: `GRANTED`, imported above from `granted.mjs`.
 *
 * Matched on **`sub`** - Cognito's immutable per-user identifier, the tightest available
 * expression of "that user specifically" - *and* on `email`, which in this pool is also the
 * username and therefore unique.
 *
 * `email_verified` is deliberately NOT required, and that is not an oversight. This user was
 * created administratively and carries no `email_verified` attribute at all (`admin-get-user`
 * returns only `email` and `sub`). The textbook check would therefore have produced a gate
 * that could never open for the one account it exists to admit - a failure invisible from the
 * deploying side, because confirming it needs that user's password. Matching on the immutable
 * `sub` is strictly stronger than an `email_verified` flag anyway.
 *
 * **The list is not in this file.** It lives in `granted.mjs`, beside this file and NOT
 * tracked. Until 2026-10-17 it was inline here, which put two people's login emails and
 * Cognito ids in every clone of the repository. `granted.mjs.example` shows the shape; emails
 * are compared lower-cased, so they must be written that way. The second entry was added at
 * the owner's request after the first deployment: the first account carries no
 * `email_verified`, so "Forgot your password?" cannot deliver to it, and granting an account
 * whose credentials the owner already holds did not require the assistant to touch a password.
 *
 * Fail-closed holds without the file, by construction rather than by a fallback: a checkout
 * with no `granted.mjs` cannot load this module at all, so every request errors before it can
 * reach the origin, and `scripts/deploy_platform.py` refuses to package the function without
 * a well-formed list. A fallback to an empty list would also deny everyone, but quietly, as
 * an "account not granted" page that looks like a permissions problem instead of a missing file.
 */

// ---------------------------------------------------------------- small helpers

const b64uEncode = (buf) => Buffer.from(buf).toString("base64url");
const b64uDecode = (str) => Buffer.from(str, "base64url");

/**
 * Parse cookies into name -> list-of-values.
 *
 * Values are collected as a LIST rather than collapsed, so a duplicated cookie can be
 * detected. A request carrying two `fcf_session` cookies is anomalous - it is what cookie
 * shadowing looks like - and `oneCookie` refuses it rather than picking a winner. Picking
 * either "first" or "last" would be choosing an attacker's preferred semantics at random.
 */
function parseCookies(headers) {
  const jar = Object.create(null);
  for (const header of headers.cookie || []) {
    for (const part of String(header.value).split(";")) {
      const eq = part.indexOf("=");
      if (eq < 0) continue;
      const name = part.slice(0, eq).trim();
      const value = part.slice(eq + 1).trim();
      if (!name) continue;
      (jar[name] ||= []).push(value);
    }
  }
  return jar;
}

/** The single value of a cookie, or null if absent OR duplicated. Fail closed. */
function oneCookie(jar, name) {
  const values = jar[name];
  return values && values.length === 1 ? values[0] : null;
}

/** Constant-time string compare, for the values where a timing oracle would matter. */
function sameSecret(a, b) {
  const left = Buffer.from(String(a ?? ""), "utf8");
  const right = Buffer.from(String(b ?? ""), "utf8");
  if (left.length !== right.length || left.length === 0) return false;
  return timingSafeEqual(left, right);
}

/**
 * Paths and queries that may be reflected into a `Location` header.
 *
 * Deliberately an allowlist of characters rather than a denylist of bad ones. Neither pattern
 * can match CR or LF, so header injection is impossible; neither can match `:` or a leading
 * `//`, so a protocol-relative open redirect to another host is impossible.
 *
 * The query pattern is permissive enough for the platform's provenance deep links, which look
 * like `?number=PWC003|2036|base|starter_ports`.
 */
const SAFE_PATH = /^\/platform(?:\/[A-Za-z0-9._~\-\/]*)?$/;
const SAFE_QUERY = /^[A-Za-z0-9._~\-=&%|+,]*$/;

function safeTarget(path, query) {
  let outPath = LANDING;
  if (typeof path === "string" && path.length <= 512 && SAFE_PATH.test(path)
      && !path.includes("//") && !path.includes("..")) {
    outPath = path;
  }
  const outQuery = (typeof query === "string" && query.length <= 256 && SAFE_QUERY.test(query))
    ? query : "";
  return outQuery ? `${outPath}?${outQuery}` : outPath;
}

// ---------------------------------------------------------------- responses

const NO_STORE = "no-store, no-cache, must-revalidate, private";

/**
 * Escape before interpolating ANYTHING into a response body.
 *
 * Not optional politeness. The first draft of this file interpolated Cognito's `error` query
 * parameter raw - an attacker-controlled value straight off the URL - which is reflected XSS
 * on this site's own origin. Escaping is centralised here so no call site has to remember.
 */
const escapeHtml = (s) => String(s).replace(/[&<>"']/g, (c) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
}[c]));

function redirect(location, setCookies = []) {
  const headers = {
    location: [{ key: "Location", value: location }],
    "cache-control": [{ key: "Cache-Control", value: NO_STORE }],
  };
  if (setCookies.length) {
    headers["set-cookie"] = setCookies.map((value) => ({ key: "Set-Cookie", value }));
  }
  return { status: "302", statusDescription: "Found", headers };
}

/**
 * A refusal that says what happened.
 *
 * "Access denied" with no reason is exactly the dead end the owner already hit once on the NFC
 * tags, and this project's whole posture is that an unexplained state is a defect. So a denial
 * names the account it saw and what to do next. It leaks nothing: the reader had to complete a
 * Cognito sign-in to reach this page at all, so they already know who they are.
 */
function refuse(status, title, detail, setCookies = []) {
  const body = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(title)}</title>
<style>body{margin:0;background:#F5F0E6;color:#1a1a1a;font:17px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.w{max-width:34rem;margin:0 auto;padding:3.5rem 1.15rem}h1{color:#1B4332;font-size:1.4rem;margin:0 0 .6rem}
p{margin:0 0 .9rem}.m{color:#4a4a4a;font-size:.92rem}
a{color:#1B4332}code{background:rgba(127,127,127,.13);padding:.1em .35em;border-radius:3px;font-size:.9em}
@media(prefers-color-scheme:dark){body{background:#16191a;color:#ececec}h1{color:#7fbf9a}.m{color:#b4b4b4}a{color:#7fbf9a}}
</style></head><body><div class="w"><h1>${escapeHtml(title)}</h1>${detail}
<p class="m">Future City Fellowship - EV charging site readiness. This is a private planning
platform. The public field pages reached by tapping an NFC tag are unaffected and need no
account.</p></div></body></html>`;
  const headers = {
    "content-type": [{ key: "Content-Type", value: "text/html; charset=utf-8" }],
    "cache-control": [{ key: "Cache-Control", value: NO_STORE }],
    "x-content-type-options": [{ key: "X-Content-Type-Options", value: "nosniff" }],
  };
  if (setCookies.length) {
    headers["set-cookie"] = setCookies.map((value) => ({ key: "Set-Cookie", value }));
  }
  return { status: String(status), statusDescription: title, headers, body };
}

const expireCookie = (name) => `${name}=; ${COOKIE_ATTRS}; Max-Age=0`;

/**
 * Is this a real top-level navigation, rather than a subresource load?
 *
 * Signing out clears cookies, so it changes state - which makes a bare `GET /…/logout`
 * forgeable: any page the signed-in user visits can embed
 * `<img src="https://…/platform/_auth/logout">` and the `Set-Cookie: Max-Age=0` headers still
 * apply, logging them out. `SameSite=Lax` does not help, because the attack does not need the
 * victim's cookie to be *sent* - only the response's cookie to be *stored*.
 *
 * The impact is nuisance rather than breach, so the defence is proportionate: browsers label
 * subresource requests with `Sec-Fetch-Dest`, and only `document` is a navigation. A client
 * that sends no such header (curl, the test suite) is not a browser and has nothing to forge
 * on someone's behalf, so it is allowed through rather than blocked.
 */
function isTopLevelNavigation(headers) {
  const dest = headers["sec-fetch-dest"]?.[0]?.value;
  return !dest || dest === "document";
}

// ---------------------------------------------------------------- token verification

let jwksCache = null;
let jwksFetchedAt = 0;
const JWKS_TTL_MS = 10 * 60 * 1000;

async function fetchJwks() {
  const res = await fetch(JWKS_URL, { signal: AbortSignal.timeout(2500) });
  if (!res.ok) throw new Error(`jwks http ${res.status}`);
  const body = await res.json();
  if (!body || !Array.isArray(body.keys)) throw new Error("jwks malformed");
  jwksCache = body;
  jwksFetchedAt = Date.now();
  return body;
}

/** The JWK for a key id, refetching once if the kid is unknown (Cognito rotates keys). */
async function jwkFor(kid) {
  if (!jwksCache || Date.now() - jwksFetchedAt > JWKS_TTL_MS) await fetchJwks();
  let key = jwksCache.keys.find((k) => k.kid === kid);
  if (!key && Date.now() - jwksFetchedAt > 30_000) {
    await fetchJwks();
    key = jwksCache.keys.find((k) => k.kid === kid);
  }
  return key || null;
}

/**
 * Verify a Cognito id_token. Returns its claims, or null - never throws a decision.
 *
 * The checks are ordered so that nothing derived from the token is trusted before the
 * signature over it is proven:
 *
 *   * `alg` must be exactly `RS256`. This rejects `none`, and it rejects the HS256 confusion
 *     attack where a forger signs with the *public* key as an HMAC secret - impossible here
 *     anyway, since verification only ever uses `createVerify` with an RSA public key.
 *   * `token_use` must be `id`. Without this, an **access token** for the same pool would be
 *     accepted as proof of identity; access tokens carry no verified `email`, so the allowlist
 *     would be comparing against `undefined`.
 *   * `aud` must be this app client, and `iss` this pool - so a token minted for a different
 *     client in the same account is not currency here.
 */
async function verifyIdToken(jwt) {
  if (typeof jwt !== "string") return null;
  const parts = jwt.split(".");
  if (parts.length !== 3) return null;

  let header, claims;
  try {
    header = JSON.parse(b64uDecode(parts[0]).toString("utf8"));
    claims = JSON.parse(b64uDecode(parts[1]).toString("utf8"));
  } catch {
    return null;
  }
  if (!header || header.alg !== "RS256" || typeof header.kid !== "string") return null;

  let jwk;
  try {
    jwk = await jwkFor(header.kid);
  } catch {
    return null;                       // JWKS unreachable -> deny, never allow
  }
  if (!jwk || jwk.kty !== "RSA" || (jwk.alg && jwk.alg !== "RS256")) return null;

  let verified = false;
  try {
    const key = createPublicKey({ key: jwk, format: "jwk" });
    const verifier = createVerify("RSA-SHA256");
    verifier.update(`${parts[0]}.${parts[1]}`);
    verifier.end();
    verified = verifier.verify(key, b64uDecode(parts[2]));
  } catch {
    return null;
  }
  if (!verified) return null;

  if (claims.iss !== ISSUER) return null;
  if (claims.token_use !== "id") return null;
  if (claims.aud !== CLIENT_ID) return null;

  const now = Math.floor(Date.now() / 1000);
  if (typeof claims.exp !== "number" || claims.exp <= now) return null;
  if (typeof claims.iat === "number" && claims.iat > now + 300) return null;

  return claims;
}

/** Is this verified identity on the allowlist? Both fields must match. */
function isGranted(claims) {
  const sub = String(claims.sub ?? "");
  const email = String(claims.email ?? "").trim().toLowerCase();
  if (!sub || !email) return false;
  return GRANTED.some((g) => g.sub === sub && g.email === email);
}

// ---------------------------------------------------------------- the flow

/** Begin PKCE: stash verifier + return target in a short-lived cookie, bounce to Cognito. */
function startLogin(path, query) {
  const verifier = b64uEncode(randomBytes(32));
  const challenge = b64uEncode(createHash("sha256").update(verifier).digest());
  const nonce = b64uEncode(randomBytes(24));

  // The return target rides in our own HttpOnly cookie, NOT in the `state` parameter. `state`
  // is an opaque nonce and nothing else, so there is no attacker-supplied path anywhere in the
  // URL for an open redirect to hide in. safeTarget() still re-validates on the way out.
  const stash = b64uEncode(Buffer.from(JSON.stringify({
    v: verifier, n: nonce, p: path, q: query,
  }), "utf8"));

  const authorize = `${HOSTED_UI}/oauth2/authorize`
    + `?client_id=${encodeURIComponent(CLIENT_ID)}`
    + `&response_type=code`
    + `&scope=${encodeURIComponent("openid email")}`
    + `&redirect_uri=${encodeURIComponent(CALLBACK_URL)}`
    + `&code_challenge_method=S256`
    + `&code_challenge=${encodeURIComponent(challenge)}`
    + `&state=${encodeURIComponent(nonce)}`;

  return redirect(authorize, [`${PKCE_COOKIE}=${stash}; ${COOKIE_ATTRS}; Max-Age=600`]);
}

async function handleCallback(query, jar) {
  if (query.get("error")) {
    return refuse(403, "Sign-in was not completed",
      `<p>Cognito reported <code>${escapeHtml(String(query.get("error")).slice(0, 60))}</code>.</p>
       <p><a href="${LANDING}">Try again</a></p>`,
      [expireCookie(PKCE_COOKIE)]);
  }

  const code = query.get("code");
  const state = query.get("state");
  const stash = oneCookie(jar, PKCE_COOKIE);
  // No stash means the 10-minute window lapsed or the cookie was dropped. Restart cleanly
  // rather than erroring - the user did nothing wrong.
  if (!code || !state || !stash) return startLogin(LANDING, "");

  let saved;
  try {
    saved = JSON.parse(b64uDecode(stash).toString("utf8"));
  } catch {
    return startLogin(LANDING, "");
  }
  if (!saved || typeof saved.v !== "string" || typeof saved.n !== "string") {
    return startLogin(LANDING, "");
  }
  // Binds this callback to the browser that began the sign-in: a forged or replayed callback
  // carries a state that will not match this browser's cookie.
  if (!sameSecret(saved.n, state)) {
    return refuse(403, "Sign-in could not be verified",
      `<p>The sign-in response did not match the request that started it.</p>
       <p><a href="${LANDING}">Start again</a></p>`,
      [expireCookie(PKCE_COOKIE)]);
  }

  let tokens;
  try {
    const res = await fetch(TOKEN_URL, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "authorization_code",
        client_id: CLIENT_ID,
        code,
        redirect_uri: CALLBACK_URL,
        code_verifier: saved.v,
      }),
      signal: AbortSignal.timeout(4000),
    });
    if (!res.ok) throw new Error(`token http ${res.status}`);
    tokens = await res.json();
  } catch {
    return refuse(502, "Could not reach the sign-in service",
      `<p>The token exchange with Cognito failed. Nothing was granted.</p>
       <p><a href="${LANDING}">Try again</a></p>`,
      [expireCookie(PKCE_COOKIE)]);
  }

  const claims = await verifyIdToken(tokens.id_token);
  if (!claims) {
    return refuse(403, "Sign-in could not be verified",
      `<p>The identity token did not verify against this user pool.</p>`,
      [expireCookie(PKCE_COOKIE)]);
  }
  if (!isGranted(claims)) {
    const who = String(claims.email ?? "an unrecognised account").slice(0, 80);
    return refuse(403, "That account does not have access",
      `<p>You signed in successfully as
        <code>${escapeHtml(who)}</code>, but that account is not on the access list
        for this platform.</p>
       <p class="m">Access is granted per account by the project owner. Signing in again with
       the same account will produce this same page.</p>
       <p><a href="${LOGOUT_PATH}">Sign out</a></p>`,
      [expireCookie(PKCE_COOKIE)]);
  }

  const ttl = Math.max(60, Math.min(3600, claims.exp - Math.floor(Date.now() / 1000)));
  return redirect(safeTarget(saved.p, saved.q), [
    `${SESSION_COOKIE}=${tokens.id_token}; ${COOKIE_ATTRS}; Max-Age=${ttl}`,
    expireCookie(PKCE_COOKIE),
  ]);
}

// ---------------------------------------------------------------- entry point

export const handler = async (event) => {
  const request = event.Records[0].cf.request;
  const uri = request.uri;
  const query = new URLSearchParams(request.querystring || "");
  const jar = parseCookies(request.headers || {});

  // Signing out clears cookies, so both of these routes change state and must not be
  // triggerable from a third-party page's <img>/<iframe>. See isTopLevelNavigation.
  if (uri === SIGNED_OUT_PATH || uri === LOGOUT_PATH) {
    if (!isTopLevelNavigation(request.headers || {})) {
      return refuse(403, "Sign-out must be a navigation",
        `<p>This address signs you out, so it only works when you go to it directly.</p>`);
    }
  }

  // Public, and intentionally so: the page you land on after signing out.
  if (uri === SIGNED_OUT_PATH) {
    return refuse(200, "Signed out",
      `<p>You are signed out of the planning platform.</p>
       <p><a href="${LANDING}">Sign in again</a></p>`,
      [expireCookie(SESSION_COOKIE), expireCookie(PKCE_COOKIE)]);
  }

  if (uri === LOGOUT_PATH) {
    const url = `${HOSTED_UI}/logout?client_id=${encodeURIComponent(CLIENT_ID)}`
      + `&logout_uri=${encodeURIComponent(`${SITE}${SIGNED_OUT_PATH}`)}`;
    return redirect(url, [expireCookie(SESSION_COOKIE), expireCookie(PKCE_COOKIE)]);
  }

  if (uri === CALLBACK_PATH) return handleCallback(query, jar);

  // `/platform` -> `/platform/` so relative asset URLs in index.html resolve correctly.
  if (uri === PREFIX) return redirect(`${PREFIX}/`);

  const session = oneCookie(jar, SESSION_COOKIE);
  if (session) {
    const claims = await verifyIdToken(session);
    if (claims && isGranted(claims)) {
      // Authorised. Rewrite directory-style URIs to a real S3 key, then pass to the origin.
      if (request.uri.endsWith("/")) request.uri += "index.html";
      return request;
    }
  }

  // Not signed in, expired, or not granted -> start the flow, remembering where they wanted
  // to go so a provenance deep link survives the round trip.
  return startLogin(uri, request.querystring || "");
};
