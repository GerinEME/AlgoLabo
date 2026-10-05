# -*- coding: utf-8 -*-
"""Rendu Tkinter et PIL des algorigrammes (FlowchartRenderer, _PilFlowRenderer)."""

import os
import math
import tkinter as tk

# =====================================================================
# Constantes de geometrie
# =====================================================================
FC_BW  = 170   # largeur boite
FC_BH  = 38    # hauteur boite
FC_DW  = 180   # largeur losange
FC_DH  = 52    # hauteur losange
FC_OW  = 120   # largeur ovale
FC_OH  = 34    # hauteur ovale
FC_VG  = 22    # ecart vertical entre elements
FC_BHG = 60    # ecart horizontal entre branches SI
FC_LM  = 44    # marge gauche pour fleche de retour (boucles)
FC_RM  = 44    # marge droite pour sortie Non


class FlowchartRenderer:
    CA = '#4472C4'                            # fleches
    CB_F = '#FFFFFF'; CB_B = '#4472C4'        # boite standard
    CI_F = '#EAF4E8'; CI_B = '#2E9E58'        # parallelogramme E/S
    CD_F = '#FFF3CD'; CD_B = '#FFA94D'        # losange condition
    CO_F = '#D6E4F0'; CO_B = '#4472C4'        # ovale debut/fin
    CD2F = '#F0F4FF'; CD2B = '#B98BFF'        # declaration variable
    CT   = '#1F2733'; CL   = '#64708A'        # texte / label

    def __init__(self, canvas):
        self.c = canvas

    # ── primitives ─────────────────────────────────────────────────

    def _t(self, cx, cy, txt, sz=9):
        self.c.create_text(cx, cy, text=txt, font=('Segoe UI', sz),
                           fill=self.CT, justify='center', width=FC_BW - 6)

    def _arr(self, x, y1, y2, lbl='', ls='e'):
        if y2 <= y1:
            return
        self.c.create_line(x, y1, x, y2, fill=self.CA, width=2,
                           arrow='last', arrowshape=(8, 10, 4))
        if lbl:
            ox = x + 4 if ls == 'e' else x - 4
            an = 'nw' if ls == 'e' else 'ne'
            self.c.create_text(ox, y1 + 2, text=lbl,
                               font=('Segoe UI', 8, 'italic'), fill=self.CL, anchor=an)

    def _ln(self, pts, arrow=False):
        kw = dict(fill=self.CA, width=2)
        if arrow:
            kw.update(arrow='last', arrowshape=(8, 10, 4))
        self.c.create_line(pts, **kw)

    def _lbl(self, x, y, txt, an='nw'):
        self.c.create_text(x, y, text=txt, font=('Segoe UI', 8, 'italic'),
                           fill=self.CL, anchor=an)

    # ── formes ────────────────────────────────────────────────────

    def _rect(self, cx, cy, w, h, txt, ff, fb):
        self.c.create_rectangle(cx-w/2, cy-h/2, cx+w/2, cy+h/2,
                                fill=ff, outline=fb, width=2)
        self._t(cx, cy, txt)
        return cy + h / 2

    def _para(self, cx, cy, w, h, txt):
        sk = 10
        self.c.create_polygon(
            [cx-w/2+sk, cy-h/2, cx+w/2+sk, cy-h/2,
             cx+w/2-sk, cy+h/2, cx-w/2-sk, cy+h/2],
            fill=self.CI_F, outline=self.CI_B, width=2)
        self._t(cx, cy, txt)
        return cy + h / 2

    def _diam(self, cx, cy, w, h, txt):
        self.c.create_polygon(
            [cx, cy-h/2, cx+w/2, cy, cx, cy+h/2, cx-w/2, cy],
            fill=self.CD_F, outline=self.CD_B, width=2)
        self._t(cx, cy, txt)
        return cy + h / 2

    def _oval(self, cx, cy, w, h, txt, ff, fb):
        self.c.create_oval(cx-w/2, cy-h/2, cx+w/2, cy+h/2,
                           fill=ff, outline=fb, width=2)
        self._t(cx, cy, txt, sz=10)
        return cy + h / 2

    # ── passe mesure ─────────────────────────────────────────────

    def _mw(self, stmts):
        if not stmts:
            return FC_BW
        return max(self._mw1(s) for s in stmts)

    def _mw1(self, s):
        t = s['type']
        if t in ('AFFECT', 'AFFECT_INDEX', 'LIRE', 'LIRE_INDEX', 'ECRIRE'):
            return FC_BW
        if t == 'SI':
            tw = self._mw(s['thenBlock'])
            if s['elseBlock']:
                ew = self._mw(s['elseBlock'])
                return max(FC_DW, tw + FC_BHG + ew)
            return max(FC_DW + FC_RM, FC_DW + tw)
        if t in ('TANT_QUE', 'POUR'):
            bw = self._mw(s['block'])
            return max(FC_DW, bw) + FC_LM + FC_RM
        return FC_BW

    # ── passe dessin ─────────────────────────────────────────────

    def draw_stmts(self, stmts, cx, top_y):
        y = top_y
        for i, s in enumerate(stmts):
            bot = self._draw1(s, cx, y)
            if i < len(stmts) - 1:
                self._arr(cx, bot, bot + FC_VG)
                y = bot + FC_VG
            else:
                y = bot
        return y

    def _draw1(self, s, cx, ty):
        t = s['type']
        cy = ty + FC_BH / 2
        if t == 'AFFECT':
            return self._rect(cx, cy, FC_BW, FC_BH,
                              s['name'] + ' ← ' + self._e(s['expr']),
                              self.CB_F, self.CB_B)
        if t == 'AFFECT_INDEX':
            return self._rect(cx, cy, FC_BW, FC_BH,
                              s['name'] + '[i] ← ' + self._e(s['expr']),
                              self.CB_F, self.CB_B)
        if t == 'LIRE':
            return self._para(cx, cy, FC_BW, FC_BH, 'Lire ' + s['name'])
        if t == 'LIRE_INDEX':
            return self._para(cx, cy, FC_BW, FC_BH, 'Lire ' + s['name'] + '[i]')
        if t == 'ECRIRE':
            return self._para(cx, cy, FC_BW, FC_BH, 'Ecrire ' + self._e(s['expr']))
        if t == 'SI':
            return self._si(s, cx, ty)
        if t == 'TANT_QUE':
            return self._tantque(s, cx, ty)
        if t == 'POUR':
            return self._pour(s, cx, ty)
        return ty + FC_BH

    def _si(self, s, cx, ty):
        has_else = bool(s['elseBlock'])
        dcy  = ty + FC_DH / 2
        self._diam(cx, dcy, FC_DW, FC_DH, self._e(s['cond']))
        dbot = dcy + FC_DH / 2
        dlft = cx - FC_DW / 2
        drgt = cx + FC_DW / 2
        btop = dbot + FC_VG

        if has_else:
            tw  = max(self._mw(s['thenBlock']), FC_BW)
            ew  = max(self._mw(s['elseBlock']), FC_BW)
            tcx = cx - FC_BHG / 2 - tw / 2
            ecx = cx + FC_BHG / 2 + ew / 2
            self._ln([dlft, dcy, tcx, dcy])
            self._lbl(dlft - 4, dcy - 13, 'Oui', 'ne')
            self._arr(tcx, dcy, btop)
            self._ln([drgt, dcy, ecx, dcy])
            self._lbl(drgt + 4, dcy - 13, 'Non', 'nw')
            self._arr(ecx, dcy, btop)
            te = self.draw_stmts(s['thenBlock'], tcx, btop)
            ee = self.draw_stmts(s['elseBlock'], ecx, btop)
            my = max(te, ee) + FC_VG / 2
            self._ln([tcx, te, tcx, my])
            self._ln([ecx, ee, ecx, my])
            self._ln([tcx, my, cx, my], arrow=True)
            self._ln([ecx, my, cx, my])
            return my
        else:
            self._arr(cx, dbot, btop, 'Oui')
            te  = self.draw_stmts(s['thenBlock'], cx, btop)
            my  = te + FC_VG / 2
            rx  = drgt + FC_RM
            self._ln([drgt, dcy, rx, dcy])
            self._lbl(drgt + 4, dcy - 13, 'Non', 'nw')
            self._ln([rx, dcy, rx, my])
            self._ln([rx, my, cx, my], arrow=True)
            self._ln([cx, te, cx, my])
            return my

    def _tantque(self, s, cx, ty):
        dcy  = ty + FC_DH / 2
        self._diam(cx, dcy, FC_DW, FC_DH, self._e(s['cond']))
        dbot = dcy + FC_DH / 2
        dlft = cx - FC_DW / 2
        drgt = cx + FC_DW / 2
        btop = dbot + FC_VG
        self._arr(cx, dbot, btop, 'Oui')
        be   = self.draw_stmts(s['block'], cx, btop)
        lx   = cx - max(FC_DW / 2, self._mw(s['block']) / 2) - FC_LM
        ly   = be + FC_VG / 2
        self._ln([cx, be, cx, ly])
        self._ln([cx, ly, lx, ly])
        self._ln([lx, ly, lx, dcy])
        self._ln([lx, dcy, dlft, dcy], arrow=True)
        ey   = ly + FC_VG / 2
        rx   = drgt + FC_RM
        self._ln([drgt, dcy, rx, dcy])
        self._lbl(drgt + 4, dcy - 13, 'Non', 'nw')
        self._ln([rx, dcy, rx, ey])
        self._ln([rx, ey, cx, ey], arrow=True)
        return ey

    def _pour(self, s, cx, ty):
        icy = ty + FC_BH / 2
        ib  = self._rect(cx, icy, FC_BW, FC_BH,
                         s['varName'] + ' ← ' + self._e(s['fromExpr']),
                         self.CB_F, self.CB_B)
        ct  = ib + FC_VG
        self._arr(cx, ib, ct)
        dcy  = ct + FC_DH / 2
        self._diam(cx, dcy, FC_DW, FC_DH,
                   s['varName'] + ' <= ' + self._e(s['toExpr']))
        dbot = dcy + FC_DH / 2
        dlft = cx - FC_DW / 2
        drgt = cx + FC_DW / 2
        btop = dbot + FC_VG
        self._arr(cx, dbot, btop, 'Oui')
        be   = self.draw_stmts(s['block'], cx, btop)
        it   = be + FC_VG
        self._arr(cx, be, it)
        icy2 = it + FC_BH / 2
        ib2  = self._rect(cx, icy2, FC_BW, FC_BH,
                          s['varName'] + ' ← ' + s['varName'] + ' + 1',
                          self.CB_F, self.CB_B)
        lx   = cx - max(FC_DW / 2, self._mw(s['block']) / 2) - FC_LM
        ly   = ib2 + FC_VG / 2
        self._ln([cx, ib2, cx, ly])
        self._ln([cx, ly, lx, ly])
        self._ln([lx, ly, lx, dcy])
        self._ln([lx, dcy, dlft, dcy], arrow=True)
        ey   = ly + FC_VG / 2
        rx   = drgt + FC_RM
        self._ln([drgt, dcy, rx, dcy])
        self._lbl(drgt + 4, dcy - 13, 'Non', 'nw')
        self._ln([rx, dcy, rx, ey])
        self._ln([rx, ey, cx, ey], arrow=True)
        return ey

    # ── expression -> chaine abregee ─────────────────────────────

    def _e(self, n, d=0):
        if d > 4:
            return '...'
        t = n['type']
        if t == 'num':
            v = n['value']
            return str(int(v)) if isinstance(v, float) and v.is_integer() else str(v)
        if t == 'str':
            s = n['value']
            return '"' + (s[:10] + '..' if len(s) > 10 else s) + '"'
        if t == 'bool':
            return 'VRAI' if n['value'] else 'FAUX'
        if t == 'var':
            return n['name']
        if t == 'index':
            return n['name'] + '[' + self._e(n['indexExpr'], d+1) + ']'
        if t == 'longueur':
            return 'LG(' + n['name'] + ')'
        if t == 'alea':
            if 'fromExpr' not in n:
                return 'ALEA()'
            return 'ALEA(' + self._e(n['fromExpr'], d+1) + ',' + self._e(n['toExpr'], d+1) + ')'
        if t in ('arith', 'compare', 'logic'):
            return self._e(n['left'], d+1) + ' ' + n['op'] + ' ' + self._e(n['right'], d+1)
        if t == 'neg':
            return '-' + self._e(n['expr'], d+1)
        if t == 'not':
            return 'NON ' + self._e(n['expr'], d+1)
        return '?'

    # ── point d'entree principal ──────────────────────────────────

    def render(self, program):
        self.c.delete('all')
        mw = self._mw(program['body'])
        cx = max(int(mw // 2) + FC_LM + 20, FC_BW // 2 + 70)
        y  = 24

        self._oval(cx, y + FC_OH/2, FC_OW, FC_OH, 'DEBUT', self.CO_F, self.CO_B)
        y += FC_OH
        self._arr(cx, y, y + FC_VG)
        y += FC_VG

        for d in program['declarations']:
            cy = y + FC_BH / 2
            b  = self._rect(cx, cy, FC_BW, FC_BH,
                            d['name'] + ' : ' + d['vtype'],
                            self.CD2F, self.CD2B)
            y = b
            self._arr(cx, y, y + FC_VG)
            y += FC_VG

        ey = self.draw_stmts(program['body'], cx, y)
        y  = ey
        self._arr(cx, y, y + FC_VG)
        y += FC_VG
        self._oval(cx, y + FC_OH/2, FC_OW, FC_OH, 'FIN', self.CO_F, self.CO_B)
        y += FC_OH + 24
        self.c.configure(scrollregion=(0, 0, cx * 2 + FC_RM + 60, y))


class _PilFlowRenderer(FlowchartRenderer):
    """Genere une image PIL de la totalite de l'algorigramme (sans capture ecran)."""

    def __init__(self):
        super().__init__(None)          # self.c = None, jamais utilise
        self._img = self._draw = None
        self._fn = self._fi = self._fn2 = None

    # -- chargement polices ---------------------------------------------
    def _load_fonts(self):
        from PIL import ImageFont
        dirs = [
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'),
            '/usr/share/fonts/truetype/dejavu',
            '/usr/share/fonts/truetype/freefont',
            '/Library/Fonts',
            '/System/Library/Fonts',
        ]
        def ttf(names, size):
            for nm in names:
                for d in dirs:
                    try:
                        return ImageFont.truetype(os.path.join(d, nm), size)
                    except (IOError, OSError):
                        pass
            try:
                return ImageFont.load_default(size=size)
            except TypeError:
                return ImageFont.load_default()
        self._fn  = ttf(['segoeui.ttf',  'DejaVuSans.ttf',         'Arial.ttf'], 12)
        self._fi  = ttf(['segoeuii.ttf', 'DejaVuSans-Oblique.ttf', 'Arial.ttf'], 11)
        self._fn2 = ttf(['segoeui.ttf',  'DejaVuSans.ttf',         'Arial.ttf'], 13)

    # -- mesure texte ---------------------------------------------------
    @staticmethod
    def _fsz(font, txt):
        try:
            bb = font.getbbox(txt)
            return bb[2] - bb[0], bb[3] - bb[1]
        except (AttributeError, TypeError):
            try:
                return font.getsize(txt)
            except AttributeError:
                return len(txt) * 6, 12

    def _wrap(self, txt, max_w, font):
        words = txt.split()
        if not words:
            return ['']
        lines, cur = [], []
        for w in words:
            test = ' '.join(cur + [w])
            if cur and self._fsz(font, test)[0] > max_w:
                lines.append(' '.join(cur))
                cur = [w]
            else:
                cur.append(w)
        if cur:
            lines.append(' '.join(cur))
        return lines or ['']

    # -- primitives (override FlowchartRenderer) -----------------------
    def _t(self, cx, cy, txt, sz=9):
        font = self._fn2 if sz >= 10 else self._fn
        lines = self._wrap(txt, FC_BW - 6, font)
        _, fh = self._fsz(font, 'Ag')
        lh = fh + 2
        y0 = cy - lh * len(lines) / 2
        for line in lines:
            lw, _ = self._fsz(font, line)
            self._draw.text((cx - lw / 2, y0), line, font=font, fill=self.CT)
            y0 += lh

    def _lbl(self, x, y, txt, an='nw'):
        lw, lh = self._fsz(self._fi, txt)
        tx = x - lw if an in ('ne', 'se') else x
        ty = y - lh if an in ('se', 'sw') else y
        self._draw.text((tx, ty), txt, font=self._fi, fill=self.CL)

    def _arr(self, x, y1, y2, lbl='', ls='e'):
        if y2 <= y1:
            return
        self._draw.line([(x, y1), (x, y2)], fill=self.CA, width=2)
        self._draw.polygon([(x, y2), (x - 4, y2 - 8), (x + 4, y2 - 8)],
                           fill=self.CA)
        if lbl:
            ox = x + 4 if ls == 'e' else x - 4
            lw, _ = self._fsz(self._fi, lbl)
            tx = ox if ls == 'e' else ox - lw
            self._draw.text((tx, y1 + 2), lbl, font=self._fi, fill=self.CL)

    def _ln(self, pts, arrow=False):
        coords = [(pts[i], pts[i + 1]) for i in range(0, len(pts), 2)]
        self._draw.line(coords, fill=self.CA, width=2)
        if arrow and len(coords) >= 2:
            (x1, y1), (x2, y2) = coords[-2], coords[-1]
            dx, dy = x2 - x1, y2 - y1
            lg = math.hypot(dx, dy)
            if lg:
                ux, uy = dx / lg, dy / lg
                px, py = -uy, ux
                L, W = 10, 4
                b1 = (x2 - ux * L + px * W, y2 - uy * L + py * W)
                b2 = (x2 - ux * L - px * W, y2 - uy * L - py * W)
                self._draw.polygon([(x2, y2), b1, b2], fill=self.CA)

    def _rect(self, cx, cy, w, h, txt, ff, fb):
        x0, y0 = cx - w / 2, cy - h / 2
        x1, y1 = cx + w / 2, cy + h / 2
        self._draw.rectangle([x0, y0, x1, y1], fill=ff, outline=fb, width=2)
        self._t(cx, cy, txt)
        return cy + h / 2

    def _para(self, cx, cy, w, h, txt):
        sk = 10
        poly = [(cx - w/2 + sk, cy - h/2), (cx + w/2 + sk, cy - h/2),
                (cx + w/2 - sk, cy + h/2), (cx - w/2 - sk, cy + h/2)]
        self._draw.polygon(poly, fill=self.CI_F)
        self._draw.line(poly + [poly[0]], fill=self.CI_B, width=2)
        self._t(cx, cy, txt)
        return cy + h / 2

    def _diam(self, cx, cy, w, h, txt):
        poly = [(cx, cy - h/2), (cx + w/2, cy),
                (cx, cy + h/2), (cx - w/2, cy)]
        self._draw.polygon(poly, fill=self.CD_F)
        self._draw.line(poly + [poly[0]], fill=self.CD_B, width=2)
        self._t(cx, cy, txt)
        return cy + h / 2

    def _oval(self, cx, cy, w, h, txt, ff, fb):
        x0, y0 = cx - w / 2, cy - h / 2
        x1, y1 = cx + w / 2, cy + h / 2
        self._draw.ellipse([x0, y0, x1, y1], fill=ff, outline=fb, width=2)
        self._t(cx, cy, txt, sz=10)
        return cy + h / 2

    # -- point d'entree ------------------------------------------------
    def to_image(self, program):
        from PIL import Image, ImageDraw
        self._load_fonts()
        mw = self._mw(program['body'])
        cx = max(int(mw // 2) + FC_LM + 20, FC_BW // 2 + 70)
        w  = cx * 2 + FC_RM + 80
        self._img  = Image.new('RGB', (w, 8000), '#FFFFFF')
        self._draw = ImageDraw.Draw(self._img)
        y = 24
        self._oval(cx, y + FC_OH / 2, FC_OW, FC_OH, 'DEBUT', self.CO_F, self.CO_B)
        y += FC_OH
        self._arr(cx, y, y + FC_VG)
        y += FC_VG
        for d in program['declarations']:
            cy = y + FC_BH / 2
            y  = self._rect(cx, cy, FC_BW, FC_BH,
                            d['name'] + ' : ' + d['vtype'],
                            self.CD2F, self.CD2B)
            self._arr(cx, y, y + FC_VG)
            y += FC_VG
        ey = self.draw_stmts(program['body'], cx, y)
        y  = ey
        self._arr(cx, y, y + FC_VG)
        y += FC_VG
        self._oval(cx, y + FC_OH / 2, FC_OW, FC_OH, 'FIN', self.CO_F, self.CO_B)
        y += FC_OH + 24
        return self._img.crop((0, 0, w, int(y)))
