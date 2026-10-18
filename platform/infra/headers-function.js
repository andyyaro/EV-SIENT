// CloudFront Function "evsient-app-headers" (runtime cloudfront-js-2.0, viewer-response).
// Sets the security headers on every response from the EV-SIENT Planner distribution.
//
// A Function is used instead of a custom response headers policy because CloudFront's
// flat-rate pricing plans allow only AWS-managed policies, while Functions are included.
//
// The Content-Security-Policy lives ONLY in the CSP list below. To widen it (for example a
// new tile host), edit the matching directive, then run the steps in platform/infra/README.md
// ("Changing the CSP"): update-function, test-function, publish-function.

var CSP = [
  "default-src 'self'",
  "script-src 'self' 'wasm-unsafe-eval'",
  "worker-src 'self'",
  "connect-src 'self' https://tiles.openfreemap.org",
  "img-src 'self' data: blob: https://tiles.openfreemap.org",
  "style-src 'self' 'unsafe-inline'",
  "font-src 'self'",
  "object-src 'none'",
  "base-uri 'none'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  "upgrade-insecure-requests"
].join('; ');

var HEADERS = {
  'content-security-policy': CSP,
  'strict-transport-security': 'max-age=31536000',
  'x-content-type-options': 'nosniff',
  'referrer-policy': 'no-referrer',
  'permissions-policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
  'cross-origin-opener-policy': 'same-origin',
  'x-robots-tag': 'noindex, nofollow'
};

function handler(event) {
  var response = event.response;
  var headers = response.headers;
  for (var name in HEADERS) {
    headers[name] = { value: HEADERS[name] };
  }
  return response;
}
