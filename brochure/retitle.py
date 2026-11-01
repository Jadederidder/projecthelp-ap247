#!/usr/bin/env python3
"""Build the Auto Pedigree 24/7 brochure by patching the Premium Help original.

    python3 brochure/retitle.py

Reads  brochure/source/premium-help-original.pdf  (committed, never edited)
Writes brochure/auto-pedigree-247.pdf

WHY THIS AND NOT A REBUILD
--------------------------
The brochure was designed in a tool we do not have and exists only as a PDF.
Re-typesetting it in HTML reproduced the words but not the thing: the layout,
the artwork, the spacing and the feel all came out as approximations. So this
script duplicates the original file and changes only what is actually
different about the Auto Pedigree product. Every page keeps its own artwork,
its own grid and its own type, because none of it is re-set.

WHAT DIFFERS BETWEEN THE TWO PRODUCTS
-------------------------------------
  * the name: Premium Help -> Auto Pedigree 24/7
  * the third service: Absa's Mental Health Support (ListenUp on WhatsApp) is
    not sold with Auto Pedigree. RAF Assist is. That is page 3, the cover
    service strip, the cover copy, an FAQ and a T&C section.
  * Free Wills is not Absa's here
  * support@projecthelp.co.za, not Absa@projecthelp.co.za
  * the fee is R23 weekly, not monthly
  * the QR codes point at ap247.projecthelp.co.za
  * fair use says plainly that a genuine emergency is never charged for

ONE SUBSTITUTION, STATED PLAINLY
--------------------------------
The original is set in Plus Jakarta Sans. That font is not on this machine and
cannot be fetched (fonts.google.com and the CDNs are blocked by the egress
policy), and the subsets embedded in the PDF are missing '7' and '/' outright,
so "24/7" cannot be drawn from them either. Replaced text is therefore set in
Inter, the closest face installed here; everything untouched stays in Plus
Jakarta Sans. Drop the real font into brochure/fonts/ as
PlusJakartaSans-{Regular,Medium,SemiBold,Bold,ExtraBold}.ttf and this script
picks it up, with no other change.
"""

import os
import sys

import pymupdf
import segno

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'source', 'premium-help-original.pdf')
OUT = os.path.join(HERE, 'auto-pedigree-247.pdf')
ASSETS = os.path.join(HERE, 'assets')
LINK = 'https://ap247.projecthelp.co.za'

_LOCAL = os.path.join(HERE, 'fonts')
_SYS = '/usr/share/fonts/opentype/inter'
_WEIGHTS = {
    'Regular': ('PlusJakartaSans-Regular.ttf', 'Inter-Regular.otf'),
    'Medium': ('PlusJakartaSans-Medium.ttf', 'Inter-Medium.otf'),
    'SemiBold': ('PlusJakartaSans-SemiBold.ttf', 'Inter-SemiBold.otf'),
    'Bold': ('PlusJakartaSans-Bold.ttf', 'Inter-Bold.otf'),
    'ExtraBold': ('PlusJakartaSans-ExtraBold.ttf', 'Inter-ExtraBold.otf'),
}
SUBSTITUTED = set()


def fontfile(weight):
    real, fallback = _WEIGHTS[weight]
    p = os.path.join(_LOCAL, real)
    if os.path.exists(p):
        return p
    SUBSTITUTED.add(weight)
    return os.path.join(_SYS, fallback)


def measure(s, weight, size):
    return pymupdf.Font(fontfile=fontfile(weight)).text_length(s, size)


# Colours sampled out of the original file.
NAVY = (19 / 255, 39 / 255, 63 / 255)
WHITE = (1, 1, 1)
GREEN_PANEL = (237 / 255, 245 / 255, 231 / 255)
STEP_CARD = (0.9569, 0.9686, 0.9490)
CHIP_LINE = (0.8118, 0.8863, 0.7529)
GREEN = (0x3f / 255, 0x7a / 255, 0x1c / 255)
RED = (0xd0 / 255, 0x31 / 255, 0x2d / 255)
INK = (0x3d / 255, 0x4a / 255, 0x57 / 255)
HEAD = (0x1f / 255, 0x3a / 255, 0x55 / 255)
TERMS = (0x2e / 255, 0x3a / 255, 0x46 / 255)
MUTE = (0x5b / 255, 0x68 / 255, 0x75 / 255)
CARD = (241 / 255, 245 / 255, 247 / 255)     # page 4/5/7 cards
WILLS_CARD = (245 / 255, 242 / 255, 250 / 255)  # page 6 cards
WILLS_PANEL = (237 / 255, 233 / 255, 246 / 255)
WARN_BG = (0.984, 0.914, 0.910)

# Leading as a multiple of the font size, measured off the original.
LEAD = {15.0: 1.30, 12.75: 1.26, 12.0: 1.56, 11.25: 1.53, 10.5: 1.57, 9.0: 1.41}


class Page:
    """Redact first, draw second.

    apply_redactions() erases everything under the rectangles, so every
    replacement has to be queued and drawn after the erase, never before it.
    """

    def __init__(self, doc, n):
        self.doc = doc
        self.page = doc[n]
        self.n = n
        self._draw = []

    # -- erase -------------------------------------------------------------
    def erase(self, x0, y0, x1, y1, fill=WHITE):
        self.page.add_redact_annot(pymupdf.Rect(x0, y0, x1, y1), fill=fill)
        return self

    # -- queue -------------------------------------------------------------
    def para(self, x0, y0, x1, y1, text, size=12.0, weight='Regular',
             color=INK, align=0, lead=None, fill=WHITE, pad=2.0):
        """Replace a block of copy, re-flowed inside the block it replaces."""
        self.erase(x0 - pad, y0 - pad, x1 + pad, y1 + pad, fill=fill)
        self._draw.append(('box', (x0, y0 - size * 0.30, x1, y1 + size * 0.9),
                           text, weight, size, color, align,
                           lead or LEAD.get(size, 1.5)))
        return self

    def line(self, x, baseline, text, size=12.0, weight='Regular', color=INK):
        self._draw.append(('line', (x, baseline), text, weight, size, color,
                           0, 1.0))
        return self

    def chips(self, x, y, labels, size=11.25, height=27.8, gap=9.0,
              pad=13.0):
        """A row of outlined pills, each sized to the words inside it."""
        font = pymupdf.Font(fontfile=fontfile('SemiBold'))
        for label in labels:
            w = font.text_length(label, size) + pad * 2
            self._draw.append(('chip', (x, y, x + w, y + height), label,
                               'SemiBold', size, HEAD, 0, None))
            x += w + gap
        return self

    def rect(self, x0, y0, x1, y1, color, radius=None):
        self._draw.append(('rect', (x0, y0, x1, y1), None, None, None, color,
                           0, radius))
        return self

    def swap_image(self, xref, path):
        """Put a different picture in an existing image slot, same rect."""
        self._draw.append(('swap', None, path, None, None, None, 0, xref))
        return self

    def blank_image(self, xref):
        """Replace an embedded bitmap with a transparent pixel.

        The object stays in place, so nothing else on the page moves; the
        picture simply stops being drawn. Used where an image overlaps
        artwork that a redaction rectangle would destroy.
        """
        self._draw.append(('blank', None, xref, None, None, None, 0, None))
        return self

    def image(self, x0, y0, x1, y1, path):
        self._draw.append(('img', (x0, y0, x1, y1), path, None, None, None,
                           0, None))
        return self

    def svg(self, x0, y0, x1, y1, markup):
        self._draw.append(('svg', (x0, y0, x1, y1), markup, None, None, None,
                           0, None))
        return self

    # -- run ---------------------------------------------------------------
    def commit(self):
        self.page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
        for kind, box, text, weight, size, color, align, extra in self._draw:
            if kind == 'box':
                rc = self.page.insert_textbox(
                    pymupdf.Rect(*box), text, fontname='F' + weight,
                    fontfile=fontfile(weight), fontsize=size, color=color,
                    align=align, lineheight=extra)
                if rc < 0:
                    sys.exit(f'page {self.n + 1}: {text[:50]!r} overflows its '
                             f'block by {-rc:.1f}pt — shorten it or widen {box}')
            elif kind == 'line':
                self.page.insert_text(
                    pymupdf.Point(*box), text, fontname='F' + weight,
                    fontfile=fontfile(weight), fontsize=size, color=color)
            elif kind == 'rect':
                r = pymupdf.Rect(*box)
                sh = self.page.new_shape()
                if extra:
                    sh.draw_rect(r, radius=extra / min(r.width, r.height) / 2)
                else:
                    sh.draw_rect(r)
                sh.finish(fill=color, color=color)
                sh.commit()
            elif kind == 'chip':
                r = pymupdf.Rect(*box)
                sh = self.page.new_shape()
                sh.draw_rect(r, radius=0.5)
                sh.finish(color=CHIP_LINE, fill=WHITE, width=1.0)
                sh.commit()
                self.page.insert_textbox(
                    pymupdf.Rect(r.x0, r.y0 + 6.2, r.x1, r.y1), text,
                    fontname='FSemiBold', fontfile=fontfile('SemiBold'),
                    fontsize=size, color=color, align=1)
            elif kind == 'swap':
                self.page.replace_image(extra, filename=text)
            elif kind == 'blank':
                self.page.replace_image(text, pixmap=pymupdf.Pixmap(
                    pymupdf.csRGB, pymupdf.IRect(0, 0, 1, 1), True))
            elif kind == 'img':
                self.page.insert_image(pymupdf.Rect(*box), filename=text,
                                       keep_proportion=True)
            elif kind == 'svg':
                src = pymupdf.open(stream=text.encode(), filetype='svg')
                pdf = pymupdf.open('pdf', src.convert_to_pdf())
                self.page.show_pdf_page(pymupdf.Rect(*box), pdf, 0)


def icon_svg(path_d, colour):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            f'<path fill="{colour}" d="{path_d}"/></svg>')


# The RAF van, lifted from the service strip on ap247.projecthelp.co.za so the
# brochure and the landing page carry the same mark.
VAN = ('M5 17a2 2 0 1 0 4 0 2 2 0 0 0-4 0Zm10 0a2 2 0 1 0 4 0 2 2 0 0 0-4 0Z'
       'M3 6h11v6h3.5l2.5 3v2h-1.1a3.5 3.5 0 0 0-6.8 0H9.9a3.5 3.5 0 0 0-6.8 '
       '0H3V6Z')


def qr_png(dest, scale=14):
    segno.make(LINK, error='m').save(dest, scale=scale, border=0,
                                     dark='#13273f', light='#ffffff')
    return dest


# ---------------------------------------------------------------------------
#  the patches
# ---------------------------------------------------------------------------

def cover(doc, qr):
    p = Page(doc, 0)

    # --- masthead. "Premium" + a red box around "Help" becomes
    # "Auto Pedigree" + a red box around "24/7". The name is longer than the
    # one it replaces and the phone mockup fixes the right-hand limit, so the
    # size is fitted to the space rather than guessed at.
    left, limit, baseline = 42.0, 366.0, 345.0
    size = 37.5
    while size > 20:
        w = (measure('Auto Pedigree ', 'ExtraBold', size)
             + measure('24/7', 'ExtraBold', size) + size * 0.60)
        if left + w <= limit:
            break
        size -= 0.5
    p.erase(38, 294, limit + 6, 360, fill=NAVY)
    p.line(left, baseline, 'Auto Pedigree', size=size, weight='ExtraBold',
           color=WHITE)
    box_x = left + measure('Auto Pedigree ', 'ExtraBold', size)
    box_w = measure('24/7', 'ExtraBold', size) + size * 0.52
    p.rect(box_x, baseline - size * 0.84, box_x + box_w, baseline + size * 0.26,
           RED, radius=size * 0.13)
    p.line(box_x + size * 0.26, baseline, '24/7', size=size, weight='ExtraBold',
           color=WHITE)

    # --- second cover paragraph: Mental Health is not part of this product.
    p.para(42, 468.3, 345, 502.9,
           'If you are ever injured in a road accident, the RAF button '
           'starts your claim at no cost to you.',
           size=12.0, color=(0xd5 / 255, 0xde / 255, 0xe8 / 255), fill=NAVY)

    # --- service strip: Mental Health Support -> RAF Claims, icon and label.
    p.erase(172.0, 666.0, 211.0, 705.0, fill=(0.918, 0.953, 0.886))
    p.svg(179.5, 673.5, 203.1, 697.1, icon_svg(VAN, '#3f7a1c'))
    # One line where Mental Health Support took two, so it is dropped to sit
    # on the same baseline as the other four labels.
    p.para(148, 718.0, 235, 744.0, 'RAF Claims', size=9.75, weight='Bold',
           color=(0x1e / 255, 0x2a / 255, 0x36 / 255), align=1, lead=1.26,
           pad=3.0)

    # --- the QR took you to the Premium Help listing.
    p.erase(114.0, 754.5, 177.0, 817.5)
    p.image(116.3, 756.8, 174.7, 815.2, qr)

    # --- the hero mockup was a design of an app that was never shipped.
    # The old bitmap is blanked where it sits (a redaction rectangle here
    # would punch a white hole in the cover photograph behind it), then the
    # real screenshot is drawn over the same spot at its own proportions.
    p.blank_image(67)
    old = pymupdf.Rect(378.0, 231.8, 522.0, 543.8)
    half = old.height * (1007 / 1733) / 2
    mid = (old.x0 + old.x1) / 2
    p.image(mid - half, old.y0, mid + half, old.y1,
            os.path.join(ASSETS, 'app-home.png'))
    p.commit()


def armed(doc):
    p = Page(doc, 1)
    # The sentence names the app, so it reflows: two lines become three.
    # There is room before step 2, which starts at y=405.
    p.para(76.5, 352.8, 272, 396.5,
           'Hold the red HOLD button in your Auto Pedigree 24/7 app for 3 '
           'seconds.', size=12.0, lead=1.46)
    p.commit()


def raf(doc):
    """Page 3 was Mental Health Support, which Auto Pedigree does not carry.

    The layout fits RAF Assist without moving anything: a tinted panel with a
    white card beside the copy, three numbered steps, a row of chips and a red
    caution box. Only the words and what the card holds change."""
    p = Page(doc, 2)

    p.para(42, 52.9, 300, 70.0, 'A F T E R  A  R O A D  A C C I D E N T',
           size=10.5, weight='Bold', color=GREEN, fill=GREEN_PANEL)
    p.para(42, 75.4, 330, 146.2, 'Road Accident\nFund Claims',
           size=30.0, weight='ExtraBold', color=GREEN, lead=1.25,
           fill=GREEN_PANEL)
    p.para(42, 156.9, 330, 196.8,
           'Injured in a road accident?\nWe run the claim for you.',
           size=15.0, weight='SemiBold', color=HEAD, fill=GREEN_PANEL)
    p.para(42, 211.8, 330, 284.7,
           'The Road Accident Fund compensates people injured in a crash '
           'caused by another driver. Claiming is slow and full of paperwork, '
           'so we run it for you \u2014 and it costs you nothing.',
           size=12.0, fill=GREEN_PANEL)

    # The white card held a QR code into a WhatsApp counselling line. It now
    # carries what the claim costs you, which is the whole pitch.
    p.erase(358, 50, 549, 286, fill=WHITE)
    p.para(380, 86, 528, 118, 'You keep 100% of your payout.',
           size=13.5, weight='Bold', color=GREEN, lead=1.24)
    p.para(380, 140, 528, 160, 'Included at no cost', size=10.5,
           weight='Bold', color=HEAD, lead=1.26)
    p.para(380, 168, 528, 270,
           'Legal representation\nClaims administration\n'
           'Medical and legal reports\nLoss of support and actuarial reports',
           size=11.25, lead=1.70)

    # three steps, inside the cards that were already there
    for x0, x1, title, body in (
        (58.5, 186.0, 'Get in touch',
         "Tap RAF on the app's home screen, or call us."),
        (233.5, 361.0, 'Verify your cover',
         'Give your ID or membership number so we can confirm your cover.'),
        (408.5, 536.0, 'We run the claim',
         'Our claims team contacts you and guides you through every step.'),
    ):
        p.para(x0, 431.5, x1, 462.0, title, size=12.75, weight='Bold',
               color=HEAD, lead=1.26, fill=STEP_CARD)
        p.para(x0, 468.0, x1, 532.0, body, size=12.0, fill=STEP_CARD)

    p.para(42, 570.4, 300, 586.0, 'W H O  I S  C O V E R E D',
           size=10.5, weight='Bold', color=GREEN)

    # The chips listed what you might want to talk about. They now say who is
    # covered and how long you have to lodge. Both rows are redrawn because
    # the outlines are sized to the words inside them.
    p.erase(40, 592, 560, 664)
    p.chips(42.7, 596.2, ['You, the main member', 'Your spouse or partner',
                          'Dependent children under 21'])
    p.chips(42.7, 633.0, ['Students under 25', 'Claim within 3 years',
                          'Hit-and-run: within 2 years'])

    p.para(93.0, 702.3, 545, 720.0, 'RAF Assist is not insurance.',
           size=12.75, weight='Bold', color=HEAD, fill=WARN_BG, lead=1.26)
    p.para(93.0, 722.5, 545, 786.0,
           'It is a service that helps you claim from the Road Accident Fund. '
           'We cannot guarantee a payout, but we make every reasonable effort '
           'to reach a settlement. The information you give us must be '
           'complete and accurate, because anything incorrect can jeopardise '
           'the claim.', size=12.0, fill=WARN_BG)
    p.commit()


def screens(doc):
    """The three interior screenshots were taken in the Absa build. These are
    the same screens in Auto Pedigree 24/7, at the same pixel size, so each
    one drops straight into the slot the old one occupied."""
    for n, xref, name in ((3, 217, 'app-licence.jpg'),
                          (4, 272, 'app-fines.jpg'),
                          (5, 322, 'app-wills.jpg')):
        p = Page(doc, n)
        p.swap_image(xref, os.path.join(ASSETS, name))
        p.commit()


def wills(doc):
    p = Page(doc, 5)
    p.para(42, 240.3, 340, 313.2,
           'Free to start, drafted by qualified Wills and Trusts '
           'professionals. Request a call back in the app and a consultant '
           'contacts you directly. No queues and no legal jargon.',
           size=12.0, fill=WILLS_PANEL)
    p.para(233.5, 550.0, 362, 566.0, 'They call you back', size=12.75,
           weight='Bold', color=HEAD, lead=1.26, fill=WILLS_CARD)
    p.para(408.5, 587.5, 537, 645.0,
           'Professionally drafted, and free to start.', size=12.0,
           fill=WILLS_CARD)
    p.para(42, 681.4, 553, 694.6,
           'Project Help is the entry point only. The provider handles all '
           'legal advice and drafting with you.',
           size=10.5, color=MUTE)
    p.commit()


def started(doc, qr):
    p = Page(doc, 6)
    p.para(57.0, 174.3, 200, 241.0,
           'Scan the QR code below or search Auto Pedigree 24/7 in the App '
           'Store or Google Play.', size=11.25, fill=CARD)
    p.erase(106.0, 285.5, 182.0, 361.0, fill=CARD)
    p.image(107.9, 287.1, 180.1, 359.4, qr)

    # fair use, in JD's words: an emergency is never charged for
    p.para(42, 618.4, 292, 698.0,
           'A genuine emergency is never charged for. Fair use is 4 armed '
           'response call-outs per person a year; a call-out that is not a '
           'security or medical emergency costs R450.00 (excl VAT). Medical '
           'transport is billed to you or your medical aid.', size=10.5)
    p.para(312.8, 598.8, 555, 629.7, 'What does RAF Assist cost me?',
           size=12.0, weight='Bold', color=HEAD, lead=1.26)
    # the question it replaces ran to two lines; this one does not, so the
    # answer moves up to sit level with the column beside it
    p.erase(310, 630, 558, 684)
    p.para(312.8, 618.4, 558, 680.3,
           'Nothing. Legal representation, claims management and the reports '
           'are all included, and you keep 100% of your payout.', size=10.5)
    p.para(42, 729.4, 290, 774.8,
           'Tap Free Wills in the app and request a call back. A Wills and '
           'Trusts consultant contacts you, usually within 24 hours.',
           size=10.5)
    p.para(312.8, 729.4, 558, 758.3,
           "Email support@projecthelp.co.za. Cancellation takes 30 days' "
           'notice.', size=10.5)
    p.commit()


def terms_one(doc):
    p = Page(doc, 7)
    p.para(52.5, 106.9, 285, 131.7,
           'Your Auto Pedigree 24/7 membership remains active for as long as '
           'you pay your weekly fee of R23.00.', size=9.0, color=TERMS)
    p.para(52.5, 236.7, 285, 260.7,
           'Payments are deducted weekly. Services cease if payments stop.',
           size=9.0, color=TERMS)
    p.para(52.5, 265.2, 290, 289.2,
           'You can cancel your membership on 30 days’ notice by email '
           'to support@projecthelp.co.za.', size=9.0, color=TERMS)
    p.para(52.5, 321.4, 285, 345.5,
           'Payments are debited weekly with the reference "ProjectHelp".',
           size=9.0, color=TERMS)
    p.para(42, 449.7, 290, 512.7,
           'A genuine emergency is never charged for. Fair use is 4 armed '
           'response call-outs per covered person every 12 months. R450.00 '
           '(VAT exclusive) applies only to a call-out that is not a security '
           'or medical emergency, or beyond the fair-use allowance.',
           size=9.0, color=TERMS)
    p.para(309.8, 137.7, 545, 175.2,
           'Subscription fees are payable weekly in advance. No refunds are '
           'given on payments already taken. Full terms and conditions: '
           'www.projecthelp.co.za/terms', size=9.0, color=TERMS)

    # section 2 was Mental Health Support
    p.para(309.8, 187.1, 545, 199.4, '2. RAF Assist', size=9.75,
           weight='ExtraBold', color=HEAD, lead=1.26)
    # The bullets on this page are drawn separately from the text, at fixed
    # heights. These two sections change how many paragraphs they hold, so
    # the old bullets are erased with the copy and set inline instead.
    p.para(309.8, 204.4, 555, 368.0,
           '\u2022  RAF Assist is not an insurance product. It is a service that '
           'helps you claim from the Road Accident Fund.\n'
           '\u2022  It covers the main member, your spouse or partner, and dependent '
           'children under 21 \u2014 or under 25 if they are unmarried '
           'full-time students \u2014 including adopted, foster and '
           'step-children.\n'
           '\u2022  The accident must have happened in South Africa. A claim must be '
           'lodged within three years, or within two years for a '
           'hit-and-run.\n'
           '\u2022  We do not guarantee a pay-out, but we make all reasonable '
           'efforts to reach a settlement. Your contributions must be paid '
           'up at the time of the accident, and your information must be '
           'complete and accurate.', size=9.0, color=TERMS, lead=1.36)

    p.para(309.8, 397.9, 550, 491.7,
           '\u2022  Free Wills is provided by qualified Wills and Trusts '
           'professionals. Project Help is the entry point only and passes '
           'your call-back request on.\n'
           '\u2022  All legal advice and drafting is handled directly between '
           'you and the provider, under their own terms.\n'
           '\u2022  The Will is free to start. Any further services or fees '
           'are agreed between you and the provider.', size=9.0, color=TERMS)
    p.commit()


def terms_two(doc):
    p = Page(doc, 8)
    p.para(168.0, 687.2, 428, 704.2, 'Email  support@projecthelp.co.za',
           size=13.5, weight='SemiBold', color=WHITE, align=1, fill=NAVY,
           lead=1.26)
    p.commit()


def footers(doc):
    for n in range(1, 8):
        p = Page(doc, n)
        p.para(42.0, 804.4, 150.0, 815.7, 'Auto Pedigree 24/7', size=9.0,
               weight='SemiBold', color=MUTE, lead=1.26)
        p.commit()


def main():
    if not os.path.exists(SRC):
        sys.exit(f'missing {SRC}')
    doc = pymupdf.open(SRC)
    qr = qr_png('/tmp/ap247-qr.png')

    cover(doc, qr)
    armed(doc)
    raf(doc)
    screens(doc)
    wills(doc)
    started(doc, qr)
    terms_one(doc)
    terms_two(doc)
    footers(doc)

    doc.save(OUT, garbage=4, deflate=True)
    note = ('  [set in Inter: ' + ', '.join(sorted(SUBSTITUTED)) + ']'
            if SUBSTITUTED else '')
    print(f'wrote {os.path.relpath(OUT)} '
          f'({os.path.getsize(OUT) / 1024:.0f} KB){note}')


if __name__ == '__main__':
    main()
