# -*- coding: utf-8 -*-
"""Interface graphique de AlgoLabo (AlgoLaboApp, Tooltip, LineNumbers)."""

import os
import sys
import re
import tkinter as tk
from tkinter import ttk, filedialog

from engine import AlgoError, UserCancelError, run_program, parse_program, RESERVED_WORDS
from flowchart import FlowchartRenderer, _PilFlowRenderer


def resource_path(relative):
    """Chemin vers une ressource — fonctionne en dev et en exe PyInstaller (--onefile)."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative)


# ── Palette de couleurs ───────────────────────────────────────────────
BG          = '#EEF1F5'
PANEL       = '#FFFFFF'
BORDER      = '#DCE2EA'
TEXT        = '#1F2733'
MUTED       = '#64708A'
ACCENT      = '#4472C4'
ACCENT_DARK = '#325590'
ACCENT_SOFT = '#E7EDF9'
EDITOR_BG   = '#1E2430'
GUTTER_BG   = '#161B26'
GUTTER_TEXT = '#4B5875'
EDITOR_TEXT = '#DDE3F0'
OK_COLOR    = '#2E9E58'
ERR_COLOR   = '#D6455A'
ERR_BG      = '#FCEAED'

COL_TYPE  = '#B98BFF'
COL_BLOCK = '#FFA94D'
COL_CTRL  = '#FF7FAE'
COL_BIND  = '#7FA6FF'
COL_STR   = '#5FD68A'
COL_NUM   = '#4FC3F7'
COL_COM   = '#7A8699'
COL_OP    = '#C3C9FF'

# ── Mots-cles (coloration syntaxique) ────────────────────────────────
KW_BLOCK = {'VARIABLES', 'DEBUT_ALGORITHME', 'FIN_ALGORITHME', 'DEBUT_SI', 'FIN_SI',
            'DEBUT_SINON', 'FIN_SINON', 'DEBUT_POUR', 'FIN_POUR', 'DEBUT_TANT_QUE', 'FIN_TANT_QUE',
            'FONCTION', 'DEBUT_FONCTION', 'FIN_FONCTION'}
KW_CTRL  = {'SI', 'ALORS', 'SINON', 'POUR', 'ALLANT_DE', 'A', 'TANT_QUE', 'FAIRE', 'RETOUR'}
KW_TYPE  = {'LIRE', 'AFFICHER', 'ECRIRE', 'NOMBRE', 'TEXTE', 'BOOLEEN', 'LISTE', 'LONGUEUR', 'ALEA',
            'VRAI', 'FAUX'}
KW_BIND  = {'EST_DU_TYPE', 'PREND_LA_VALEUR'}
KW_OPW   = {'ET', 'OU', 'NON', 'MOD', 'DIV'}


def classify_word(word):
    up = word.upper()
    if up in KW_BLOCK: return 'kw_block'
    if up in KW_CTRL:  return 'kw_ctrl'
    if up in KW_TYPE:  return 'kw_type'
    if up in KW_BIND:  return 'kw_bind'
    if up in KW_OPW:   return 'kw_op'
    return None


# ── Contenu editeur par defaut et exemples ───────────────────────────
DEFAULT_CODE = """VARIABLES
DEBUT_ALGORITHME
FIN_ALGORITHME"""

EXAMPLES = [
    ("1. Signe d'un nombre (SI / SINON)", """VARIABLES
  x EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  LIRE x
  SI (x > 0) ALORS
    DEBUT_SI
    ECRIRE "Le nombre est positif"
    FIN_SI
  SINON
    DEBUT_SINON
    SI (x < 0) ALORS
      DEBUT_SI
      ECRIRE "Le nombre est negatif"
      FIN_SI
    SINON
      DEBUT_SINON
      ECRIRE "Le nombre est nul"
      FIN_SINON
    FIN_SINON
FIN_ALGORITHME"""),
    ("2. Somme et parite (POUR + SI)", """VARIABLES
  i EST_DU_TYPE NOMBRE
  n EST_DU_TYPE NOMBRE
  somme EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  LIRE n
  somme PREND_LA_VALEUR 0
  POUR i ALLANT_DE 1 A n
    DEBUT_POUR
    somme PREND_LA_VALEUR somme + i
    SI (i MOD 2 == 0) ALORS
      DEBUT_SI
      ECRIRE i + " est pair"
      FIN_SI
    SINON
      DEBUT_SINON
      ECRIRE i + " est impair"
      FIN_SINON
    FIN_POUR
  ECRIRE "Somme totale : " + somme
FIN_ALGORITHME"""),
    ("3. Jeu du nombre mystere (TANT_QUE)", """VARIABLES
  secret EST_DU_TYPE NOMBRE
  proposition EST_DU_TYPE NOMBRE
  essais EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  secret PREND_LA_VALEUR 7
  essais PREND_LA_VALEUR 0
  proposition PREND_LA_VALEUR 0
  TANT_QUE (proposition != secret ET essais < 5) FAIRE
    DEBUT_TANT_QUE
    LIRE proposition
    essais PREND_LA_VALEUR essais + 1
    SI (proposition == secret) ALORS
      DEBUT_SI
      ECRIRE "Trouve en " + essais + " essai(s) !"
      FIN_SI
    SINON
      DEBUT_SINON
      ECRIRE "Rate, essaie encore"
      FIN_SINON
    FIN_TANT_QUE
FIN_ALGORITHME"""),
    ("4. Table de multiplication (POUR imbrique)", """VARIABLES
  i EST_DU_TYPE NOMBRE
  j EST_DU_TYPE NOMBRE
  produit EST_DU_TYPE NOMBRE
  toutPair EST_DU_TYPE BOOLEEN
DEBUT_ALGORITHME
  toutPair PREND_LA_VALEUR VRAI
  POUR i ALLANT_DE 1 A 3
    DEBUT_POUR
    POUR j ALLANT_DE 1 A 3
      DEBUT_POUR
      produit PREND_LA_VALEUR i * j
      ECRIRE i + " x " + j + " = " + produit
      SI (produit MOD 2 != 0) ALORS
        DEBUT_SI
        toutPair PREND_LA_VALEUR FAUX
        FIN_SI
      FIN_POUR
    FIN_POUR
  ECRIRE "Tous les produits sont pairs : " + toutPair
FIN_ALGORITHME"""),
    ("5. Liste de notes et mention (LISTE + POUR + SI)", """VARIABLES
  notes EST_DU_TYPE LISTE
  i EST_DU_TYPE NOMBRE
  somme EST_DU_TYPE NOMBRE
  moyenne EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  notes[0] PREND_LA_VALEUR 12
  notes[1] PREND_LA_VALEUR 18
  notes[2] PREND_LA_VALEUR 9
  notes[3] PREND_LA_VALEUR 15
  somme PREND_LA_VALEUR 0
  POUR i ALLANT_DE 0 A LONGUEUR(notes) - 1
    DEBUT_POUR
    ECRIRE "Note " + i + " : " + notes[i]
    somme PREND_LA_VALEUR somme + notes[i]
    FIN_POUR
  moyenne PREND_LA_VALEUR somme / LONGUEUR(notes)
  ECRIRE "Moyenne : " + moyenne
  SI (moyenne >= 10) ALORS
    DEBUT_SI
    ECRIRE "Admis"
    FIN_SI
  SINON
    DEBUT_SINON
    ECRIRE "Non admis"
    FIN_SINON
FIN_ALGORITHME"""),
    ("6. Liste de chaines (mots et longueur)", """VARIABLES
  prenoms EST_DU_TYPE LISTE
  i EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  prenoms[0] PREND_LA_VALEUR "Alice"
  prenoms[1] PREND_LA_VALEUR "Bilal"
  prenoms[2] PREND_LA_VALEUR "Chloe"
  POUR i ALLANT_DE 0 A LONGUEUR(prenoms) - 1
    DEBUT_POUR
    ECRIRE prenoms[i]
    FIN_POUR
FIN_ALGORITHME"""),
    ("7. Nombre mystere aleatoire (ALEA + TANT_QUE)", """VARIABLES
  secret EST_DU_TYPE NOMBRE
  proposition EST_DU_TYPE NOMBRE
  essais EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  secret PREND_LA_VALEUR ALEA(1, 100)
  essais PREND_LA_VALEUR 0
  proposition PREND_LA_VALEUR 0
  TANT_QUE (proposition != secret ET essais < 10) FAIRE
    DEBUT_TANT_QUE
    LIRE proposition
    essais PREND_LA_VALEUR essais + 1
    SI (proposition == secret) ALORS
      DEBUT_SI
      ECRIRE "Trouve en " + essais + " essai(s) !"
      FIN_SI
    SINON
      DEBUT_SINON
      SI (proposition < secret) ALORS
        DEBUT_SI
        ECRIRE "Plus grand"
        FIN_SI
      SINON
        DEBUT_SINON
        ECRIRE "Plus petit"
        FIN_SINON
      FIN_SINON
    FIN_TANT_QUE
FIN_ALGORITHME"""),
    ("8. Recherche dichotomique (LISTE + DIV)", """VARIABLES
  L EST_DU_TYPE LISTE
  cible EST_DU_TYPE NOMBRE
  gauche EST_DU_TYPE NOMBRE
  droite EST_DU_TYPE NOMBRE
  milieu EST_DU_TYPE NOMBRE
  trouve EST_DU_TYPE BOOLEEN
DEBUT_ALGORITHME
  L[0] PREND_LA_VALEUR 2
  L[1] PREND_LA_VALEUR 5
  L[2] PREND_LA_VALEUR 9
  L[3] PREND_LA_VALEUR 14
  L[4] PREND_LA_VALEUR 21
  L[5] PREND_LA_VALEUR 30
  LIRE cible
  gauche PREND_LA_VALEUR 0
  droite PREND_LA_VALEUR LONGUEUR(L) - 1
  trouve PREND_LA_VALEUR FAUX
  TANT_QUE (gauche <= droite ET NON trouve) FAIRE
    DEBUT_TANT_QUE
    milieu PREND_LA_VALEUR (gauche + droite) DIV 2
    SI (L[milieu] == cible) ALORS
      DEBUT_SI
      trouve PREND_LA_VALEUR VRAI
      ECRIRE "Trouve a l'indice " + milieu
      FIN_SI
    SINON
      DEBUT_SINON
      SI (L[milieu] < cible) ALORS
        DEBUT_SI
        gauche PREND_LA_VALEUR milieu + 1
        FIN_SI
      SINON
        DEBUT_SINON
        droite PREND_LA_VALEUR milieu - 1
        FIN_SINON
      FIN_SINON
    FIN_TANT_QUE
  SI (NON trouve) ALORS
    DEBUT_SI
    ECRIRE "Absent de la liste"
    FIN_SI
FIN_ALGORITHME"""),
    ("9. Compter les voyelles (chaines de caracteres)", """VARIABLES
  mot EST_DU_TYPE TEXTE
  i EST_DU_TYPE NOMBRE
  nbVoyelles EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  LIRE mot
  nbVoyelles PREND_LA_VALEUR 0
  POUR i ALLANT_DE 0 A LONGUEUR(mot) - 1
    DEBUT_POUR
    SI (mot[i] == "A" OU mot[i] == "E" OU mot[i] == "I" OU mot[i] == "O" OU mot[i] == "U") ALORS
      DEBUT_SI
      nbVoyelles PREND_LA_VALEUR nbVoyelles + 1
      FIN_SI
    FIN_POUR
  ECRIRE "Le mot " + mot + " contient " + nbVoyelles + " voyelle(s)"
FIN_ALGORITHME"""),
    ("10. Fonctions : carre et surface (FONCTION / RETOUR)", """FONCTION carre(valeur)
DEBUT_FONCTION
  RETOUR valeur * valeur
FIN_FONCTION

FONCTION surface(longueur, largeur)
DEBUT_FONCTION
  RETOUR longueur * largeur
FIN_FONCTION

FONCTION afficherTrait()
DEBUT_FONCTION
  ECRIRE "--------------------"
FIN_FONCTION

VARIABLES
  x EST_DU_TYPE NOMBRE
  L EST_DU_TYPE NOMBRE
  l EST_DU_TYPE NOMBRE
  res EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  afficherTrait()
  LIRE x
  res PREND_LA_VALEUR carre(x)
  ECRIRE "Carre de " + x + " = " + res
  afficherTrait()
  LIRE L
  LIRE l
  res PREND_LA_VALEUR surface(L, l)
  ECRIRE "Surface = " + res
  afficherTrait()
FIN_ALGORITHME"""),
]

REFERENCE_TEXT = [
    ('Structure du programme :  ', 'kw_block', 'VARIABLES  DEBUT_ALGORITHME  FIN_ALGORITHME   '),
    ('', 'kw_bind', 'EST_DU_TYPE\n'),
    ('Types :  ', 'kw_type', 'NOMBRE  TEXTE  BOOLEEN  LISTE\n'),
    ('Entrees / sorties :  ', 'kw_type', 'LIRE  ECRIRE  AFFICHER   '),
    ('', 'kw_bind', 'PREND_LA_VALEUR\n'),
    ('Condition :  ', 'kw_ctrl', 'SI  ALORS  SINON   '),
    ('', 'kw_block', 'DEBUT_SI  FIN_SI  DEBUT_SINON  FIN_SINON\n'),
    ('Boucle bornee :  ', 'kw_ctrl', 'POUR  ALLANT_DE  A   '),
    ('', 'kw_block', 'DEBUT_POUR  FIN_POUR\n'),
    ('Boucle conditionnelle :  ', 'kw_ctrl', 'TANT_QUE  FAIRE   '),
    ('', 'kw_block', 'DEBUT_TANT_QUE  FIN_TANT_QUE\n'),
    ('Listes :  ', 'kw_op', 'nom[indice]   '),
    ('', 'kw_type', 'LONGUEUR(nom)\n'),
    ('Chaines :  ', 'kw_op', 'nom[indice]   '),
    ('', 'kw_type', 'LONGUEUR(nom)\n'),
    ('Aleatoire :  ', 'kw_type', 'ALEA(a, b)   ALEA()\n'),
    ('Operateurs :  ', 'kw_op', '+ - * / MOD DIV   < > <= >= == !=   ET  OU  NON\n'),
    ('Valeurs :  ', 'kw_type', 'VRAI  FAUX\n'),
]

REFERENCE_NOTE = (
    "ECRIRE est le mot-cle principal. AFFICHER est accepte comme synonyme.\n"
    "Une LISTE s'indexe a partir de 0 et peut contenir des nombres, des chaines ou\n"
    "des booleens (meme melanges).\n"
    "Une liste entiere ne peut pas etre affichee ou lue directement : indique toujours un indice, ou utilise\n"
    "LONGUEUR(nom) pour la parcourir avec un POUR. Une chaine (TEXTE) se parcourt de la meme facon : mot[i]\n"
    "donne la lettre a l'indice i (a partir de 0) et LONGUEUR(mot) donne son nombre de caracteres.\n"
    "DIV donne la division entiere (17 DIV 5 vaut 3), utile pour les recherches dichotomiques.\n"
    "ALEA(a, b) tire un nombre entier au hasard entre a et b inclus ; ALEA() tire un nombre decimal entre 0 et 1.\n"
    "Toute instruction hors de cette liste est refusee avec un message d'erreur indiquant la ligne concernee.\n"
    "Les commentaires commencent par //."
)


# ── Widgets utilitaires ───────────────────────────────────────────────

class Tooltip:
    """Infobulle affichee au survol d'un widget Tkinter."""

    def __init__(self, widget, text, delay=550):
        self.widget = widget
        self.text   = text
        self.delay  = delay
        self._job   = None
        self._tip   = None
        widget.bind('<Enter>',       self._schedule, add='+')
        widget.bind('<Leave>',       self._cancel,   add='+')
        widget.bind('<ButtonPress>', self._cancel,   add='+')

    def _schedule(self, _e=None):
        self._cancel()
        self._job = self.widget.after(self.delay, self._show)

    def _cancel(self, _e=None):
        if self._job:
            self.widget.after_cancel(self._job)
            self._job = None
        if self._tip:
            self._tip.destroy()
            self._tip = None

    def _show(self):
        if self._tip:
            return
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        frm = tk.Frame(self._tip, bg='#FFFDE7', relief='solid', borderwidth=1)
        frm.pack()
        tk.Label(frm, text=self.text, bg='#FFFDE7', fg='#1F2733',
                 font=('Segoe UI', 9), justify='left',
                 padx=8, pady=5, wraplength=320).pack()
        self._tip.update_idletasks()
        tw = self._tip.winfo_reqwidth()
        th = self._tip.winfo_reqheight()
        sw = self.widget.winfo_screenwidth()
        sh = self.widget.winfo_screenheight()
        x = self.widget.winfo_rootx() + 8
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        if x + tw > sw:
            x = sw - tw - 4
        if y + th > sh:
            y = self.widget.winfo_rooty() - th - 4
        self._tip.wm_geometry(f'+{max(0, x)}+{max(0, y)}')


class LineNumbers(tk.Canvas):
    def __init__(self, master, text_widget, **kwargs):
        super().__init__(master, **kwargs)
        self.text_widget = text_widget

    def redraw(self, *_args):
        self.delete('all')
        i = self.text_widget.index('@0,0')
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split('.')[0]
            self.create_text(52, y, anchor='ne', text=linenum, fill=GUTTER_TEXT, font=('Consolas', 11))
            i = self.text_widget.index(f'{i}+1line')


# ── Application principale ────────────────────────────────────────────

class AlgoLaboApp:
    def __init__(self, root):
        self.root = root
        root.title('AlgoLabo')
        root.geometry('1180x720')
        root.configure(bg=BG)

        self._current_file = None

        self._build_style()
        self._build_header()
        self._build_snippet_bar()
        self._build_main()
        self._build_reference()

        self.code_text.insert('1.0', DEFAULT_CODE)
        self.code_text.edit_modified(False)
        self.highlight()
        self.linenumbers.redraw()

        self.root.bind('<Control-s>', lambda e: self.on_save())
        self.root.bind('<Control-o>', lambda e: self.on_open())
        self.root.bind('<Control-n>', lambda e: self.on_clear())
        self.root.bind('<Control-slash>', lambda e: self._toggle_comment())
        self.root.bind('<Control-Return>', lambda e: self.on_run())
        self.root.bind('<Control-t>', lambda e: self.on_run())
        self.root.bind('<F5>', lambda e: self.on_run())
        # Raccourcis snippets (Ctrl+Maj+Lettre)
        # Sur Windows, Shift change le keysym en majuscule : on utilise <Control-MAJUSCULE>
        self.root.bind('<Control-V>', lambda e: self._dlg_variable())
        self.root.bind('<Control-S>', lambda e: self._insert_snippet(
            '  SI (condition) ALORS\n    DEBUT_SI\n    \n    FIN_SI\n'))
        self.root.bind('<Control-O>', lambda e: self._insert_snippet(
            '  SINON\n    DEBUT_SINON\n    \n    FIN_SINON\n'))
        self.root.bind('<Control-P>', lambda e: self._insert_snippet(
            '  POUR i ALLANT_DE 1 A n\n    DEBUT_POUR\n    \n    FIN_POUR\n'))
        self.root.bind('<Control-W>', lambda e: self._insert_snippet(
            '  TANT_QUE (condition) FAIRE\n    DEBUT_TANT_QUE\n    \n    FIN_TANT_QUE\n'))
        self.root.bind('<Control-E>', lambda e: self._insert_snippet('  ECRIRE \n'))
        self.root.bind('<Control-L>', lambda e: self._dlg_lire())
        self.root.bind('<Control-A>', lambda e: self._dlg_affectation())

    # ---------- construction de l'interface ----------
    def _build_style(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('TNotebook', background=PANEL, borderwidth=0)
        style.configure('TNotebook.Tab', padding=(14, 6), background=PANEL, foreground=MUTED)
        style.map('TNotebook.Tab', background=[('selected', ACCENT_SOFT)], foreground=[('selected', ACCENT_DARK)])
        style.configure('Treeview', font=('Consolas', 10), rowheight=22)
        style.configure('Treeview.Heading', font=('Segoe UI', 9, 'bold'))
        style.configure('Accent.TButton', background=ACCENT, foreground='white')
        style.map('Accent.TButton', background=[('active', ACCENT_DARK)])

    def _build_header(self):
        header = tk.Frame(self.root, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        header.pack(fill='x')

        title_frame = tk.Frame(header, bg=PANEL)
        title_frame.pack(side='top', anchor='w', padx=16, pady=(10, 4))
        # Logo canvas : [cercle noir] ---> [carre bleu] ---> [cercle noir]
        #               AlgoLabo  (texte bold en dessous)
        # TODO: remplacer par les assets AlgoLabo (resources/LogoEME.png non utilise ici)
        logo_canvas = tk.Canvas(title_frame, width=160, height=54, bg=PANEL,
                                highlightthickness=0)
        logo_canvas.pack(anchor='w')
        # Coordonnees horizontales : centrees sur 80px
        # cercle gauche cx=26, carre cx=80, cercle droit cx=134
        # fleche 1 : de 36 a 68 ; fleche 2 : de 92 a 124
        R = 10  # rayon cercles
        SZ = 10  # demi-cote du carre (20x20)
        CY = 20  # centre vertical des formes
        # Cercle gauche
        logo_canvas.create_oval(16, CY - R, 36, CY + R,
                                fill=TEXT, outline='')
        # Fleche 1
        logo_canvas.create_line(37, CY, 68, CY,
                                fill='#888888', width=2, arrow=tk.LAST)
        # Carre bleu
        logo_canvas.create_rectangle(70, CY - SZ, 90, CY + SZ,
                                     fill=ACCENT, outline='')
        # Fleche 2
        logo_canvas.create_line(91, CY, 122, CY,
                                fill='#888888', width=2, arrow=tk.LAST)
        # Cercle droit
        logo_canvas.create_oval(124, CY - R, 144, CY + R,
                                fill=TEXT, outline='')
        # Texte AlgoLabo
        logo_canvas.create_text(80, 43, text='AlgoLabo',
                                font=('Segoe UI', 11, 'bold'), fill=TEXT,
                                anchor='center')
        tk.Label(title_frame, text='Environnement simplifie pour apprendre les bases de la logique algorithmique',
                 font=('Segoe UI', 9), bg=PANEL, fg=MUTED).pack(anchor='w')

        toolbar = tk.Frame(header, bg=PANEL)
        toolbar.pack(side='top', fill='x', padx=16, pady=(0, 10))

        # Boutons d'action : packes en premier avec side='right' pour garantir
        # qu'ils restent toujours visibles, meme si la fenetre est redimensionnee.
        btn_run = tk.Button(toolbar, text='▶ Executer', command=self.on_run, relief='flat',
                            bg=ACCENT, fg='white', activebackground=ACCENT_DARK, activeforeground='white',
                            font=('Segoe UI', 9, 'bold'), padx=14, pady=6)
        btn_run.pack(side='right')
        Tooltip(btn_run, 'Executer le programme\nLes resultats apparaissent dans la console.\nRaccourcis : Ctrl+Entree  /  F5  /  Ctrl+T')

        _fb, _fh = '#F0F4F8', '#DDE4EE'

        def _file_btn(parent, label, cmd):
            b = tk.Button(parent, text=label, command=cmd, relief='flat',
                          bg=_fb, fg=TEXT, activebackground=_fh, activeforeground=TEXT,
                          font=('Segoe UI', 9), padx=12, pady=5, cursor='hand2',
                          highlightbackground=BORDER, highlightthickness=1)
            b.bind('<Enter>', lambda e: b.config(bg=_fh))
            b.bind('<Leave>', lambda e: b.config(bg=_fb))
            return b

        btn_clear = _file_btn(toolbar, '✖  Effacer', self.on_clear)
        btn_clear.pack(side='right', padx=8)
        Tooltip(btn_clear, 'Vider l\'editeur et revenir au squelette minimal\n'
                            'VARIABLES / DEBUT_ALGORITHME / FIN_ALGORITHME\n'
                            'Raccourci : Ctrl+N')

        tk.Frame(toolbar, width=1, bg=BORDER).pack(side='right', fill='y', padx=6, pady=4)

        btn_save = _file_btn(toolbar, '\U0001F4BE  Enregistrer', self.on_save)
        btn_save.pack(side='right')
        Tooltip(btn_save, 'Enregistrer le programme dans un fichier .algo\n'
                          'Raccourci : Ctrl+S\nSauvegarde directe si un fichier est deja ouvert.')

        btn_open = _file_btn(toolbar, '\U0001F4C2  Ouvrir', self.on_open)
        btn_open.pack(side='right', padx=8)
        Tooltip(btn_open, 'Ouvrir un fichier .algo existant\nRaccourci : Ctrl+O')

        self.trace_var = tk.BooleanVar(value=False)
        cb_trace = tk.Checkbutton(toolbar, text='Activer la trace des variables',
                                   variable=self.trace_var,
                                   bg=PANEL, fg=MUTED, activebackground=PANEL,
                                   font=('Segoe UI', 9))
        cb_trace.pack(side='left')
        Tooltip(cb_trace, 'Enregistrer l\'etat de toutes les variables apres chaque instruction\n'
                          'Visible dans l\'onglet "Trace des variables" apres execution.\n'
                          'Ralentit les programmes avec beaucoup d\'etapes.')

        self.example_var = tk.StringVar(value='Charger un exemple...')
        example_box = ttk.Combobox(toolbar, textvariable=self.example_var, state='readonly',
                                    values=['Charger un exemple...'] + [label for label, _ in EXAMPLES], width=38)
        example_box.pack(side='left', padx=16)
        example_box.bind('<<ComboboxSelected>>', self.on_example_selected)
        Tooltip(example_box, 'Charger un programme exemple dans l\'editeur\n'
                             '9 exemples couvrant toutes les notions : SI, POUR, TANT_QUE,\n'
                             'LISTE, chaines, ALEA, DIV...')

        btn_about = tk.Button(toolbar, text='?', command=self._show_about, relief='flat',
                              bg=PANEL, fg=MUTED, font=('Segoe UI', 10, 'bold'),
                              padx=8, pady=4, cursor='hand2',
                              activebackground=ACCENT_SOFT, activeforeground=ACCENT_DARK)
        btn_about.pack(side='left', padx=(6, 0))
        Tooltip(btn_about, 'A propos de AlgoLabo')

    def _show_about(self):
        dlg = tk.Toplevel(self.root)
        dlg.title('A propos')
        dlg.resizable(False, False)
        dlg.configure(bg=PANEL)
        dlg.grab_set()
        dlg.transient(self.root)

        # Logo canvas dans la boite "A propos"
        # TODO: remplacer par les assets AlgoLabo (resources/LogoEME.png non utilise ici)
        about_canvas = tk.Canvas(dlg, width=160, height=54, bg=PANEL, highlightthickness=0)
        about_canvas.pack(pady=(24, 8))
        R2, SZ2, CY2 = 10, 10, 20
        about_canvas.create_oval(16, CY2 - R2, 36, CY2 + R2, fill=TEXT, outline='')
        about_canvas.create_line(37, CY2, 68, CY2, fill='#888888', width=2, arrow=tk.LAST)
        about_canvas.create_rectangle(70, CY2 - SZ2, 90, CY2 + SZ2, fill=ACCENT, outline='')
        about_canvas.create_line(91, CY2, 122, CY2, fill='#888888', width=2, arrow=tk.LAST)
        about_canvas.create_oval(124, CY2 - R2, 144, CY2 + R2, fill=TEXT, outline='')
        about_canvas.create_text(80, 43, text='AlgoLabo',
                                 font=('Segoe UI', 11, 'bold'), fill=TEXT, anchor='center')

        tk.Label(dlg, text='AlgoLabo', font=('Segoe UI', 15, 'bold'),
                 bg=PANEL, fg=TEXT).pack()
        tk.Label(dlg, text='Environnement simplifie pour apprendre\nles bases de la logique algorithmique',
                 font=('Segoe UI', 9), bg=PANEL, fg=MUTED, justify='center').pack(pady=(2, 16))

        sep = tk.Frame(dlg, bg=BORDER, height=1)
        sep.pack(fill='x', padx=24)

        info_frame = tk.Frame(dlg, bg=PANEL)
        info_frame.pack(pady=16, padx=32)

        rows = [
            ('Developpe par',  'Tristan GERIN - 2026'),
            ('Etablissement',  'Lycee EME, Marseille'),
            ('Licence',        'Logiciel libre - MIT'),
            ('Langage',        'Python 3 / Tkinter'),
        ]
        for label, value in rows:
            row = tk.Frame(info_frame, bg=PANEL)
            row.pack(anchor='w', pady=2)
            tk.Label(row, text=label + ' : ', font=('Segoe UI', 9, 'bold'),
                     bg=PANEL, fg=MUTED, width=16, anchor='e').pack(side='left')
            tk.Label(row, text=value, font=('Segoe UI', 9),
                     bg=PANEL, fg=TEXT, anchor='w').pack(side='left')

        tk.Frame(dlg, bg=BORDER, height=1).pack(fill='x', padx=24)

        tk.Button(dlg, text='Fermer', command=dlg.destroy, relief='flat',
                  bg=ACCENT, fg='white', activebackground=ACCENT_DARK, activeforeground='white',
                  font=('Segoe UI', 9, 'bold'), padx=20, pady=5,
                  cursor='hand2').pack(pady=16)

        dlg.bind('<Escape>', lambda e: dlg.destroy())
        dlg.bind('<Return>', lambda e: dlg.destroy())
        dlg.update_idletasks()
        w, h = dlg.winfo_width(), dlg.winfo_height()
        x = self.root.winfo_x() + (self.root.winfo_width() - w) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - h) // 2
        dlg.geometry(f'+{x}+{y}')

    def _build_main(self):
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill='both', expand=True, padx=16, pady=12)

        paned = tk.PanedWindow(main, orient='horizontal', bg=BG, sashwidth=8, bd=0)
        paned.pack(fill='both', expand=True)

        # ---- Panneau editeur ----
        editor_pane = tk.Frame(paned, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        paned.add(editor_pane, stretch='always', width=650)

        editor_head = tk.Frame(editor_pane, bg=PANEL)
        editor_head.pack(fill='x')
        tk.Label(editor_head, text='Programme', font=('Segoe UI', 9, 'bold'),
                 bg=PANEL, fg=MUTED).pack(side='left', padx=12, pady=8)
        tk.Frame(editor_head, bg=BORDER, height=1).pack(fill='x', side='bottom')

        editor_body = tk.Frame(editor_pane, bg=EDITOR_BG)
        editor_body.pack(fill='both', expand=True)

        self.linenumbers = LineNumbers(editor_body, None, width=56, bg=GUTTER_BG, highlightthickness=0)
        self.linenumbers.pack(side='left', fill='y')

        text_scroll = tk.Scrollbar(editor_body)
        text_scroll.pack(side='right', fill='y')
        self.editor_scroll = text_scroll

        self.code_text = tk.Text(editor_body, wrap='none', undo=True, bg=EDITOR_BG, fg=EDITOR_TEXT,
                                  insertbackground='white', selectbackground='#33415C',
                                  font=('Consolas', 11), relief='flat', padx=10, pady=10,
                                  yscrollcommand=self._on_text_yscroll, borderwidth=0)
        self.code_text.pack(side='left', fill='both', expand=True)
        text_scroll.config(command=self._on_scrollbar)
        self.linenumbers.text_widget = self.code_text

        for tagname, color, extra in [
            ('kw_block', COL_BLOCK, {'font': ('Consolas', 11, 'bold')}),
            ('kw_ctrl', COL_CTRL, {'font': ('Consolas', 11, 'bold italic')}),
            ('kw_type', COL_TYPE, {}),
            ('kw_bind', COL_BIND, {'font': ('Consolas', 11, 'bold')}),
            ('kw_str', COL_STR, {}),
            ('kw_num', COL_NUM, {}),
            ('kw_com', COL_COM, {'font': ('Consolas', 11, 'italic')}),
            ('kw_op', COL_OP, {'font': ('Consolas', 11, 'bold')}),
        ]:
            self.code_text.tag_configure(tagname, foreground=color, **extra)
        self.code_text.tag_configure('err_line', background='#4A1520')
        self.code_text.tag_raise('sel')

        self.code_text.bind('<KeyRelease>', self._on_text_change)
        self.code_text.bind('<Tab>', self._on_tab)
        self.code_text.bind('<MouseWheel>', lambda e: self.root.after(10, self.linenumbers.redraw))
        self.code_text.bind('<Button-4>', lambda e: self.root.after(10, self.linenumbers.redraw))
        self.code_text.bind('<Button-5>', lambda e: self.root.after(10, self.linenumbers.redraw))
        self.code_text.bind('<Configure>', lambda e: self.linenumbers.redraw())
        # Raccourcis snippets aussi sur l'editeur (priorite sur les bindings racine)
        self.code_text.bind('<Control-V>', lambda e: self._dlg_variable() or 'break')
        self.code_text.bind('<Control-S>', lambda e: self._insert_snippet(
            '  SI (condition) ALORS\n    DEBUT_SI\n    \n    FIN_SI\n') or 'break')
        self.code_text.bind('<Control-O>', lambda e: self._insert_snippet(
            '  SINON\n    DEBUT_SINON\n    \n    FIN_SINON\n') or 'break')
        self.code_text.bind('<Control-P>', lambda e: self._insert_snippet(
            '  POUR i ALLANT_DE 1 A n\n    DEBUT_POUR\n    \n    FIN_POUR\n') or 'break')
        self.code_text.bind('<Control-W>', lambda e: self._insert_snippet(
            '  TANT_QUE (condition) FAIRE\n    DEBUT_TANT_QUE\n    \n    FIN_TANT_QUE\n') or 'break')
        self.code_text.bind('<Control-E>', lambda e: self._insert_snippet('  ECRIRE \n') or 'break')
        self.code_text.bind('<Control-L>', lambda e: self._dlg_lire() or 'break')
        self.code_text.bind('<Control-A>', lambda e: self._dlg_affectation() or 'break')

        # ---- Panneau resultats ----
        output_pane = tk.Frame(paned, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        paned.add(output_pane, stretch='always', width=480)

        out_head = tk.Frame(output_pane, bg=PANEL)
        out_head.pack(fill='x')
        self.status_var = tk.StringVar(value='')
        self.status_label = tk.Label(out_head, textvariable=self.status_var, font=('Segoe UI', 9, 'bold'),
                                      bg=PANEL, fg=OK_COLOR)
        self.status_label.pack(side='right', padx=12, pady=8)
        tk.Frame(out_head, bg=BORDER, height=1).pack(fill='x', side='bottom')

        notebook = ttk.Notebook(output_pane)
        notebook.pack(fill='both', expand=True, padx=8, pady=8)

        console_frame = tk.Frame(notebook, bg=PANEL)
        notebook.add(console_frame, text='Console')
        self.console_text = tk.Text(console_frame, wrap='word', bg=PANEL, fg=TEXT,
                                     font=('Segoe UI', 10), relief='flat', state='disabled', padx=8, pady=8)
        self.console_text.pack(fill='both', expand=True)
        self.console_text.tag_configure('err', foreground=ERR_COLOR, background=ERR_BG)
        self.console_text.tag_configure('muted', foreground=MUTED, font=('Segoe UI', 10, 'italic'))
        self.console_text.tag_configure('input_echo', foreground=OK_COLOR, font=('Consolas', 10, 'italic'))

        trace_frame = tk.Frame(notebook, bg=PANEL)
        notebook.add(trace_frame, text='Trace des variables')
        self.trace_tree = ttk.Treeview(trace_frame, columns=('ligne', 'action', 'etat'), show='headings')
        self.trace_tree.heading('ligne', text='Ligne')
        self.trace_tree.heading('action', text='Action')
        self.trace_tree.heading('etat', text='Etat des variables')
        self.trace_tree.column('ligne', width=50, anchor='center')
        self.trace_tree.column('action', width=200)
        self.trace_tree.column('etat', width=320)
        trace_scroll = ttk.Scrollbar(trace_frame, orient='vertical', command=self.trace_tree.yview)
        self.trace_tree.configure(yscrollcommand=trace_scroll.set)
        self.trace_tree.pack(side='left', fill='both', expand=True)
        trace_scroll.pack(side='right', fill='y')

        # ---- Onglet Algorigramme ----
        fc_outer = tk.Frame(notebook, bg=PANEL)
        notebook.add(fc_outer, text='Algorigramme')

        fc_toolbar = tk.Frame(fc_outer, bg=PANEL)
        fc_toolbar.pack(fill='x', padx=8, pady=(6, 0))
        tk.Button(fc_toolbar, text='Generer l\'algorigramme', command=self._on_gen_fc,
                  relief='flat', bg=ACCENT_SOFT, fg=ACCENT_DARK, cursor='hand2',
                  font=('Segoe UI', 9), padx=10, pady=4,
                  activebackground=ACCENT, activeforeground='white').pack(side='left')
        tk.Button(fc_toolbar, text='Enregistrer...', command=self._save_flowchart,
                  relief='flat', bg='#EEF7EE', fg='#1E7040', cursor='hand2',
                  font=('Segoe UI', 9), padx=10, pady=4,
                  activebackground='#5FD68A', activeforeground='white').pack(side='left', padx=(6, 0))
        self._fc_msg = tk.StringVar(
            value='Executer le programme ou cliquer "Generer" pour voir l\'algorigramme.')
        tk.Label(fc_toolbar, textvariable=self._fc_msg, bg=PANEL, fg=MUTED,
                 font=('Segoe UI', 9)).pack(side='left', padx=10)

        fc_body = tk.Frame(fc_outer, bg=PANEL)
        fc_body.pack(fill='both', expand=True)
        fc_vbar = ttk.Scrollbar(fc_body, orient='vertical')
        fc_hbar = ttk.Scrollbar(fc_body, orient='horizontal')
        self.fc_canvas = tk.Canvas(fc_body, bg='#FFFFFF', highlightthickness=0,
                                    yscrollcommand=fc_vbar.set,
                                    xscrollcommand=fc_hbar.set,
                                    scrollregion=(0, 0, 800, 600))
        fc_vbar.config(command=self.fc_canvas.yview)
        fc_hbar.config(command=self.fc_canvas.xview)
        fc_vbar.pack(side='right', fill='y')
        fc_hbar.pack(side='bottom', fill='x')
        self.fc_canvas.pack(fill='both', expand=True)
        self.fc_canvas.bind('<MouseWheel>',
                             lambda e: self.fc_canvas.yview_scroll(-1 if e.delta > 0 else 1, 'units'))
        self.fc_renderer = FlowchartRenderer(self.fc_canvas)

        self._render_console_message('Aucun resultat pour le moment. Clique sur Executer.')

    def _build_reference(self):
        outer = tk.Frame(self.root, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        outer.pack(fill='x', padx=16, pady=(0, 14))

        self.ref_open = tk.BooleanVar(value=False)
        head = tk.Frame(outer, bg=PANEL, cursor='hand2')
        head.pack(fill='x')
        self.ref_arrow_var = tk.StringVar(value='▸')
        tk.Label(head, textvariable=self.ref_arrow_var, bg=PANEL, fg=MUTED,
                 font=('Segoe UI', 10)).pack(side='left', padx=(12, 4), pady=8)
        tk.Label(head, text='Instructions autorisees dans cet outil', bg=PANEL, fg=TEXT,
                 font=('Segoe UI', 10, 'bold')).pack(side='left', pady=8)
        head.bind('<Button-1>', self._toggle_reference)
        for child in head.winfo_children():
            child.bind('<Button-1>', self._toggle_reference)

        self.ref_body = tk.Frame(outer, bg=PANEL)
        ref_text = tk.Text(self.ref_body, wrap='word', bg=PANEL, fg=TEXT, font=('Consolas', 10),
                            relief='flat', height=9, padx=12, pady=6)
        for prefix, tag, words in REFERENCE_TEXT:
            if prefix:
                ref_text.insert('end', prefix, 'label')
            ref_text.insert('end', words, tag)
        ref_text.tag_configure('label', foreground=MUTED, font=('Segoe UI', 9, 'bold'))
        for tagname, color in [('kw_block', COL_BLOCK), ('kw_ctrl', COL_CTRL), ('kw_type', COL_TYPE),
                                ('kw_bind', COL_BIND), ('kw_op', COL_OP)]:
            ref_text.tag_configure(tagname, foreground=ACCENT_DARK, background=ACCENT_SOFT)
        ref_text.configure(state='disabled')
        ref_text.pack(fill='x')

        note = tk.Label(self.ref_body, text=REFERENCE_NOTE, bg=PANEL, fg=MUTED, font=('Segoe UI', 9),
                         justify='left', anchor='w', padx=12)
        note.pack(fill='x', pady=(0, 10))

    def _toggle_reference(self, _event=None):
        if self.ref_open.get():
            self.ref_body.pack_forget()
            self.ref_arrow_var.set('▸')
            self.ref_open.set(False)
        else:
            self.ref_body.pack(fill='x')
            self.ref_arrow_var.set('▾')
            self.ref_open.set(True)

    # ---------- algorigramme ----------
    def _on_gen_fc(self):
        source = self.code_text.get('1.0', 'end-1c')
        try:
            prog = parse_program(source)
            self.fc_renderer.render(prog)
            self._fc_msg.set('Algorigramme genere.')
        except AlgoError as e:
            self._fc_msg.set('Erreur (ligne %s) : %s' % (e.line, e.message[:55]))

    def _save_flowchart(self):
        if not self.fc_canvas.find_all():
            self._fc_msg.set("Rien a enregistrer : generez d'abord l'algorigramme.")
            return
        try:
            from PIL import Image as _PILImg  # noqa
            _pil = True
        except ImportError:
            _pil = False
        if _pil:
            filetypes = [('Image PNG', '*.png'), ('PostScript vectoriel', '*.eps')]
            defext = '.png'
        else:
            filetypes = [('PostScript vectoriel', '*.eps')]
            defext = '.eps'
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Enregistrer l'algorigramme",
            defaultextension=defext,
            filetypes=filetypes + [('Tous les fichiers', '*.*')])
        if not path:
            return
        try:
            if _pil and path.lower().endswith('.png'):
                source = self.code_text.get('1.0', 'end-1c')
                prog   = parse_program(source)
                img    = _PilFlowRenderer().to_image(prog)
                img.save(path)
            else:
                if not path.lower().endswith('.eps'):
                    path += '.eps'
                ps = self.fc_canvas.postscript(colormode='color')
                with open(path, 'w', encoding='latin-1') as f:
                    f.write(ps)
            self._fc_msg.set('Enregistre : ' + os.path.basename(path))
        except Exception as ex:
            self._fc_msg.set("Erreur lors de l'enregistrement : " + str(ex))

    # ---------- barre de snippets ----------
    def _build_snippet_bar(self):
        outer = tk.Frame(self.root, bg=PANEL,
                         highlightbackground=BORDER, highlightthickness=1)
        outer.pack(fill='x', padx=16, pady=(0, 6))

        bar = tk.Frame(outer, bg=PANEL)
        bar.pack(fill='x')

        tk.Label(bar, text='Inserer :', bg=PANEL, fg=MUTED,
                 font=('Segoe UI', 9, 'bold')).pack(side='left', padx=(12, 8), pady=6)

        S_VAR  = dict(bg='#E7EDF9', fg='#325590',
                      activebackground=ACCENT, activeforeground='white')
        S_CTRL = dict(bg='#FFECF3', fg='#B0204A',
                      activebackground='#FF7FAE', activeforeground='white')
        S_IO   = dict(bg='#F3EBFF', fg='#6535A0',
                      activebackground='#B98BFF', activeforeground='white')
        S_COM  = dict(bg='#EDEEF0', fg='#5A6477',
                      activebackground='#BFC4CF', activeforeground='#1F2733')
        S_BIND = dict(bg='#FFF8ED', fg='#924A00',
                      activebackground='#FDE8C0', activeforeground='#5C2D00')

        snippets = [
            ('+ Variable',
             self._dlg_variable, S_VAR,
             'Declarer une nouvelle variable dans le bloc VARIABLES\n'
             'Choisir son nom et son type : NOMBRE, TEXTE, BOOLEEN ou LISTE.\n'
             'Raccourci : Ctrl+Maj+V'),
            ('SI...ALORS',
             lambda: self._insert_snippet(
                 '  SI (condition) ALORS\n    DEBUT_SI\n    \n    FIN_SI\n'), S_CTRL,
             'Structure conditionnelle : execute le bloc si la condition est VRAIE.\n'
             'Remplacer "condition" par ex : x > 0  ou  note >= 10\n'
             'Ajouter SINON juste apres FIN_SI pour la branche alternative.\n'
             'Raccourci : Ctrl+Maj+S'),
            ('SINON',
             lambda: self._insert_snippet(
                 '  SINON\n    DEBUT_SINON\n    \n    FIN_SINON\n'), S_CTRL,
             'Branche alternative du SI : executee si la condition est FAUSSE.\n'
             'A placer directement apres FIN_SI.\n'
             'Raccourci : Ctrl+Maj+O'),
            ('POUR...ALLANT_DE',
             lambda: self._insert_snippet(
                 '  POUR i ALLANT_DE 1 A n\n    DEBUT_POUR\n    \n    FIN_POUR\n'), S_CTRL,
             'Boucle bornee : repete le bloc pour i allant de 1 a n (inclus).\n'
             'Remplacer i, 1 et n par les valeurs souhaitees.\n'
             'Pratique pour parcourir une liste : ALLANT_DE 0 A LONGUEUR(L) - 1\n'
             'Raccourci : Ctrl+Maj+P'),
            ('TANT_QUE...FAIRE',
             lambda: self._insert_snippet(
                 '  TANT_QUE (condition) FAIRE\n    DEBUT_TANT_QUE\n    \n    FIN_TANT_QUE\n'), S_CTRL,
             'Boucle conditionnelle : repete le bloc TANT QUE la condition est VRAIE.\n'
             'Attention : la condition doit finir par devenir FAUSSE, sinon boucle infinie.\n'
             'Protection automatique a 200 000 etapes.\n'
             'Raccourci : Ctrl+Maj+W'),
            ('ECRIRE',
             lambda: self._insert_snippet('  ECRIRE \n'), S_IO,
             'Afficher une valeur ou un texte dans la console.\n'
             'Exemples : ECRIRE x    ECRIRE "Bonjour"    ECRIRE "Score : " + score\n'
             'AFFICHER est accepte comme synonyme.\n'
             'Raccourci : Ctrl+Maj+E'),
            ('LIRE',
             self._dlg_lire, S_IO,
             'Demander une valeur a l\'utilisateur et la stocker dans une variable.\n'
             'Ouvre un dialogue pour choisir parmi les variables declarees.\n'
             'Exemple : LIRE age   (stocke la saisie dans la variable age)\n'
             'Raccourci : Ctrl+Maj+L'),
            ('← Affecter',
             self._dlg_affectation, S_BIND,
             'Affecter une valeur a une variable (PREND_LA_VALEUR).\n'
             'Choisir la variable dans la liste, puis saisir la valeur ou l\'expression.\n'
             'Le dialogue s\'adapte au type declare (NOMBRE, TEXTE, BOOLEEN, LISTE).\n'
             'Exemples :\n'
             '  x PREND_LA_VALEUR 0\n'
             '  somme PREND_LA_VALEUR somme + 1\n'
             '  message PREND_LA_VALEUR "Bonjour"\n'
             'Raccourci : Ctrl+Maj+A'),
            ('// ...',
             self._toggle_comment, S_COM,
             'Commenter ou decommenter la ligne courante.\n'
             'Un commentaire est ignore a l\'execution : il sert a expliquer le code.\n'
             'On peut aussi ecrire le commentaire apres une instruction :\n'
             '  x <- x + 1  // incrementation\n'
             'Raccourci : Ctrl+/'),
        ]

        for label, cmd, style, tip in snippets:
            btn = tk.Button(bar, text=label, command=cmd, relief='flat', cursor='hand2',
                            font=('Segoe UI', 9), padx=10, pady=4, **style)
            btn.pack(side='left', padx=3, pady=6)
            Tooltip(btn, tip)

        self._op_open = tk.BooleanVar(value=False)
        self._op_lbl  = tk.StringVar(value='▸ Operateurs...')
        btn_op = tk.Button(bar, textvariable=self._op_lbl, command=self._toggle_op_panel,
                           relief='flat', bg=PANEL, fg=MUTED, cursor='hand2',
                           activebackground=ACCENT_SOFT, activeforeground=ACCENT_DARK,
                           font=('Segoe UI', 9), padx=10, pady=4)
        btn_op.pack(side='left', padx=(14, 3), pady=6)
        Tooltip(btn_op, 'Afficher/masquer le panneau des operateurs, comparaisons,\n'
                        'operateurs logiques et fonctions integrees (ALEA, LONGUEUR...).\n'
                        'Cliquer un symbole l\'insere a la position du curseur.')

        self._op_panel = tk.Frame(outer, bg='#F8F9FB',
                                   highlightbackground=BORDER, highlightthickness=1)

        S_OP  = dict(bg='#EDEDFF', fg='#3030A0',
                     activebackground='#C3C9FF', activeforeground='#1F2733')
        S_LOG = dict(bg='#FFECF3', fg='#B0204A',
                     activebackground='#FF7FAE', activeforeground='white')
        S_VAL = dict(bg='#F3EBFF', fg='#6535A0',
                     activebackground='#B98BFF', activeforeground='white')
        S_FN  = dict(bg='#E8F5EE', fg='#1E7040',
                     activebackground='#5FD68A', activeforeground='white')

        def op_btn(parent, label, ins, style, tip=''):
            btn = tk.Button(parent, text=label, relief='flat', cursor='hand2',
                            font=('Consolas', 9), padx=7, pady=3,
                            command=lambda t=ins: self._insert_inline(t),
                            **style)
            btn.pack(side='left', padx=2)
            if tip:
                Tooltip(btn, tip)

        def sep(parent):
            tk.Frame(parent, width=1, bg=BORDER).pack(side='left', fill='y', padx=8, pady=4)

        row1 = tk.Frame(self._op_panel, bg='#F8F9FB')
        row1.pack(fill='x', padx=10, pady=(6, 2))
        row2 = tk.Frame(self._op_panel, bg='#F8F9FB')
        row2.pack(fill='x', padx=10, pady=(2, 6))

        tk.Label(row1, text='Arith. :', bg='#F8F9FB', fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(side='left', padx=(0, 4))
        _arith_tips = {
            '+': 'Addition (nombres) ou concatenation (chaines)\nEx : x + 1   ou   "Bonjour " + nom',
            '-': 'Soustraction\nEx : total - remise',
            '*': 'Multiplication\nEx : prix * quantite',
            '/': 'Division reelle (resultat decimal)\nEx : 7 / 2 = 3.5',
        }
        for sym in ['+', '-', '*', '/']:
            op_btn(row1, sym, ' ' + sym + ' ', S_OP, _arith_tips[sym])
        op_btn(row1, '(', '(', S_OP, 'Parenthese ouvrante — groupe une sous-expression\nEx : (a + b) * c')
        op_btn(row1, ')', ')', S_OP, 'Parenthese fermante — ferme le groupe\nEx : (a + b) * c')
        sep(row1)
        tk.Label(row1, text='Compar. :', bg='#F8F9FB', fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(side='left', padx=(0, 4))
        _cmp_tips = {
            '<':  'Strictement inferieur\nEx : age < 18',
            '>':  'Strictement superieur\nEx : score > 100',
            '<=': 'Inferieur ou egal\nEx : note <= 10',
            '>=': 'Superieur ou egal\nEx : temperature >= 37',
            '==': 'Egalite (test, pas affectation)\nEx : reponse == "oui"',
            '!=': 'Difference — vrai si les deux valeurs sont differentes\nEx : code != 0',
        }
        for sym in ['<', '>', '<=', '>=', '==', '!=']:
            op_btn(row1, sym, ' ' + sym + ' ', S_OP, _cmp_tips[sym])

        tk.Label(row2, text='Logique :', bg='#F8F9FB', fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(side='left', padx=(0, 4))
        op_btn(row2, 'ET',  ' ET ',  S_LOG,
               'ET logique — vrai si les deux conditions sont vraies\nEx : age >= 18 ET nationalite == "FR"')
        op_btn(row2, 'OU',  ' OU ',  S_LOG,
               'OU logique — vrai si au moins une condition est vraie\nEx : jour == "sam" OU jour == "dim"')
        op_btn(row2, 'NON', 'NON ',  S_LOG,
               'Negation logique — inverse la valeur booleenne\nEx : NON estConnecte')
        sep(row2)
        tk.Label(row2, text='Div./Mod. :', bg='#F8F9FB', fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(side='left', padx=(0, 4))
        op_btn(row2, 'MOD', ' MOD ', S_OP,
               'Reste de la division entiere\nEx : 7 MOD 3 = 1\nAstuce : x MOD 2 == 0 teste la parite')
        op_btn(row2, 'DIV', ' DIV ', S_OP,
               'Quotient entier (division sans decimales)\nEx : 7 DIV 3 = 2')
        sep(row2)
        tk.Label(row2, text='Valeurs :', bg='#F8F9FB', fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(side='left', padx=(0, 4))
        op_btn(row2, 'VRAI', 'VRAI', S_VAL,
               'Constante booleenne vraie\nEx : continuer <- VRAI')
        op_btn(row2, 'FAUX', 'FAUX', S_VAL,
               'Constante booleenne fausse\nEx : trouve <- FAUX')
        sep(row2)
        tk.Label(row2, text='Fonctions :', bg='#F8F9FB', fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(side='left', padx=(0, 4))
        op_btn(row2, 'ALEA(a, b)',    'ALEA(a, b)',    S_FN,
               'Nombre entier aleatoire entre a et b inclus\nEx : ALEA(1, 6) simule un de a 6 faces')
        op_btn(row2, 'ALEA()',        'ALEA()',        S_FN,
               'Nombre reel aleatoire entre 0.0 et 1.0 (exclu)\nEx : ALEA() < 0.5 est vrai une fois sur deux')
        op_btn(row2, 'LONGUEUR(nom)', 'LONGUEUR(nom)', S_FN,
               'Nombre de caracteres d\'une chaine\nEx : LONGUEUR("Bonjour") = 7\nRemplacer nom par la variable chaine')

        # ---- Bouton Fonctions ----
        self._fn_open = tk.BooleanVar(value=False)
        self._fn_lbl  = tk.StringVar(value='▸ Fonctions...')
        btn_fn = tk.Button(bar, textvariable=self._fn_lbl, command=self._toggle_fn_panel,
                           relief='flat', bg=PANEL, fg=MUTED, cursor='hand2',
                           activebackground=ACCENT_SOFT, activeforeground=ACCENT_DARK,
                           font=('Segoe UI', 9), padx=10, pady=4)
        btn_fn.pack(side='left', padx=(8, 3), pady=6)
        Tooltip(btn_fn, 'Afficher/masquer le panneau de creation et d\'utilisation de fonctions.\n'
                        'CREER_FONCTION ouvre un dialogue pour declarer une nouvelle fonction.\n'
                        'RETOUR et UTILISER_FONCTION inserent les mots-cles correspondants.')

        S_FN2 = dict(bg='#E8F5EE', fg='#1E7040',
                     activebackground='#5FD68A', activeforeground='white')

        self._fn_panel = tk.Frame(outer, bg='#F0FAF4',
                                   highlightbackground='#B2DEC2', highlightthickness=1)
        fn_row = tk.Frame(self._fn_panel, bg='#F0FAF4')
        fn_row.pack(fill='x', padx=10, pady=6)

        tk.Label(fn_row, text='Fonctions :', bg='#F0FAF4', fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(side='left', padx=(0, 6))

        btn_creer = tk.Button(fn_row, text='CREER_FONCTION', command=self._dlg_creer_fonction,
                              relief='flat', cursor='hand2', font=('Segoe UI', 9),
                              padx=10, pady=3, **S_FN2)
        btn_creer.pack(side='left', padx=2)
        Tooltip(btn_creer, 'Declarer une nouvelle fonction.\n'
                           'Ouvre un dialogue pour saisir le nom et les parametres.\n'
                           'Insere le squelette FONCTION / DEBUT_FONCTION / FIN_FONCTION\n'
                           'avant le bloc VARIABLES.')

        tk.Frame(fn_row, width=1, bg='#B2DEC2').pack(side='left', fill='y', padx=8, pady=2)

        btn_retour = tk.Button(fn_row, text='RETOUR',
                               command=lambda: self._insert_snippet('  RETOUR \n'),
                               relief='flat', cursor='hand2', font=('Segoe UI', 9),
                               padx=10, pady=3, **S_FN2)
        btn_retour.pack(side='left', padx=2)
        Tooltip(btn_retour, 'Inserer RETOUR : renvoie une valeur depuis la fonction.\n'
                            'Ex : RETOUR valeur * valeur\n'
                            'Placer RETOUR a l\'interieur d\'un bloc DEBUT_FONCTION / FIN_FONCTION.')

        btn_utiliser = tk.Button(fn_row, text='UTILISER_FONCTION',
                                 command=self._dlg_utiliser_fonction,
                                 relief='flat', cursor='hand2', font=('Segoe UI', 9),
                                 padx=10, pady=3, **S_FN2)
        btn_utiliser.pack(side='left', padx=2)
        Tooltip(btn_utiliser, 'Appeler une fonction sans valeur de retour.\n'
                              'Ouvre un dialogue listant les fonctions declarees.\n'
                              'Insere directement : afficherTrait()\n'
                              'Pour une fonction avec RETOUR, utiliser dans une affectation :\n'
                              '  res PREND_LA_VALEUR carre(x)')

    def _get_declared_functions(self):
        """Retourne la liste des fonctions declarees : [(nom, [param1, param2, ...]), ...]"""
        result = []
        content = self.code_text.get('1.0', 'end-1c')
        for ln in content.split('\n'):
            m = re.match(r'^\s*FONCTION\s+([A-Za-zÀ-ÿ_][A-Za-zÀ-ÿ0-9_]*)\s*\(([^)]*)\)\s*$',
                         ln, re.IGNORECASE)
            if m:
                name = m.group(1)
                params_str = m.group(2).strip()
                params = [p.strip() for p in params_str.split(',') if p.strip()] if params_str else []
                result.append((name, params))
        return result

    def _dlg_utiliser_fonction(self):
        funcs = self._get_declared_functions()

        if not funcs:
            def build_vide(body, close):
                tk.Label(body, text='Aucune fonction declaree.\nUtilise CREER_FONCTION\npour en ajouter une.',
                         bg=BG, fg=TEXT, font=('Segoe UI', 9), justify='center').pack(padx=20, pady=16)
                btn = tk.Button(body, text='OK', command=close, relief='flat',
                                bg=ACCENT, fg='white', font=('Segoe UI', 9), padx=16, pady=4)
                btn.pack(pady=(0, 14))
                body.after(0, btn.focus_set)
                body.bind('<Return>', lambda e: close())
            self._show_modal('Utiliser une fonction', build_vide)
            return

        def build(body, close):
            func_labels = [
                name + '(' + ', '.join(params) + ')' for name, params in funcs
            ]
            tk.Label(body, text='Fonction :', bg=BG, fg=TEXT,
                     font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w', padx=16, pady=(16, 6))
            fn_combo = ttk.Combobox(body, values=func_labels, state='readonly', width=30,
                                    font=('Consolas', 10))
            fn_combo.current(0)
            fn_combo.grid(row=0, column=1, sticky='w', padx=(0, 16), pady=(16, 6))
            body.after(0, fn_combo.focus_set)

            # Zone dynamique pour les arguments
            args_frame = tk.Frame(body, bg=BG)
            args_frame.grid(row=1, column=0, columnspan=2, sticky='ew', padx=16, pady=(0, 4))
            arg_vars = []

            def rebuild_args(event=None):
                for w in args_frame.winfo_children():
                    w.destroy()
                arg_vars.clear()
                _, params = funcs[fn_combo.current()]
                if not params:
                    tk.Label(args_frame, text='(pas de parametre)', bg=BG, fg=MUTED,
                             font=('Segoe UI', 8, 'italic')).pack(anchor='w', pady=2)
                    return
                for i, p in enumerate(params):
                    row = tk.Frame(args_frame, bg=BG)
                    row.pack(fill='x', pady=2)
                    tk.Label(row, text=p + ' :', bg=BG, fg=TEXT,
                             font=('Consolas', 9), width=14, anchor='e').pack(side='left')
                    v = tk.StringVar()
                    ent = tk.Entry(row, textvariable=v, font=('Consolas', 10), width=20,
                                   relief='flat', highlightthickness=1, highlightbackground=BORDER)
                    ent.pack(side='left', padx=(6, 0))
                    arg_vars.append(v)
                    if i == 0:
                        body.after(0, ent.focus_set)

            fn_combo.bind('<<ComboboxSelected>>', rebuild_args)
            rebuild_args()

            err_label = tk.Label(body, text='', bg=BG, fg=ERR_COLOR, font=('Segoe UI', 8))
            err_label.grid(row=2, column=0, columnspan=2, padx=16, pady=(2, 0))

            def do_insert():
                name, params = funcs[fn_combo.current()]
                args = [v.get().strip() for v in arg_vars]
                for i, (p, a) in enumerate(zip(params, args)):
                    if not a:
                        err_label.configure(text='Argument manquant : ' + p)
                        return
                snippet = '  ' + name + '(' + ', '.join(args) + ')\n'
                self._insert_snippet(snippet)
                close()

            btn_frame = tk.Frame(body, bg=BG)
            btn_frame.grid(row=3, column=0, columnspan=2, pady=(8, 12))
            tk.Button(btn_frame, text='Annuler', command=close, relief='flat',
                      bg=PANEL, fg=TEXT, font=('Segoe UI', 9), padx=10, pady=4).pack(side='left', padx=8)
            tk.Button(btn_frame, text='Inserer', command=do_insert, relief='flat',
                      bg=ACCENT, fg='white', activebackground=ACCENT_DARK, activeforeground='white',
                      font=('Segoe UI', 9, 'bold'), padx=10, pady=4).pack(side='left', padx=8)
            body.bind('<Return>', lambda e: do_insert())

        self._show_modal('Utiliser une fonction', build)

    def _toggle_fn_panel(self):
        if self._fn_open.get():
            self._fn_panel.pack_forget()
            self._fn_lbl.set('▸ Fonctions...')
            self._fn_open.set(False)
        else:
            self._fn_panel.pack(fill='x')
            self._fn_lbl.set('▾ Fonctions...')
            self._fn_open.set(True)

    def _dlg_creer_fonction(self):
        def build(body, close):
            tk.Label(body, text='Nom de la fonction :', bg=BG, fg=TEXT,
                     font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w', padx=16, pady=(16, 6))
            name_var = tk.StringVar()
            name_entry = tk.Entry(body, textvariable=name_var, font=('Consolas', 10), width=22,
                                  relief='flat', highlightthickness=1, highlightbackground=BORDER)
            name_entry.grid(row=0, column=1, sticky='w', padx=(0, 16), pady=(16, 6))
            body.after(0, name_entry.focus_set)

            tk.Label(body, text='Parametres :', bg=BG, fg=TEXT,
                     font=('Segoe UI', 9)).grid(row=1, column=0, sticky='w', padx=16, pady=6)
            params_var = tk.StringVar()
            params_entry = tk.Entry(body, textvariable=params_var, font=('Consolas', 10), width=22,
                                    relief='flat', highlightthickness=1, highlightbackground=BORDER)
            params_entry.grid(row=1, column=1, sticky='w', padx=(0, 16), pady=6)
            tk.Label(body, text='(laisser vide si aucun parametre, sinon : a, b, c)',
                     bg=BG, fg=MUTED, font=('Segoe UI', 8)).grid(row=2, column=0, columnspan=2,
                                                                  padx=16, sticky='w')

            err_label = tk.Label(body, text='', bg=BG, fg=ERR_COLOR, font=('Segoe UI', 8))
            err_label.grid(row=3, column=0, columnspan=2, padx=16)

            def do_insert():
                name = name_var.get().strip()
                if not re.match(r'^[A-Za-z\xc0-\xff_][A-Za-z\xc0-\xff0-9_]*$', name):
                    err_label.configure(text='Nom invalide (lettres, chiffres, _ ; commence par une lettre)')
                    name_entry.focus_set()
                    return
                if name.upper() in RESERVED_WORDS:
                    err_label.configure(text='"' + name + '" est un mot reserve du langage')
                    name_entry.focus_set()
                    return
                raw_params = params_var.get().strip()
                params_list = [p.strip() for p in raw_params.split(',') if p.strip()] if raw_params else []
                for p in params_list:
                    if not re.match(r'^[A-Za-z\xc0-\xff_][A-Za-z\xc0-\xff0-9_]*$', p):
                        err_label.configure(text='Parametre invalide : "' + p + '"')
                        params_entry.focus_set()
                        return
                params_str = ', '.join(params_list)
                snippet = ('FONCTION ' + name + '(' + params_str + ')\n'
                           'DEBUT_FONCTION\n'
                           '  \n'
                           'FIN_FONCTION\n\n')
                # Inserer avant VARIABLES (ou en debut de fichier si absent)
                content = self.code_text.get('1.0', 'end-1c')
                lines_list = content.split('\n')
                insert_at = '1.0'
                for idx, ln in enumerate(lines_list):
                    if ln.strip().upper() == 'VARIABLES':
                        insert_at = f'{idx + 1}.0'
                        break
                self.code_text.edit_separator()
                self.code_text.insert(insert_at, snippet)
                self.highlight()
                self.linenumbers.redraw()
                close()

            btn_frame = tk.Frame(body, bg=BG)
            btn_frame.grid(row=4, column=0, columnspan=2, pady=(8, 12))
            tk.Button(btn_frame, text='Annuler', command=close, relief='flat',
                      bg=PANEL, fg=TEXT, font=('Segoe UI', 9), padx=10, pady=4).pack(side='left', padx=8)
            tk.Button(btn_frame, text='Inserer', command=do_insert, relief='flat',
                      bg=ACCENT, fg='white', activebackground=ACCENT_DARK, activeforeground='white',
                      font=('Segoe UI', 9, 'bold'), padx=10, pady=4).pack(side='left', padx=8)
            name_entry.bind('<Return>', lambda e: do_insert())
            params_entry.bind('<Return>', lambda e: do_insert())

        self._show_modal('Creer une fonction', build)

    def _insert_snippet(self, snippet):
        self.code_text.edit_separator()
        insert_idx = self.code_text.index(tk.INSERT)
        line_num = int(insert_idx.split('.')[0])
        self.code_text.insert(f'{line_num}.0', snippet)
        first_line_len = len(snippet.split('\n')[0])
        self.code_text.mark_set(tk.INSERT, f'{line_num}.{first_line_len}')
        self.code_text.see(tk.INSERT)
        self.highlight()
        self.linenumbers.redraw()
        self.code_text.focus_set()

    def _insert_inline(self, text):
        self.code_text.edit_separator()
        self.code_text.insert(tk.INSERT, text)
        self.highlight()
        self.code_text.focus_set()

    def _toggle_comment(self):
        self.code_text.edit_separator()
        insert_idx = self.code_text.index(tk.INSERT)
        line_num = int(insert_idx.split('.')[0])
        line_text = self.code_text.get(f'{line_num}.0', f'{line_num}.end')
        stripped = line_text.lstrip()
        indent = line_text[:len(line_text) - len(stripped)]
        if stripped.startswith('// '):
            new_text = indent + stripped[3:]
        elif stripped.startswith('//'):
            new_text = indent + stripped[2:]
        else:
            new_text = indent + '// ' + stripped
        self.code_text.delete(f'{line_num}.0', f'{line_num}.end')
        self.code_text.insert(f'{line_num}.0', new_text)
        self.highlight()
        self.linenumbers.redraw()
        self.code_text.focus_set()

    def _toggle_op_panel(self):
        if self._op_open.get():
            self._op_panel.pack_forget()
            self._op_lbl.set('▸ Operateurs...')
            self._op_open.set(False)
        else:
            self._op_panel.pack(fill='x')
            self._op_lbl.set('▾ Operateurs...')
            self._op_open.set(True)

    def _show_modal(self, title, build_fn):
        overlay = tk.Frame(self.root, bg='#1A2035')
        overlay.place(x=0, y=0, relwidth=1, relheight=1)
        overlay.lift()

        card = tk.Frame(overlay, bg=BG,
                        highlightbackground=BORDER, highlightthickness=1)

        def close():
            overlay.destroy()
            self.code_text.focus_set()

        hdr = tk.Frame(card, bg=ACCENT_SOFT)
        hdr.pack(fill='x')
        tk.Label(hdr, text=title, bg=ACCENT_SOFT, fg=ACCENT_DARK,
                 font=('Segoe UI', 10, 'bold'), padx=14, pady=8).pack(side='left')

        body = tk.Frame(card, bg=BG)
        body.pack(fill='both', expand=True)

        build_fn(body, close)

        overlay.update_idletasks()
        cw = card.winfo_reqwidth()
        ch = card.winfo_reqheight()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        card.place(x=max(16, (rw - cw) // 2), y=max(16, (rh - ch) // 2))

        overlay.bind('<Button-1>', lambda e: close() if e.widget is overlay else None)
        overlay.bind('<Escape>', lambda e: close())
        card.bind('<Escape>', lambda e: close())

    def _dlg_variable(self):
        def build(body, close):
            tk.Label(body, text='Nom :', bg=BG, fg=TEXT,
                     font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w', padx=16, pady=(16, 6))
            name_var = tk.StringVar()
            name_entry = tk.Entry(body, textvariable=name_var, font=('Consolas', 10), width=18,
                                  relief='flat', highlightthickness=1, highlightbackground=BORDER)
            name_entry.grid(row=0, column=1, sticky='w', padx=(0, 16), pady=(16, 6))
            body.after(0, name_entry.focus_set)

            tk.Label(body, text='Type :', bg=BG, fg=TEXT,
                     font=('Segoe UI', 9)).grid(row=1, column=0, sticky='w', padx=16, pady=6)
            type_var = tk.StringVar(value='NOMBRE')
            ttk.Combobox(body, textvariable=type_var,
                         values=['NOMBRE', 'TEXTE', 'BOOLEEN', 'LISTE'],
                         state='readonly', width=16).grid(row=1, column=1, sticky='w', padx=(0, 16), pady=6)

            err_label = tk.Label(body, text='', bg=BG, fg=ERR_COLOR, font=('Segoe UI', 8))
            err_label.grid(row=2, column=0, columnspan=2, padx=16)

            def do_insert():
                name = name_var.get().strip()
                if not re.match(r'^[A-Za-z\xc0-\xff_][A-Za-z\xc0-\xff0-9_]*$', name):
                    err_label.configure(text='Nom invalide (lettres, chiffres, _ ; commence par une lettre)')
                    name_entry.focus_set()
                    return
                if name.upper() in RESERVED_WORDS:
                    err_label.configure(text='"' + name + '" est un mot reserve du langage')
                    name_entry.focus_set()
                    return
                vtype = type_var.get()
                decl = f'  {name} EST_DU_TYPE {vtype}\n'
                content = self.code_text.get('1.0', 'end-1c')
                lines_list = content.split('\n')
                insert_at = None
                for idx, ln in enumerate(lines_list):
                    if ln.strip().upper() == 'DEBUT_ALGORITHME':
                        insert_at = f'{idx + 1}.0'
                        break
                if insert_at is None:
                    for idx, ln in enumerate(lines_list):
                        if ln.strip().upper() == 'VARIABLES':
                            insert_at = f'{idx + 2}.0'
                            break
                if insert_at:
                    self.code_text.insert(insert_at, decl)
                    self.highlight()
                    self.linenumbers.redraw()
                close()

            btn_frame = tk.Frame(body, bg=BG)
            btn_frame.grid(row=3, column=0, columnspan=2, pady=(8, 12))
            tk.Button(btn_frame, text='Annuler', command=close, relief='flat',
                      bg=PANEL, fg=TEXT, font=('Segoe UI', 9), padx=10, pady=4).pack(side='left', padx=8)
            tk.Button(btn_frame, text='Inserer', command=do_insert, relief='flat',
                      bg=ACCENT, fg='white', activebackground=ACCENT_DARK, activeforeground='white',
                      font=('Segoe UI', 9, 'bold'), padx=10, pady=4).pack(side='left', padx=8)
            name_entry.bind('<Return>', lambda e: do_insert())
            body.bind('<Return>', lambda e: do_insert())

        self._show_modal('Ajouter une variable', build)

    def _get_declared_vars(self):
        result = []
        in_vars = False
        for ln in self.code_text.get('1.0', 'end-1c').split('\n'):
            t = ln.strip().upper()
            if t == 'VARIABLES':
                in_vars = True
                continue
            if t in ('DEBUT_ALGORITHME', 'FIN_ALGORITHME'):
                break
            if in_vars:
                m = re.match(r'^([A-Za-zÀ-ÿ_][A-Za-zÀ-ÿ0-9_]*)\s+EST_DU_TYPE\s+(NOMBRE|TEXTE|BOOLEEN|LISTE)$',
                             ln.strip(), re.IGNORECASE)
                if m:
                    result.append((m.group(1), m.group(2).upper()))
        return result

    def _dlg_affectation(self):
        vars_list = self._get_declared_vars()

        if not vars_list:
            def build_vide(body, close):
                tk.Label(body, text='Aucune variable declaree.\nAjoute d\'abord une variable\n'
                                   'dans le bloc VARIABLES.',
                         bg=BG, fg=TEXT, font=('Segoe UI', 9), justify='center').pack(padx=20, pady=16)
                btn = tk.Button(body, text='OK', command=close, relief='flat',
                                bg=ACCENT, fg='white', font=('Segoe UI', 9), padx=16, pady=4)
                btn.pack(pady=(0, 14))
                body.after(0, btn.focus_set)
                body.bind('<Return>', lambda e: close())
            self._show_modal('Affecter une valeur', build_vide)
            return

        def build(body, close):
            tk.Label(body, text='Variable :', bg=BG, fg=TEXT,
                     font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w', padx=16, pady=(16, 6))
            var_labels = [f"{n}  ({t})" for n, t in vars_list]
            var_combo = ttk.Combobox(body, values=var_labels, state='readonly', width=28,
                                     font=('Consolas', 10))
            var_combo.current(0)
            var_combo.grid(row=0, column=1, sticky='w', padx=(0, 16), pady=(16, 6))
            body.after(0, var_combo.focus_set)

            dyn = tk.Frame(body, bg=BG)
            dyn.grid(row=1, column=0, columnspan=2, sticky='ew', padx=16)

            expr_var     = tk.StringVar()
            bool_var     = tk.StringVar(value='VRAI')
            idx_var      = tk.StringVar()
            idx_expr_var = tk.StringVar()
            _focus = [None]

            def rebuild_dyn(vtype):
                for w in dyn.winfo_children():
                    w.destroy()
                expr_var.set('')
                if vtype in ('NOMBRE', 'TEXTE'):
                    tk.Label(dyn, text='Expression :', bg=BG, fg=TEXT,
                             font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w', pady=4)
                    ent = tk.Entry(dyn, textvariable=expr_var, font=('Consolas', 10), width=26,
                                   relief='flat', highlightthickness=1, highlightbackground=BORDER)
                    ent.grid(row=0, column=1, sticky='w', padx=(8, 0), pady=4)
                    hint = 'ex : 0   x + 1   ALEA(1, 6)' if vtype == 'NOMBRE' else 'ex : "Bonjour"   prenom + " Dupont"'
                    tk.Label(dyn, text=hint, bg=BG, fg=MUTED,
                             font=('Segoe UI', 8)).grid(row=1, column=0, columnspan=2, sticky='w')
                    _focus[0] = ent
                elif vtype == 'BOOLEEN':
                    bool_var.set('VRAI')
                    tk.Label(dyn, text='Valeur :', bg=BG, fg=TEXT,
                             font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w', pady=4)
                    cb = ttk.Combobox(dyn, textvariable=bool_var,
                                      values=['VRAI', 'FAUX', 'expression...'],
                                      state='readonly', width=20, font=('Consolas', 10))
                    cb.grid(row=0, column=1, sticky='w', padx=(8, 0), pady=4)
                    tk.Label(dyn, text='ou choisir "expression..." pour saisir une condition',
                             bg=BG, fg=MUTED, font=('Segoe UI', 8)).grid(row=1, column=0, columnspan=2, sticky='w')
                    expr_frame = tk.Frame(dyn, bg=BG)
                    ent_expr = tk.Entry(expr_frame, textvariable=expr_var, font=('Consolas', 10), width=26,
                                        relief='flat', highlightthickness=1, highlightbackground=BORDER)
                    ent_expr.pack()
                    def on_bool_cb(event=None):
                        if bool_var.get() == 'expression...':
                            expr_frame.grid(row=2, column=0, columnspan=2, sticky='w', pady=(4, 0))
                            ent_expr.focus_set()
                        else:
                            expr_frame.grid_remove()
                            expr_var.set('')
                    cb.bind('<<ComboboxSelected>>', on_bool_cb)
                    _focus[0] = None
                elif vtype == 'LISTE':
                    idx_var.set('')
                    idx_expr_var.set('')
                    tk.Label(dyn, text='Indice :', bg=BG, fg=TEXT,
                             font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w', pady=4)
                    ent_i = tk.Entry(dyn, textvariable=idx_var, font=('Consolas', 10), width=10,
                                     relief='flat', highlightthickness=1, highlightbackground=BORDER)
                    ent_i.grid(row=0, column=1, sticky='w', padx=(8, 0), pady=4)
                    tk.Label(dyn, text='Valeur :', bg=BG, fg=TEXT,
                             font=('Segoe UI', 9)).grid(row=1, column=0, sticky='w', pady=4)
                    ent_v = tk.Entry(dyn, textvariable=idx_expr_var, font=('Consolas', 10), width=22,
                                     relief='flat', highlightthickness=1, highlightbackground=BORDER)
                    ent_v.grid(row=1, column=1, sticky='w', padx=(8, 0), pady=4)
                    tk.Label(dyn, text='ex : indice 0, valeur 42 ou "Alice"', bg=BG,
                             fg=MUTED, font=('Segoe UI', 8)).grid(row=2, column=0, columnspan=2, sticky='w')
                    _focus[0] = ent_i
                if _focus[0]:
                    _focus[0].focus_set()

            def on_var_change(event=None):
                i = var_combo.current()
                if i >= 0:
                    rebuild_dyn(vars_list[i][1])

            var_combo.bind('<<ComboboxSelected>>', on_var_change)
            rebuild_dyn(vars_list[0][1])

            err_label = tk.Label(body, text='', bg=BG, fg=ERR_COLOR, font=('Segoe UI', 8))
            err_label.grid(row=2, column=0, columnspan=2, padx=16, pady=(6, 0))

            def do_insert():
                ci = var_combo.current()
                if ci < 0:
                    err_label.configure(text='Choisir une variable.')
                    return
                var_name, vtype = vars_list[ci]
                if vtype == 'LISTE':
                    idx_s = idx_var.get().strip()
                    val_s = idx_expr_var.get().strip()
                    if not idx_s:
                        err_label.configure(text='L\'indice est obligatoire.')
                        return
                    if not val_s:
                        err_label.configure(text='La valeur est obligatoire.')
                        return
                    snippet = f'  {var_name}[{idx_s}] PREND_LA_VALEUR {val_s}\n'
                elif vtype == 'BOOLEEN':
                    val_s = bool_var.get()
                    if val_s == 'expression...':
                        val_s = expr_var.get().strip()
                        if not val_s:
                            err_label.configure(text='L\'expression est obligatoire.')
                            return
                    snippet = f'  {var_name} PREND_LA_VALEUR {val_s}\n'
                else:
                    val_s = expr_var.get().strip()
                    if not val_s:
                        err_label.configure(text='La valeur ou l\'expression est obligatoire.')
                        return
                    snippet = f'  {var_name} PREND_LA_VALEUR {val_s}\n'
                self._insert_snippet(snippet)
                close()

            btn_frame = tk.Frame(body, bg=BG)
            btn_frame.grid(row=3, column=0, columnspan=2, pady=(8, 14))
            tk.Button(btn_frame, text='Annuler', command=close, relief='flat',
                      bg=PANEL, fg=TEXT, font=('Segoe UI', 9), padx=10, pady=4).pack(side='left', padx=8)
            tk.Button(btn_frame, text='Inserer', command=do_insert, relief='flat',
                      bg=ACCENT, fg='white', activebackground=ACCENT_DARK, activeforeground='white',
                      font=('Segoe UI', 9, 'bold'), padx=10, pady=4).pack(side='left', padx=8)
            body.bind('<Return>', lambda e: do_insert())

        self._show_modal('Affecter une valeur', build)

    def _dlg_lire(self):
        vars_list = self._get_declared_vars()

        if not vars_list:
            def build_vide(body, close):
                tk.Label(body, text='Aucune variable declaree.\nAjoute d\'abord une variable\n'
                                   'dans le bloc VARIABLES.',
                         bg=BG, fg=TEXT, font=('Segoe UI', 9), justify='center').pack(padx=20, pady=16)
                btn = tk.Button(body, text='OK', command=close, relief='flat',
                                bg=ACCENT, fg='white', font=('Segoe UI', 9), padx=16, pady=4)
                btn.pack(pady=(0, 14))
                body.after(0, btn.focus_set)
                body.bind('<Return>', lambda e: close())
            self._show_modal('Lire une variable', build_vide)
            return

        def build(body, close):
            tk.Label(body, text='Variable :', bg=BG, fg=TEXT,
                     font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w', padx=16, pady=(16, 6))
            var_labels = [f"{n}  ({t})" for n, t in vars_list]
            var_combo = ttk.Combobox(body, values=var_labels, state='readonly', width=26,
                                     font=('Consolas', 10))
            var_combo.current(0)
            var_combo.grid(row=0, column=1, sticky='w', padx=(0, 16), pady=(16, 6))
            body.after(0, var_combo.focus_set)

            idx_frame = tk.Frame(body, bg=BG)
            idx_frame.grid(row=1, column=0, columnspan=2, sticky='w', padx=16)
            idx_var = tk.StringVar()
            idx_label = tk.Label(idx_frame, text='Indice :', bg=BG, fg=TEXT, font=('Segoe UI', 9))
            idx_entry = tk.Entry(idx_frame, textvariable=idx_var, font=('Consolas', 10), width=10,
                                 relief='flat', highlightthickness=1, highlightbackground=BORDER)
            idx_hint  = tk.Label(idx_frame, text='ex : 0   i   LONGUEUR(L) - 1',
                                 bg=BG, fg=MUTED, font=('Segoe UI', 8))

            def update_idx_visibility(event=None):
                i = var_combo.current()
                if i >= 0 and vars_list[i][1] == 'LISTE':
                    idx_label.grid(row=0, column=0, sticky='w', pady=4)
                    idx_entry.grid(row=0, column=1, sticky='w', padx=(8, 0), pady=4)
                    idx_hint.grid(row=1, column=0, columnspan=2, sticky='w')
                    idx_entry.focus_set()
                else:
                    idx_label.grid_remove()
                    idx_entry.grid_remove()
                    idx_hint.grid_remove()
                    idx_var.set('')

            var_combo.bind('<<ComboboxSelected>>', update_idx_visibility)
            update_idx_visibility()

            err_label = tk.Label(body, text='', bg=BG, fg=ERR_COLOR, font=('Segoe UI', 8))
            err_label.grid(row=2, column=0, columnspan=2, padx=16, pady=(4, 0))

            def do_insert():
                ci = var_combo.current()
                if ci < 0:
                    err_label.configure(text='Choisir une variable.')
                    return
                var_name, vtype = vars_list[ci]
                if vtype == 'LISTE':
                    idx_s = idx_var.get().strip()
                    if not idx_s:
                        err_label.configure(text='L\'indice est obligatoire pour une LISTE.')
                        return
                    snippet = f'  LIRE {var_name}[{idx_s}]\n'
                else:
                    snippet = f'  LIRE {var_name}\n'
                self._insert_snippet(snippet)
                close()

            btn_frame = tk.Frame(body, bg=BG)
            btn_frame.grid(row=3, column=0, columnspan=2, pady=(8, 14))
            tk.Button(btn_frame, text='Annuler', command=close, relief='flat',
                      bg=PANEL, fg=TEXT, font=('Segoe UI', 9), padx=10, pady=4).pack(side='left', padx=8)
            tk.Button(btn_frame, text='Inserer', command=do_insert, relief='flat',
                      bg=ACCENT, fg='white', activebackground=ACCENT_DARK, activeforeground='white',
                      font=('Segoe UI', 9, 'bold'), padx=10, pady=4).pack(side='left', padx=8)
            body.bind('<Return>', lambda e: do_insert())

        self._show_modal('Lire une variable', build)

    # ---------- editeur ----------
    def _on_text_yscroll(self, *args):
        self.editor_scroll.set(*args)
        self.linenumbers.redraw()

    def _on_scrollbar(self, *args):
        self.code_text.yview(*args)
        self.linenumbers.redraw()

    def _on_text_change(self, _event=None):
        self.highlight()
        self.linenumbers.redraw()
        if self.status_var.get() == 'Erreur':
            self.status_var.set('')
            self.status_var_color(TEXT)

    def _on_tab(self, _event=None):
        self.code_text.insert(tk.INSERT, '  ')
        return 'break'

    def highlight(self):
        content = self.code_text.get('1.0', 'end-1c')
        for tag in ('kw_block', 'kw_ctrl', 'kw_type', 'kw_bind', 'kw_str', 'kw_num', 'kw_com', 'kw_op'):
            self.code_text.tag_remove(tag, '1.0', 'end')
        i = 0
        n = len(content)

        def add_tag(tag, start, end):
            self.code_text.tag_add(tag, f'1.0+{start}c', f'1.0+{end}c')

        while i < n:
            c = content[i]
            if c == '/' and i + 1 < n and content[i + 1] == '/':
                j = i
                while j < n and content[j] != '\n':
                    j += 1
                add_tag('kw_com', i, j)
                i = j
                continue
            if c == '"':
                j = i + 1
                while j < n and content[j] != '"' and content[j] != '\n':
                    j += 1
                end = j + 1 if j < n and content[j] == '"' else j
                add_tag('kw_str', i, end)
                i = end
                continue
            if c.isdigit():
                j = i
                while j < n and (content[j].isdigit() or content[j] == '.'):
                    j += 1
                add_tag('kw_num', i, j)
                i = j
                continue
            if c.isalpha() or c == '_':
                j = i
                while j < n and (content[j].isalnum() or content[j] == '_'):
                    j += 1
                word = content[i:j]
                cls = classify_word(word)
                if cls:
                    add_tag(cls, i, j)
                i = j
                continue
            if c in '+-*/()<>=![],':
                add_tag('kw_op', i, i + 1)
                i += 1
                continue
            i += 1

    # ---------- actions ----------
    def _check_unsaved(self):
        from tkinter import messagebox
        if not self.code_text.edit_modified():
            return True
        return messagebox.askyesno(
            'Modifications non sauvegardees',
            'Le programme en cours a ete modifie et n\'est pas sauvegarde.\n'
            'Continuer sans sauvegarder ?',
            parent=self.root)

    def on_example_selected(self, _event=None):
        label = self.example_var.get()
        if label == 'Charger un exemple...':
            return
        if not self._check_unsaved():
            self.example_var.set('Charger un exemple...')
            return
        for ex_label, code in EXAMPLES:
            if ex_label == label:
                self.code_text.delete('1.0', 'end')
                self.code_text.insert('1.0', code)
                self.code_text.edit_modified(False)
                self.highlight()
                self.linenumbers.redraw()
                break
        self.example_var.set('Charger un exemple...')

    def on_clear(self):
        if not self._check_unsaved():
            return
        self.code_text.delete('1.0', 'end')
        self.code_text.insert('1.0', DEFAULT_CODE)
        self.code_text.edit_modified(False)
        self.highlight()
        self.linenumbers.redraw()
        self._render_console_message('Aucun resultat pour le moment. Clique sur Executer.')
        for item in self.trace_tree.get_children():
            self.trace_tree.delete(item)
        self.status_var.set('')
        self._current_file = None
        self.root.title('AlgoLabo')

    def on_open(self):
        if not self._check_unsaved():
            return
        path = filedialog.askopenfilename(
            parent=self.root,
            title='Ouvrir un exercice',
            defaultextension='.algo',
            filetypes=[('Fichiers algorithme', '*.algo'), ('Fichiers texte', '*.txt'),
                       ('Tous les fichiers', '*.*')])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self._render_console_message('Impossible d\'ouvrir le fichier : ' + str(e))
            return
        self.code_text.delete('1.0', 'end')
        self.code_text.insert('1.0', content)
        self.code_text.edit_modified(False)
        self.highlight()
        self.linenumbers.redraw()
        self._render_console_message('Aucun resultat pour le moment. Clique sur Executer.')
        for item in self.trace_tree.get_children():
            self.trace_tree.delete(item)
        self.status_var.set('')
        self._current_file = path
        self.root.title('AlgoLabo  -  ' + os.path.basename(path))

    def on_save(self):
        if self._current_file:
            path = self._current_file
        else:
            path = filedialog.asksaveasfilename(
                parent=self.root,
                title='Enregistrer l\'exercice',
                defaultextension='.algo',
                filetypes=[('Fichiers algorithme', '*.algo'), ('Fichiers texte', '*.txt'),
                           ('Tous les fichiers', '*.*')])
            if not path:
                return
        try:
            content = self.code_text.get('1.0', 'end-1c')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            self._render_console_message('Impossible d\'enregistrer le fichier : ' + str(e))
            return
        self._current_file = path
        self.root.title('AlgoLabo  -  ' + os.path.basename(path))
        self.code_text.edit_modified(False)
        self.status_var.set('Enregistre')
        self.status_var_color(OK_COLOR)

    def _ask_lire(self, name, vtype):
        """Modal inline bloquant pour la saisie LIRE — avec bouton Arreter."""
        result = [None]
        done   = tk.BooleanVar(value=False)

        overlay = tk.Frame(self.root, bg='#1A2035')
        overlay.place(x=0, y=0, relwidth=1, relheight=1)
        overlay.lift()

        card = tk.Frame(overlay, bg=BG, highlightbackground=BORDER, highlightthickness=1)

        def close():
            overlay.destroy()
            done.set(True)

        hdr = tk.Frame(card, bg=ACCENT_SOFT)
        hdr.pack(fill='x')
        tk.Label(hdr, text='LIRE ' + name, bg=ACCENT_SOFT, fg=ACCENT_DARK,
                 font=('Segoe UI', 10, 'bold'), padx=14, pady=8).pack(side='left')

        body = tk.Frame(card, bg=BG)
        body.pack(fill='both', expand=True)

        info = tk.Frame(body, bg=BG)
        info.pack(padx=16, pady=(12, 6), anchor='w')
        tk.Label(info, text='Type attendu :', bg=BG, fg=MUTED,
                 font=('Segoe UI', 8)).pack(side='left')
        tk.Label(info, text=vtype, bg=BG, fg=TEXT,
                 font=('Consolas', 9, 'bold')).pack(side='left', padx=(4, 0))

        val_var = tk.StringVar()
        entry = tk.Entry(body, textvariable=val_var, font=('Consolas', 11), width=22,
                         relief='flat', highlightthickness=1, highlightbackground=BORDER)
        entry.pack(padx=16, pady=(0, 4))

        hints = {'NOMBRE': 'ex : 42   3.14   -5',
                 'TEXTE':  'ex : Bonjour   Alice',
                 'BOOLEEN': 'VRAI  ou  FAUX',
                 'LISTE':   'valeur pour un element'}
        tk.Label(body, text=hints.get(vtype, ''), bg=BG, fg=MUTED,
                 font=('Segoe UI', 8)).pack(padx=16)

        err_label = tk.Label(body, text='', bg=BG, fg=ERR_COLOR, font=('Segoe UI', 8))
        err_label.pack(padx=16)

        def do_ok():
            val = val_var.get()
            if not val.strip():
                err_label.configure(text='Entrer une valeur.')
                return
            result[0] = val
            close()

        def do_stop():
            close()  # result[0] reste None -> UserCancelError dans on_run

        btn_frame = tk.Frame(body, bg=BG)
        btn_frame.pack(pady=(8, 14))
        tk.Button(btn_frame, text='■ Arreter', command=do_stop, relief='flat',
                  bg=ERR_BG, fg=ERR_COLOR, font=('Segoe UI', 9),
                  padx=10, pady=4, cursor='hand2').pack(side='left', padx=8)
        tk.Button(btn_frame, text='Valider', command=do_ok, relief='flat',
                  bg=ACCENT, fg='white', activebackground=ACCENT_DARK, activeforeground='white',
                  font=('Segoe UI', 9, 'bold'), padx=10, pady=4, cursor='hand2').pack(side='left', padx=8)

        entry.bind('<Return>', lambda e: do_ok())
        overlay.bind('<Escape>', lambda e: do_stop())
        card.bind('<Escape>', lambda e: do_stop())

        overlay.update_idletasks()
        cw = card.winfo_reqwidth()
        ch = card.winfo_reqheight()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        card.place(x=max(16, (rw - cw) // 2), y=max(16, (rh - ch) // 2))
        body.after(0, entry.focus_set)

        self.root.wait_variable(done)

        if result[0] is None:
            raise UserCancelError()
        return result[0]

    def on_run(self):
        source = self.code_text.get('1.0', 'end-1c')
        trace_on = self.trace_var.get()

        self.code_text.tag_remove('err_line', '1.0', 'end')

        try:
            prog = parse_program(source)
            self.fc_renderer.render(prog)
            self._fc_msg.set('Algorigramme genere.')
        except AlgoError:
            pass

        self.console_text.configure(state='normal')
        self.console_text.delete('1.0', 'end')
        self.console_text.configure(state='disabled')
        lines_written = [0]

        def stream_output(text):
            self.console_text.configure(state='normal')
            self.console_text.insert('end', text + '\n')
            self.console_text.see('end')
            self.console_text.configure(state='disabled')
            lines_written[0] += 1
            self.root.update_idletasks()

        def ask_input(name, vtype):
            val = self._ask_lire(name, vtype)
            self.console_text.configure(state='normal')
            self.console_text.insert('end', f'> LIRE {name} : {val}\n', 'input_echo')
            self.console_text.see('end')
            self.console_text.configure(state='disabled')
            lines_written[0] += 1
            return val

        for item in self.trace_tree.get_children():
            self.trace_tree.delete(item)

        try:
            res = run_program(source, trace=trace_on, read_input=ask_input,
                              write_output=stream_output)
            if lines_written[0] == 0:
                self._render_console_message(
                    'Ce programme ne produit aucun affichage (aucun ECRIRE execute).')
            if trace_on:
                for step in res['trace']:
                    state_str = '   '.join(
                        '%s = %s' % (k, self._format_display(v)) for k, v in step['state'].items())
                    self.trace_tree.insert('', 'end', values=(step['line'], step['action'], state_str))
            self.status_var.set('Execution terminee')
            self.status_var_color(OK_COLOR)
        except UserCancelError:
            self.console_text.configure(state='normal')
            if lines_written[0] > 0:
                self.console_text.insert('end', '\n')
            self.console_text.insert('end', 'Execution annulee par l\'utilisateur.', 'muted')
            self.console_text.configure(state='disabled')
            self.status_var.set('Annule')
            self.status_var_color(MUTED)
        except AlgoError as e:
            ligne = (' (ligne %s)' % e.line) if getattr(e, 'line', None) else ''
            if getattr(e, 'line', None):
                self.code_text.tag_add('err_line', '%d.0' % e.line, '%d.end+1c' % e.line)
                self.code_text.see('%d.0' % e.line)
            self.console_text.configure(state='normal')
            if lines_written[0] > 0:
                self.console_text.insert('end', '\n')
            self.console_text.insert('end', 'Erreur%s :\n%s' % (ligne, e.message), 'err')
            self.console_text.configure(state='disabled')
            self.status_var.set('Erreur')
            self.status_var_color(ERR_COLOR)

    def status_var_color(self, color):
        self.status_label.configure(fg=color)

    def _format_display(self, v):
        if isinstance(v, bool):
            return 'VRAI' if v else 'FAUX'
        if isinstance(v, dict):
            return '[liste]'
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v)

    def _render_console_message(self, msg):
        self.console_text.configure(state='normal')
        self.console_text.delete('1.0', 'end')
        self.console_text.insert('end', msg, 'muted')
        self.console_text.configure(state='disabled')
