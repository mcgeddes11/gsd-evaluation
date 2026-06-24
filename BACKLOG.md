# Backlog

## Bugs

### ~~[BUG] Republishing a post resets published_at to now~~ ✓ DONE
**File:** `app/blueprints/posts.py:164`
The `/publish` route unconditionally sets `published_at = datetime.utcnow()` on every publish, even if the post was previously published. This causes republished posts to bubble to the top of the public feed.
**Fix:** Guard with `if not post.published_at` (same pattern already used in `_apply_post_form`).

---

## Features

### ~~[FEATURE] Editable published date in admin post list~~ ✓ DONE
When migrating content, it would be useful to manually set the published date on a post so it appears in the correct position in the public feed rather than defaulting to the current date.
**Scope:**
- New route: `POST /<post_id>/set-published-date` (owner or admin only)
- Add inline date input + save button to the published date column in `templates/posts/list.html`
- No schema change required (`published_at` is already a nullable DateTime)

**Depends on:** Bug fix above should be shipped first.

### [FEATURE] Post preview for drafts
The Quill editor and the public post render use different base templates and CSS, making it hard to judge formatting before publishing. A preview should show the post exactly as the public would see it.
**Scope:**
- New route: `GET /admin/posts/<post_id>/preview` — renders the existing `public/post.html` template without requiring `status = "published"`, owner or admin only
- Add a "Preview" button to `templates/posts/editor.html` that saves the draft (same as "Save Draft") then opens the preview URL in a new tab
- No schema or CSS changes required

**Note:** Unsaved changes won't appear in the preview — you must save first.
