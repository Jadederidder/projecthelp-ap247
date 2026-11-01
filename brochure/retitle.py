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
HOME_ASPECT = 738 / 1600   # a full device capture, like every other screen

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

    def dot(self, cx, cy, r, color):
        self._draw.append(('dot', (cx, cy, r, 0), None, None, None, color,
                           0, None))
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
                    sh.draw_rect(r, radius=extra)
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
            elif kind == 'dot':
                cx, cy, r, _ = box
                sh = self.page.new_shape()
                sh.draw_circle(pymupdf.Point(cx, cy), r)
                sh.finish(fill=color, color=color)
                sh.commit()
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


# The mockups on the licence, fines and wills pages are all one shape: a
# filled body, the screen inset inside it, and a camera dot drawn on top of
# the screen. Measured off the licence page -- body 169.5 x 353.2, screen
# inset 6pt, corner radius 25.5pt, dot 7.5pt across, its centre 15pt below
# the body's top edge -- and held as ratios so a phone of any size matches.
PHONE_BODY = (0.043, 0.090, 0.149)
PHONE_INSET = 6.0 / 353.2          # of the body height
PHONE_RADIUS = 25.5 / 169.5        # of the body width (the shorter side)
PHONE_DOT = 7.5 / 169.5            # of the body width
PHONE_DOT_Y = 14.95 / 169.5        # of the body width, below the body top


def draw_phone(p, centre_x, top, height, screenshot, aspect, dot=True):
    """Body, screen and camera dot, in the proportions this document uses.

    dot=False for a screenshot that has no status bar of its own: on the
    other pages the camera sits in the status bar, and on a screen that
    starts straight into the app it would land on top of the UI.
    """
    inset = height * PHONE_INSET
    screen_h = height - inset * 2
    screen_w = screen_h * aspect
    body_w = screen_w + inset * 2
    x0, x1 = centre_x - body_w / 2, centre_x + body_w / 2
    p.rect(x0, top, x1, top + height, PHONE_BODY, radius=PHONE_RADIUS)
    p.image(x0 + inset, top + inset, x1 - inset, top + height - inset,
            screenshot)
    if dot:
        p.dot(centre_x, top + body_w * PHONE_DOT_Y,
              body_w * PHONE_DOT / 2, PHONE_BODY)
    return pymupdf.Rect(x0, top, x1, top + height)


def icon_svg(path_d, colour):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            f'<path fill="{colour}" d="{path_d}"/></svg>')


# The RAF van, lifted from the service strip on ap247.projecthelp.co.za so the
# brochure and the landing page carry the same mark.
TILE_LABEL = (0x1e / 255, 0x2a / 255, 0x36 / 255)
RED_TILE = (0.9843, 0.9137, 0.9098)
GREEN_TILE = (0.9176, 0.9529, 0.8863)
BLUE_TILE = (0.9098, 0.9333, 0.9569)
VIOLET_TILE = (0.9333, 0.9176, 0.9686)

# The service marks, the same paths the landing page uses.
SHIELD = ('M12 2 4 5.5v5.8c0 5 3.4 9.7 8 10.7 4.6-1 8-5.7 8-10.7V5.5L12 2Z'
          'm1 14h-2v-2h2v2Zm0-4h-2V7h2v5Z')
LICENCE = 'M3 5h18v14H3V5Zm2 3v2h7V8H5Zm0 4v2h5v-2H5Zm9-4v6h5V8h-5Z'
FINES = ('M4 4h16v16H4V4Zm2.5 3v2h11V7h-11Zm0 4v2h11v-2h-11Zm0 4v2h7v-2h-7Z')
WILL = ('M6 2h8l4 4v16H6V2Zm7 1.5V7h3.5L13 3.5ZM8 11v1.6h8V11H8Zm0 4v1.6h8'
        'V15H8Z')
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
    left, limit, baseline = 42.0, 354.0, 345.0
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
           RED, radius=0.12)
    p.line(box_x + size * 0.26, baseline, '24/7', size=size, weight='ExtraBold',
           color=WHITE)

    # --- Auto Pedigree does not carry medical response: the member already
    # has it from another provider. It comes out of the brochure until it is
    # part of the product.
    p.para(42, 398.5, 345, 452.7,
           'Over 5000 Armed Responders protecting you and your family. Hold '
           'one button to reach the closest response vehicles from a '
           'nationwide network.',
           size=12.0, color=(0xd5 / 255, 0xde / 255, 0xe8 / 255), fill=NAVY)

    # --- second cover paragraph: Mental Health is not part of this product.
    p.para(42, 468.3, 345, 502.9,
           'If you are ever injured in a road accident, the RAF button '
           'starts your claim at no cost to you.',
           size=12.0, color=(0xd5 / 255, 0xde / 255, 0xe8 / 255), fill=NAVY)

    # --- service strip. Mental Health leaves, RAF goes to the end, and the
    # three between it shuffle up one slot, so four of the five tiles are
    # redrawn. Slot 1 keeps its shield and only loses the word "Medical".
    # The old shield carried a medical cross. Without medical response that
    # mark would promise something the product does not include.
    p.erase(58.0, 660.0, 112.0, 711.0)
    p.rect(62.2, 663.0, 107.2, 708.0, RED_TILE, radius=0.24)
    p.svg(72.9, 673.5, 96.5, 697.1, icon_svg(SHIELD, '#d0312d'))
    p.para(34, 718.0, 136, 744.0, 'Armed Response', size=9.75, weight='Bold',
           color=TILE_LABEL, align=1, lead=1.26, pad=3.0)
    for slot, (tint, glyph, colour, label) in enumerate((
        (BLUE_TILE, LICENCE, '#1f3a55', 'Licence Disc\nRenewal'),
        (BLUE_TILE, FINES, '#1f3a55', 'Fines Payment'),
        (VIOLET_TILE, WILL, '#6b4ce0', 'Free Wills'),
        (GREEN_TILE, VAN, '#3f7a1c', 'RAF Claims'),
    ), start=2):
        cx = 62.2 + (slot - 1) * 106.5 + 22.5
        p.erase(cx - 52, 660.0, cx + 52, 745.0)
        p.rect(cx - 22.5, 663.0, cx + 22.5, 708.0, tint, radius=0.24)
        p.svg(cx - 11.8, 673.5, cx + 11.8, 697.1, icon_svg(glyph, colour))
        p.para(cx - 52, 718.0 if '\n' not in label else 715.1,
               cx + 52, 748.0, label, size=9.75, weight='Bold',
               color=TILE_LABEL, align=1, lead=1.26, pad=0.0)

    # --- the QR took you to the Premium Help listing.
    p.erase(114.0, 754.5, 177.0, 817.5)
    p.image(116.3, 756.8, 174.7, 815.2, qr)

    # --- the hero mockup was a design of an app that was never shipped.
    #
    # The phone is two objects: a filled rounded rectangle for the body, and
    # the screen as a bitmap inset 6pt inside it. The real home screen is a
    # wider phone than the one that was drawn here (0.515 against 0.462), so
    # forcing it into the old slot either squashed it or left black bands
    # down the sides. The body is redrawn to the screenshot's proportions
    # instead, at the same height and on the same centre line, and the
    # screen is placed inside it.
    #
    # Nothing is erased: a redaction rectangle here would punch a white hole
    # in the cover photograph. The new body is wider than the old one in
    # every direction that matters, so it covers it.
    p.blank_image(67)
    draw_phone(p, 450.0, 225.8, 324.0,
               os.path.join(ASSETS, 'app-home-screen.png'), HOME_ASPECT)

    # --- the badge logo was a 170px bitmap blown up, and looked it
    p.swap_image(64, os.path.join(ASSETS, 'project-help-logo.png'))
    p.commit()


def armed(doc):
    p = Page(doc, 1)
    # Medical response is not part of Auto Pedigree: the member already has
    # it from another provider. Until that changes it is out of the brochure.
    p.erase(38, 249, 440, 292, fill=WHITE)
    p.line(42.0, 281.0, 'Armed', size=27.0, weight='ExtraBold', color=RED)
    p.line(42.0 + measure('Armed ', 'ExtraBold', 27.0), 281.0, 'Response',
           size=27.0, weight='ExtraBold', color=HEAD)
    p.para(42, 151.8, 290, 205.2,
           'Cutting edge technology combined with GPS connects you to the '
           'best armed responders in the country.',
           size=12.0, color=(0xd5 / 255, 0xde / 255, 0xe8 / 255), fill=NAVY)

    # The phone in the dispatch illustration is part of one bitmap with the
    # response pins, so it cannot be swapped on its own. Its body is redrawn
    # over the top at the real screenshot's proportions and the home screen
    # placed inside, which also takes the Mental Health tile off a page that
    # no longer sells it.
    draw_phone(p, 355.0, 549.8, 199.0,
               os.path.join(ASSETS, 'app-home-screen.png'), HOME_ASPECT)
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
         "Tap RAF on the app's home screen to start a claim."),
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
           'security emergency costs R450.00 (excl VAT).', size=10.5)
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
    """Page 8. Medical assistance was most of the left column and the top of
    the right one. Taking it out would have left a third of the page blank in
    the middle, so the sections after it move up: RAF Assist into the space
    medical left in the left column, Free Wills and Fines Assist up the right
    column. The white space ends up at the foot of the page, where it reads
    as the end of the text rather than as a hole in it."""
    p = Page(doc, 7)

    p.para(52.5, 106.9, 285, 131.7,
           'Your Auto Pedigree 24/7 membership remains active for as long as '
           'you pay your weekly fee of R23.00.', size=9.0, color=TERMS)
    p.para(52.5, 236.7, 285, 260.7,
           'Payments are deducted weekly. Services cease if payments stop.',
           size=9.0, color=TERMS)
    p.para(52.5, 265.2, 290, 289.2,
           'You can cancel your membership on 30 days\u2019 notice by email '
           'to support@projecthelp.co.za.', size=9.0, color=TERMS)
    p.para(52.5, 321.4, 285, 345.5,
           'Payments are debited weekly with the reference "ProjectHelp".',
           size=9.0, color=TERMS)

    # 1. Armed Response -- the "and Medical" half of the section goes
    p.erase(38, 410, 290, 430)
    p.line(42.0, 424.0, '1. Armed Response', size=9.75, weight='ExtraBold',
           color=HEAD)
    p.para(42, 449.7, 290, 512.7,
           'A genuine emergency is never charged for. Fair use is 4 armed '
           'response call-outs per covered person every 12 months. R450.00 '
           '(VAT exclusive) applies only to a call-out that is not a '
           'security emergency, or beyond the fair-use allowance.',
           size=9.0, color=TERMS)

    # everything medical, and the two columns it occupied
    p.erase(38, 516, 292, 790)
    p.erase(305, 64, 556, 745)

    # 2. RAF Assist, moved into the left column
    p.line(42.0, 530.0, '2. RAF Assist', size=9.75, weight='ExtraBold',
           color=HEAD)
    p.para(42, 545.0, 290, 740.0,
           '\u2022  RAF Assist is not an insurance product. It is a service '
           'that helps you claim from the Road Accident Fund.\n'
           '\u2022  It covers the main member, your spouse or partner, and '
           'dependent children under 21 \u2014 or under 25 if they are '
           'unmarried full-time students \u2014 including adopted, foster '
           'and step-children.\n'
           '\u2022  The accident must have happened in South Africa. A claim '
           'must be lodged within three years, or within two years for a '
           'hit-and-run.\n'
           '\u2022  We do not guarantee a pay-out, but we make all '
           'reasonable efforts to reach a settlement. Your contributions '
           'must be paid up at the time of the accident, and your '
           'information must be complete and accurate.',
           size=9.0, color=TERMS)

    # right column, all of it moved up
    p.para(309.8, 69.4, 548, 108.0,
           'Subscription fees are payable weekly in advance. No refunds are '
           'given on payments already taken. Full terms and conditions: '
           'www.projecthelp.co.za/terms', size=9.0, color=TERMS)

    p.line(309.8, 127.0, '3. Free Wills', size=9.75, weight='ExtraBold',
           color=HEAD)
    p.para(309.8, 142.0, 550, 236.0,
           '\u2022  Free Wills is provided by qualified Wills and Trusts '
           'professionals. Project Help is the entry point only and passes '
           'your call-back request on.\n'
           '\u2022  All legal advice and drafting is handled directly '
           'between you and the provider, under their own terms.\n'
           '\u2022  The Will is free to start. Any further services or fees '
           'are agreed between you and the provider.', size=9.0, color=TERMS)

    p.line(309.8, 258.0, '4. Fines Assist Benefit', size=9.75,
           weight='ExtraBold', color=HEAD)
    p.line(309.8, 280.0, 'Authorisation', size=9.0, weight='Bold', color=HEAD)
    p.para(309.8, 292.0, 550, 346.0,
           'You authorise Fines Assist to collect and process all fines '
           'information from all relevant authorities across Southern Africa '
           'using the ID number provided in your membership application.',
           size=9.0, color=TERMS)
    p.line(309.8, 368.0, 'Services', size=9.0, weight='Bold', color=HEAD)
    p.para(309.8, 380.0, 550, 447.0,
           'Fines Assist gives you a monthly report of all fines linked to '
           'your ID number across South Africa and lets you settle fines '
           'through our payment options. We provide proof of payment once '
           'fines are settled. A service fee of R8.00 applies to all fine '
           'payments.', size=9.0, color=TERMS)
    p.line(309.8, 469.0, 'Service disclaimer', size=9.0, weight='Bold',
           color=HEAD)
    p.para(309.8, 481.0, 550, 535.0,
           'Project Help and its Vendors operate this service with all '
           'reasonable care, skill, policies, procedures and security '
           'measures. Except as set out in these terms, no warranties are '
           'given for this service.', size=9.0, color=TERMS)
    p.commit()


def terms_two(doc):
    p = Page(doc, 8)
    p.swap_image(441, os.path.join(ASSETS, 'project-help-logo.png'))
    p.para(168.0, 687.2, 428, 704.2, 'Email  support@projecthelp.co.za',
           size=13.5, weight='SemiBold', color=WHITE, align=1, fill=NAVY,
           lead=1.26)
    p.commit()


# Cover, armed response, licence, fines, wills, RAF, getting started, terms.
# RAF Assist moves to the end of the services, where JD wants it; everything
# else keeps its order. The T&C sections are not renumbered, because they
# never ran in page order in the first place.
ORDER = [0, 1, 3, 4, 5, 2, 6, 7, 8]


def footers(doc):
    """Run last, after the reorder: the page number has to match where the
    page ended up, not where it started."""
    for n in range(1, 8):
        p = Page(doc, n)
        p.erase(38.0, 801.0, 556.0, 819.0)
        p.para(42.0, 804.4, 160.0, 815.7, 'Auto Pedigree 24/7', size=9.0,
               weight='SemiBold', color=MUTE, lead=1.26)
        p.para(480.0, 804.4, 553.5, 815.7, str(n + 1), size=9.0,
               weight='SemiBold', color=MUTE, align=2, lead=1.26)
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

    doc.select(ORDER)
    footers(doc)

    doc.save(OUT, garbage=4, deflate=True)
    note = ('  [set in Inter: ' + ', '.join(sorted(SUBSTITUTED)) + ']'
            if SUBSTITUTED else '')
    print(f'wrote {os.path.relpath(OUT)} '
          f'({os.path.getsize(OUT) / 1024:.0f} KB){note}')


if __name__ == '__main__':
    main()
