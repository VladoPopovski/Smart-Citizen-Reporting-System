# Bug List

## Critical

**BUG-001 - Hardcoded admin bypass in RoleContext.tsx**
File: `frontend/src/context/RoleContext.tsx` lines 103-109
Problem: Dev shortcut is left in — every visitor is automatically logged in as admin without any credentials.
Fix: Remove the hardcoded block and restore the real Supabase auth flow.

**BUG-002 - DEV_SKIP_AUTH uses citizen UUID instead of admin**
File: `app/utils/dependencies.py` - DEV_USER
Problem: When DEV_SKIP_AUTH=true, the backend returns a citizen user. Admin/officer endpoints return 403 during development.
Fix: Change DEV_USER UUID to the admin UUID bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb.

---

## High

**BUG-003 - Login always sends role "citizen" regardless of selector**
File: `frontend/src/pages/LoginPage.tsx` line 40
Problem: `login(email, password, "citizen")` is hardcoded. The role dropdown on the login tab is ignored.
Fix: Pass the `role` state variable instead of the string literal.

**BUG-004 - UI and exports read from different databases**
Problem: The frontend fetchReports() reads from Supabase directly. The backend export endpoints read from DATABASE_URL (local PostgreSQL). Exported CSV/PDF may have different data than what the user sees.
Fix: Point DATABASE_URL in the backend .env to the same Supabase PostgreSQL database.

**BUG-005 - Wrong DATABASE_URL driver prefix**
Problem: SQLAlchemy with psycopg3 needs `postgresql+psycopg://`. Using `postgresql://` causes connection failure.
Fix: Update DATABASE_URL prefix to `postgresql+psycopg://`.

**BUG-006 - Notification bell does nothing when clicked**
File: `frontend/src/components/Navbar.tsx`
Problem: The bell icon had no click handler — no dropdown opened, no notifications shown.
Status: Fixed.

---

## Medium

**BUG-007 - CSV values wrapped in unnecessary quotes**
File: `app/routers/analytics.py`
Problem: Used csv.QUOTE_ALL so every cell had quotes around it. Some Excel/locale setups displayed them visibly.
Status: Fixed — removed QUOTE_ALL.

**BUG-008 - PDF shows black squares instead of Macedonian text**
File: `app/routers/analytics.py`, `app/routers/reports.py`
Problem: ReportLab default fonts don't support Cyrillic.
Status: Fixed — added font detection for Arial (Windows) and DejaVu Sans (Linux).

**BUG-009 - CSV includes latitude/longitude columns**
File: `app/routers/analytics.py`
Problem: Raw coordinates were included in the export which confused users.
Status: Fixed — removed lat/lng columns.

**BUG-010 - Reports PDF table overflows page width**
File: `app/routers/reports.py`
Problem: No colWidths set on the ReportLab table, causing data to be cut off on the right.
Status: Fixed — added explicit column widths.

**BUG-011 - App crashes with blank page when Supabase env vars are missing**
File: `frontend/src/lib/supabase.ts`
Problem: Missing VITE_SUPABASE_URL threw an error and crashed the whole frontend.
Status: Fixed — fallback values added with ??.

**BUG-012 - Login tab shows role selector (should only be on register)**
File: `frontend/src/pages/LoginPage.tsx`
Problem: Role dropdown appears on the login tab. At login the role should come from the database, not be chosen by the user.
Fix: Show the role selector only when activeTab === "register".

---

## Low

**BUG-013 - Month names in analytics are in English**
File: `app/routers/analytics.py`
Problem: strftime("%b") returns English month names (Jan, Feb...) on English-locale servers.
Fix: Use a manual Macedonian month name mapping.

**BUG-014 - Ratings grouped by category but labeled as "per department"**
File: `app/services/rating_service.py`
Problem: CR-06 specifies ratings per department but the department FK was removed. Function now groups by category but the UI still says "per department".
Fix: Update UI labels to say "по категорија".

**BUG-015 - psycopg[binary] listed twice in requirements.txt**
File: `requirements.txt`
Problem: Duplicate dependency entry, also psycopg2-binary is listed alongside psycopg3.
Fix: Remove the duplicate line.