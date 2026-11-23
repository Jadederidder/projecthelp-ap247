# Project Help — Auto Pedigree 24/7 (ap247)

Every session starts with **no memory**. This file is the only thing loaded
automatically, so what is learned goes here rather than only into a commit
message.

## What this repo is

Two pieces of **customer-facing collateral** for the Auto Pedigree "Auto Plus
Plan", and nothing else:

1. **The landing page** — `docs/index.html`, published at
   `https://ap247.projecthelp.co.za`. This is where the SMS campaign sends
   people.
2. **The brochure** — `brochure/retitle.py` builds
   `brochure/auto-pedigree-247.pdf` by patching the original Premium Help PDF.
   The served copy is `docs/auto-pedigree-247-brochure.pdf`.

**This repo is genuinely public.** `Jadederidder/projecthelp-ap247` is a
public repository with GitHub Pages enabled, serving `docs/` on `main`
(confirmed 2026-11-23 against the GitHub API). It is the **only** one of
Project Help's collateral repos with no gate in front of it — no Cloudflare
Access, no access code, no `robots.txt` disallow. Everything you commit here
is readable by anybody, immediately.

DNS, from the README: Afrihost DNS for `projecthelp.co.za`, CNAME `ap247` →
`jadederidder.github.io`, TTL 14400.

It does **not** own anything operational. Collections, cancellations, Casi,
Revio, Paystack and the CRM are elsewhere — see the bottom of this file.

## Nothing here runs on a schedule

**No workflows. None.** No `.github/` directory, no cron, no dispatch job, no
CI, and **no repository secrets**. Publishing is: push to `main`, GitHub
Pages builds it.

`main` carries a **single squashed commit** — `6603f25`, PR #3, 2026-11-01,
the brochure and the page together. `claude/funny-bardeen-ogppie` holds the
unsquashed history behind it (its commit `6444bad` has the identical tree to
`main`) plus **exactly one commit of new content**: `c8a7201`, the
landing-page fix below, open as **PR #4** and **unmerged as at 2026-11-23**.

So the diff that matters between the branch and `main` is one file,
`docs/index.html`. Everything else is the same work with different hashes.

## The page is wired to the CRM, and its source is not in any repo here

`docs/index.html` ends with a campaign click tracker. The SMS links in with
`?t=<token>`; the page POSTs that token to

    https://lgziureyluogydpbsgfq.supabase.co/functions/v1/ap-click

and then strips `?t=` out of the address bar with `history.replaceState`. It
is deliberately fail-soft — a failed POST never blocks or delays the page.
There is no key in the page, so the function must be running with
`verify_jwt: false`.

That project id is the **CRM's** Supabase project (`project-help-crm`,
`lgziureyluogydpbsgfq`). **But `ap-click` is not among the edge functions
committed in `project-help-crm/supabase/functions/`, and the string appears
in no repo in this checkout** (checked 2026-11-23). The CRM's own `CLAUDE.md`
says there are ~30 edge functions and that `list_edge_functions` is the list,
so the function is almost certainly deployed without its source in git.

**Do not rebuild it on an assumption of what it does.** To find out: run
`list_edge_functions` on the Supabase project, or ask JD. Until then, treat
the endpoint as live and leave the tracker alone.

## The brochure is a patch of the original, not a rebuild

`brochure/retitle.py` (pymupdf + segno) **duplicates** the Premium Help PDF
and changes only what is actually different about the Auto Pedigree product.
Every page keeps its own artwork, grid and type, because none of it is re-set.

Re-typesetting it in HTML was tried and reproduced the words but not the
thing — the layout, artwork, spacing and feel all came out as approximations.

- `brochure/source/premium-help-original.pdf` is **committed and never
  edited.** It is the input.
- `brochure/auto-pedigree-247.pdf` is the output. `docs/…-brochure.pdf` is the
  served copy. They are two files with different names. They were byte-identical
  on 2026-11-23 — **check that before a campaign goes out**, because nothing
  copies one to the other automatically.
- **One substitution, stated plainly.** The original is set in Plus Jakarta
  Sans. That font is not installed here, the CDNs are blocked by the egress
  policy, and the subsets embedded in the PDF are missing `7` and `/`
  outright — so "24/7" cannot be drawn from them either. Replaced text is set
  in **Inter**; untouched text stays in Plus Jakarta Sans. Drop
  `PlusJakartaSans-{Regular,Medium,SemiBold,Bold,ExtraBold}.ttf` into
  `brochure/fonts/` and the script picks them up with no other change.
- Both QR codes in the brochure point at `ap247.projecthelp.co.za` — this
  page. The two pieces of collateral are a loop; a change to one is read
  against the other.

## The brochure and the page described two different products

Know this before touching either, and know where the fix currently sits.

The brochure was deliberately built to say:

- **No medical response.** Auto Pedigree members have it from another
  provider. `retitle.py` strips it from the cover strip, page 3 and page 8,
  and takes the medical cross off the shield.
- **No Mental Health Support.** Absa's ListenUp on WhatsApp is not sold with
  Auto Pedigree. **RAF Assist replaces it**, and goes last in the running
  order, where JD wants it.

**`main` still says the opposite.** `docs/index.html` on `main` sells
"Medical Emergency" as its second service card, repeats it in the hero, both
meta descriptions, the family-cover list and the FAQ, and carries "The
Talking Point — confidential mental health chat support" as a service card.
Both QR codes in the brochure point at that page, so a member reads one and
is then shown the other.

**It is fixed on a branch that is not merged.** Commit `c8a7201` on
`claude/funny-bardeen-ogppie` (open as **PR #4**, 2026-11-01, unmerged as at
2026-11-23) removes Medical Emergency and The Talking Point from the card,
the family list, the hero sentence, the family FAQ and both meta
descriptions, and moves RAF Claims Assistance to the end. Its message records
why: *"JD asked whether the page had been rebuilt since medical came out. It
had not, so the page the SMS links to was still promising a service Auto
Pedigree does not carry."* With it, the page, the brochure and the four live
campaign templates describe the same product.

**So: do not re-fix this.** The work exists. If the page is still wrong in
production, the answer is that PR #4 has not been merged — say that, rather
than opening a second one. JD merges nothing by hand: open it and merge it.

**One defect survives on that branch.** Five service cards now sit under a
heading that still reads **"Six services. One app. Zero hassle."** It was
seven cards under the same heading on `main`. Flagged, not changed.

## Dead links on a live page

As at 2026-11-23, on the page the SMS campaign points at:

- **Every store badge is `href="#"`** — both in the hero and both in the
  closing band. "Get the App" is the page's primary call to action and all
  four badges go nowhere. True on `main` and on the PR #4 branch.
- **Terms & Conditions, Privacy Policy and POPIA Notice in the footer are all
  `href="#"`** — on a page that captures a campaign token tied to a specific
  recipient.
- **"Six services" over five cards**, as above.

Record them; do not invent the destinations. The store URLs and the legal
pages are JD's to supply.

## R23 a week — say which R23 you mean

On this page **R23 a week is the household upgrade**: five people, the member
plus four, 66c per person per day, *added in the app*. The member's own cover
is described as **already included with the Auto Plus Plan at no additional
cost**.

`project-help-collections/CLAUDE.md` describes the same R23 a week as "Auto
Pedigree's current product… on CARD through Paystack, signed up in the app",
and the Auto Pedigree dashboard counts those card subscribers and earns the
**single** rate on them (R23/wk ≈ R92/month ≈ the R89 single membership).

Same price, same weekly card subscription — **but say which thing you are
quoting**, because "R23 is what an Auto Pedigree member pays for cover" is
not what this page tells the customer.

## What is safe to put here, and what is not

`docs/` is served to the open internet with no gate. Published business
contacts are fine and already on the page: `support@projecthelp.co.za` and
`0860 203 203`, the company registration in the footer.

**Never put a customer's name, cell number, ID number, account number or
email address anywhere in this repo** — not in `docs/`, not in `brochure/`,
not in a commit message, not in a test fixture. There is nothing here that
needs one: the page has no form, no login and no customer data. The only
outbound call is the opaque campaign token.

There are no credentials in this repo and none are needed. Anything that
requires one belongs in `project-help-collections` or `project-help-crm`.

## Naming

**"My Red Button" must not appear anywhere in the ecosystem** — not in code,
not in copy, not in a screen. It appears nowhere in this repo (checked
2026-11-23). Keep product, cover and campaign names plain business English;
JD has been explicit that he does not want vernacular naming suggestions.

## The other repos

- **`project-help-collections`** — Revio / Casi / Paystack operations, the
  monthly cancellation engine, outbound email, **and the sync that builds the
  Auto Pedigree dashboard's data**. Its `CLAUDE.md` holds the Casi hosts,
  credentials and cover ids. Read it before touching anything that cancels or
  collects, and **do not ask JD for Casi credentials** — they are repo secrets
  there.
- **`project-help-crm`** — Supabase `lgziureyluogydpbsgfq`, the edge
  functions, the `ph_x_*` view gate, the Aura book.
- **`auto-pedigree-dashboard`** — the client-facing commission dashboard for
  this same product.
- **`project-help-vw-sales`**, **`project-help-netstar`** — different books.

## Still open

- **PR #4 is open and unmerged.** Until it lands, the live page promises
  medical response and mental health support that the product does not carry.
- The "Six services" heading over five cards, on that same branch.
- The store links and the three legal pages.
- Where `ap-click`'s source lives, and what it writes.

## How JD wants to be answered

- He has said these already; do not make him say them again.
- **No menus.** If you have the answer, give it. If a decision is genuinely
  his — anything that cancels more people, charges more, or writes to a live
  cover or a client-facing page — ask once, in one line.
- Never present a flag, a count or a status as a fact without checking what it
  measures. He will check, and he will be right.
- **Do not say "I don't know" about something written in these repos.** Read
  them.
- He merges nothing by hand: open the PR and merge it.

## Safety rules that are not negotiable

- Never commit a credential. Hashes only (SHA-256), never the secret.
- Never put a live ID number, phone number, account number or customer email
  address into a commit message, a comment, or anything else
  version-controlled — and **never anywhere under `docs/`, which on this repo
  is served publicly with no gate at all.**
- `DRY_RUN` defaults to true in every script that writes to a back end.
- Ask JD before deleting or switching anything off.
