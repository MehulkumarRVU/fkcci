# Frontend UI Restoration Report

Assessment date: 2026-11-09. The retained `pocketcoach-check` deployment and
its PostgreSQL volume were not restarted, rebuilt, replaced, or otherwise
operated on. The restored UI was verified in a separate Compose project at
`http://127.0.0.1:18002`.

## Summary

**Root cause confirmed:** the custom [nginx.conf](./nginx.conf) did not load
Nginx's MIME type map. Nginx returned the linked stylesheet
`/css/styles.css` as `text/plain`. Browsers reject a stylesheet response served
with that MIME type, leaving the otherwise present HTML to render with default
browser styles. JavaScript files were also served as `text/plain`.

The original design was already present in
[`frontend/css/styles.css`](./frontend/css/styles.css), and every HTML entry
page linked to it. The retained Nginx container bind-mounts the workspace's
`frontend/` directory read-only; the assets were present and were not missing
from an image. Therefore, a frontend rewrite or Dockerfile asset-copy change
was unnecessary.

## Diagnosis

### Before the fix

Browser and HTTP checks against the retained app at port 18001 showed:

| Resource / browser value | Observed |
|---|---|
| `/` | HTTP 200, `text/html` |
| `/css/styles.css` | HTTP 200, `text/plain`, 30,222 bytes |
| `/js/app.js` | HTTP 200, `text/plain`, 4,828 bytes |
| Computed body font | `"Times New Roman"` |
| Computed body background | Transparent |
| Computed link color | Browser-default blue |

The before screenshot captured the unstyled landing page: default serif type,
bulleted navigation, and blue underlined links.

### Source and deployment inspection

- All 14 HTML pages use the shared stylesheet, with correct paths:
  `css/styles.css` from the root page and `../css/styles.css` from
  `frontend/pages/`.
- The CSS already defines the PocketCoach navy/blue palette, system/Inter font
  stack, navigation, buttons, forms, cards, dashboard/session layouts, and
  responsive rules.
- The active Nginx container is from the `pocketcoach-check` Compose project.
  Its Nginx image is `nginx:stable-alpine`; its read-only bind mounts point to
  the workspace `nginx.conf` and `frontend/` directory. The frontend is served
  from that mount, not copied into the backend image.
- The custom Nginx config had a `/api/` proxy and a frontend `try_files`
  fallback, but omitted `include /etc/nginx/mime.types;`. HTML still rendered
  because the browser accepted the HTML response, while CSS and JS received
  the wrong MIME type.
- The stylesheet contains no image/font URL dependencies; the inspected HTML
  and CSS contain no `<img>`, inline SVG, favicon, or CSS background-image
  references. UI icons are text/emoji. The font declaration includes Inter
  followed by system fallbacks; no Inter font file is bundled.
- The three MediaPipe script URLs used by camera/session pages returned HTTP
  200 with a JavaScript content type when checked over HTTP. The camera
  workflow itself was not started.
- The Docker Compose Nginx service bind-mounts `./frontend` read-only. The
  backend Dockerfile only copies backend code; a frontend build/copy step is
  not part of this deployment design.

### Other observations

- `/health/ready` is not routed by Nginx and currently falls back to the
  frontend HTML; the backend health endpoint is available internally to its
  Docker health check. This separate routing issue was not changed as part of
  the stylesheet restoration.
- The retained backend image is older than the current workspace, but its age
  did not cause this UI failure: Nginx serves frontend files from the
  workspace bind mount.

## Change implemented

Added the standard MIME mapping and an explicit fallback inside the Nginx
`http` block:

```nginx
include /etc/nginx/mime.types;
default_type application/octet-stream;
```

The existing route configuration and application files were left as found.
No HTML, CSS, JavaScript, API, authentication, or database code was changed.
An existing uncommitted `X-Forwarded-For` line in `nginx.conf` was preserved;
it was not introduced or altered by this restoration.

## Isolated verification

To respect the retained-deployment restriction, the edited configuration and
workspace frontend were tested with a separate Compose project,
`pocketcoach-ui-restore`, on port 18002, using new backend/Redis/PostgreSQL
containers and a fresh disposable PostgreSQL volume. The optimized local
backend image was reused without rebuilding. The isolated services report
healthy; `nginx -t` passed.

After the fix:

| Resource / browser value | Observed at port 18002 |
|---|---|
| `/css/styles.css` | HTTP 200, `text/css`, 30,222 bytes |
| `/js/app.js` and app scripts | HTTP 200, `application/javascript` |
| CSS/JS requests resolved from all pages | 47 checked, 0 failures |
| Computed body background | `rgb(247, 249, 252)` |
| Computed navigation background | `rgba(255, 255, 255, 0.96)` |
| Computed primary button background | `rgb(53, 109, 243)` |
| Computed body font stack | `Inter, ui-sans-serif, system-ui, ...` |

Browser inspection confirmed that the stylesheet is loaded and the landing
page renders with the original gradient hero, styled navigation, sport cards,
and blue/green call-to-action buttons. Login and signup markup and forms remain
present. The normal browser run of the landing and login pages reported no
JavaScript console errors or uncaught page errors.

### Pages and responsive sizes

Shared CSS was verified in the browser on all 14 pages:

- Landing (`index.html`)
- Login/signup
- Athlete dashboard
- Coach/admin dashboard
- Profile settings
- Session setup and camera precheck
- Live training (`session-live.html`)
- Session detail/history
- Demo
- For coaches
- Forgot/reset password
- Pricing

The static page layouts were checked at **320, 375, 390, 430, 768, 1024,
1440, and 1920 CSS pixels**. No horizontal overflow was detected on these
pages at those widths. For the static layout sweep, JavaScript was paused so
authenticated pages would not redirect before their markup was measured.
Separately, normal JavaScript execution was checked on the landing and login
pages. Protected pages require a valid session; without one, the browser
received expected HTTP 401 responses and redirected to login. No authenticated
workflow or camera session was exercised in this UI restoration.

The local asset scan covered **47 page-to-asset references** (14 stylesheet
loads and 33 script loads); all resolved as HTTP 200 with the corrected MIME
type. The normal browser run of the landing/login pages had no console errors
or uncaught page errors. The unauthenticated protected-page pass did record
expected 401 responses before redirecting to login.

The before and after browser screenshots are attached to the task conversation.

## Retained deployment status and access

- `pocketcoach-check` on **port 18001** was not restarted or reloaded. It
  continues to run its already-loaded Nginx configuration, so its live page
  remains unstyled until that Nginx service is deliberately reloaded/restarted.
- The restored, browser-verified stack is available at
  **http://localhost:18002**. It has separate containers and a separate fresh
  PostgreSQL volume; it does not point at the retained database.
- The root `nginx.conf` is now fixed for subsequent launches. No commit, push,
  merge, or deployment was performed.

## Remaining issues

1. If the restored UI should replace the app at port 18001, a separately
   approved Nginx reload/restart of the retained project is still required.
   It was intentionally not performed under the safety requirement.
2. Authenticated dashboard and camera interactions were not tested without a
   test account; their static styling and asset paths were checked.
3. Inter is not bundled as a font asset, so browsers use the configured
   system-font fallback when Inter is not installed.
4. The unrelated Nginx `/health/ready` fallback behavior remains unchanged.
