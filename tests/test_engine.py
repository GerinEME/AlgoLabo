# -*- coding: utf-8 -*-
from engine import run_program, AlgoError


def test(name, source, expected_output, read_input=None):
    try:
        res = run_program(source, read_input=read_input)
        ok = res['output'] == expected_output
        print(('OK   ' if ok else 'FAIL ') + name)
        if not ok:
            print('  attendu :', expected_output)
            print('  obtenu  :', res['output'])
    except AlgoError as e:
        print('ERREUR ' + name + ' : ' + e.message + ' (ligne ' + str(e.line) + ')')


def expect_error(label, source):
    try:
        run_program(source)
        print('FAIL : ' + label + ' aurait du lever une erreur')
    except AlgoError as e:
        print('OK   : ' + label + ' -> ' + e.message + ' (ligne ' + str(e.line) + ')')


test('SI-SINON', """
VARIABLES
  x EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  x PREND_LA_VALEUR 5
  SI (x > 0) ALORS
    DEBUT_SI
    ECRIRE "positif"
    FIN_SI
  SINON
    DEBUT_SINON
    ECRIRE "negatif"
    FIN_SINON
FIN_ALGORITHME
""", ['positif'])

test('POUR-somme', """
VARIABLES
  i EST_DU_TYPE NOMBRE
  somme EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  somme PREND_LA_VALEUR 0
  POUR i ALLANT_DE 1 A 5
    DEBUT_POUR
    somme PREND_LA_VALEUR somme + i
    FIN_POUR
  ECRIRE somme
FIN_ALGORITHME
""", ['15'])

test('TANT_QUE', """
VARIABLES
  n EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  n PREND_LA_VALEUR 0
  TANT_QUE (n < 3) FAIRE
    DEBUT_TANT_QUE
    ECRIRE n
    n PREND_LA_VALEUR n + 1
    FIN_TANT_QUE
FIN_ALGORITHME
""", ['0', '1', '2'])

test('LIRE', """
VARIABLES
  x EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  LIRE x
  ECRIRE x * 2
FIN_ALGORITHME
""", ['42'], read_input=lambda name, vtype: '21')

test('logique ET/OU/NON', """
VARIABLES
  a EST_DU_TYPE BOOLEEN
  b EST_DU_TYPE BOOLEEN
DEBUT_ALGORITHME
  a PREND_LA_VALEUR VRAI
  b PREND_LA_VALEUR FAUX
  SI (a ET NON b) ALORS
    DEBUT_SI
    ECRIRE "ok"
    FIN_SI
  SINON
    DEBUT_SINON
    ECRIRE "non"
    FIN_SINON
FIN_ALGORITHME
""", ['ok'])

test('concat texte', """
VARIABLES
  note EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  note PREND_LA_VALEUR 14
  ECRIRE "Note : " + note + "/20"
FIN_ALGORITHME
""", ['Note : 14/20'])

test('POUR imbrique', """
VARIABLES
  i EST_DU_TYPE NOMBRE
  j EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  POUR i ALLANT_DE 1 A 2
    DEBUT_POUR
    POUR j ALLANT_DE 1 A 2
      DEBUT_POUR
      ECRIRE i * j
      FIN_POUR
    FIN_POUR
FIN_ALGORITHME
""", ['1', '2', '2', '4'])

test('commentaires', """
VARIABLES
  x EST_DU_TYPE NOMBRE // variable de test
DEBUT_ALGORITHME
  // initialisation
  x PREND_LA_VALEUR 1
  ECRIRE x
FIN_ALGORITHME
""", ['1'])

test('MOD parite', """
VARIABLES
  i EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  POUR i ALLANT_DE 1 A 4
    DEBUT_POUR
    SI (i MOD 2 == 0) ALORS
      DEBUT_SI
      ECRIRE "pair"
      FIN_SI
    SINON
      DEBUT_SINON
      ECRIRE "impair"
      FIN_SINON
    FIN_POUR
FIN_ALGORITHME
""", ['impair', 'pair', 'impair', 'pair'])

test('ECRIRE synonyme', """
VARIABLES
  x EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  x PREND_LA_VALEUR 3
  ECRIRE "x vaut " + x
  ECRIRE "et ca marche aussi"
FIN_ALGORITHME
""", ['x vaut 3', 'et ca marche aussi'])

test('LISTE de nombres', """
VARIABLES
  L EST_DU_TYPE LISTE
  i EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  POUR i ALLANT_DE 0 A 4
    DEBUT_POUR
    L[i] PREND_LA_VALEUR i * i
    FIN_POUR
  ECRIRE L[3]
  ECRIRE LONGUEUR(L)
FIN_ALGORITHME
""", ['9', '5'])

test('LISTE de chaines', """
VARIABLES
  prenoms EST_DU_TYPE LISTE
DEBUT_ALGORITHME
  prenoms[0] PREND_LA_VALEUR "Alice"
  prenoms[1] PREND_LA_VALEUR "Bilal"
  prenoms[2] PREND_LA_VALEUR "Chloe"
  ECRIRE prenoms[0] + " et " + prenoms[2]
FIN_ALGORITHME
""", ['Alice et Chloe'])

test('LISTE mixte', """
VARIABLES
  L EST_DU_TYPE LISTE
  i EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  L[0] PREND_LA_VALEUR "premier"
  L[1] PREND_LA_VALEUR 42
  L[2] PREND_LA_VALEUR VRAI
  POUR i ALLANT_DE 0 A LONGUEUR(L) - 1
    DEBUT_POUR
    ECRIRE L[i]
    FIN_POUR
FIN_ALGORITHME
""", ['premier', '42', 'VRAI'])

test('DIV (division entiere)', """
VARIABLES
  a EST_DU_TYPE NOMBRE
  b EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  a PREND_LA_VALEUR 17
  b PREND_LA_VALEUR 5
  ECRIRE a DIV b
  ECRIRE a MOD b
FIN_ALGORITHME
""", ['3', '2'])

test('recherche dichotomique (DIV)', """
VARIABLES
  L EST_DU_TYPE LISTE
  gauche EST_DU_TYPE NOMBRE
  droite EST_DU_TYPE NOMBRE
  milieu EST_DU_TYPE NOMBRE
  cible EST_DU_TYPE NOMBRE
  trouve EST_DU_TYPE BOOLEEN
DEBUT_ALGORITHME
  L[0] PREND_LA_VALEUR 2
  L[1] PREND_LA_VALEUR 5
  L[2] PREND_LA_VALEUR 9
  L[3] PREND_LA_VALEUR 14
  L[4] PREND_LA_VALEUR 21
  cible PREND_LA_VALEUR 14
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
FIN_ALGORITHME
""", ["Trouve a l'indice 3"])

test('chaine : LONGUEUR et extraction de lettre', """
VARIABLES
  mot EST_DU_TYPE TEXTE
  i EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  mot PREND_LA_VALEUR "BONJOUR"
  ECRIRE LONGUEUR(mot)
  ECRIRE mot[0]
  ECRIRE mot[6]
FIN_ALGORITHME
""", ['7', 'B', 'R'])

test('chaine : parcours lettre par lettre (POUR + LONGUEUR + index)', """
VARIABLES
  mot EST_DU_TYPE TEXTE
  i EST_DU_TYPE NOMBRE
  nbVoyelles EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  mot PREND_LA_VALEUR "ALGORITHME"
  nbVoyelles PREND_LA_VALEUR 0
  POUR i ALLANT_DE 0 A LONGUEUR(mot) - 1
    DEBUT_POUR
    SI (mot[i] == "A" OU mot[i] == "E" OU mot[i] == "I" OU mot[i] == "O" OU mot[i] == "U") ALORS
      DEBUT_SI
      nbVoyelles PREND_LA_VALEUR nbVoyelles + 1
      FIN_SI
    FIN_POUR
  ECRIRE nbVoyelles
FIN_ALGORITHME
""", ['4'])

print('\n--- verification specifique de ALEA (bornes respectees sur 200 tirages) ---')
ok_alea = True
for _ in range(200):
    res = run_program("""
VARIABLES
  x EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  x PREND_LA_VALEUR ALEA(1, 6)
  ECRIRE x
FIN_ALGORITHME
""")
    val = int(res['output'][0])
    if val < 1 or val > 6:
        ok_alea = False
        print('FAIL : valeur hors bornes ->', val)
        break
print('OK   : ALEA(1, 6) reste dans [1, 6] sur 200 tirages' if ok_alea else 'FAIL : ALEA hors bornes')

expect_error("ALEA avec des bornes inversees", """
VARIABLES
  x EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  x PREND_LA_VALEUR ALEA(10, 1)
FIN_ALGORITHME
""")
expect_error("extraction hors des limites d'une chaine", """
VARIABLES
  mot EST_DU_TYPE TEXTE
DEBUT_ALGORITHME
  mot PREND_LA_VALEUR "AB"
  ECRIRE mot[5]
FIN_ALGORITHME
""")

print('\n--- verification des erreurs ---')
expect_error('variable non declaree', """
VARIABLES
  x EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  y PREND_LA_VALEUR 3
FIN_ALGORITHME
""")
expect_error('division par zero', """
VARIABLES
  x EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  x PREND_LA_VALEUR 5 / 0
FIN_ALGORITHME
""")
expect_error("lecture d'un indice non initialise", """
VARIABLES
  L EST_DU_TYPE LISTE
DEBUT_ALGORITHME
  ECRIRE L[0]
FIN_ALGORITHME
""")
expect_error('ECRIRE une liste entiere sans indice', """
VARIABLES
  L EST_DU_TYPE LISTE
DEBUT_ALGORITHME
  L[0] PREND_LA_VALEUR 1
  ECRIRE L
FIN_ALGORITHME
""")
expect_error('LIRE une liste entiere sans indice', """
VARIABLES
  L EST_DU_TYPE LISTE
DEBUT_ALGORITHME
  LIRE L
FIN_ALGORITHME
""")
expect_error("indexer une variable qui n'est pas une liste", """
VARIABLES
  x EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  x PREND_LA_VALEUR 5
  ECRIRE x[0]
FIN_ALGORITHME
""")
expect_error('mot reserve comme nom de variable', """
VARIABLES
  SI EST_DU_TYPE NOMBRE
DEBUT_ALGORITHME
  ECRIRE SI
FIN_ALGORITHME
""")
expect_error('mot reserve VRAI comme nom de variable', """
VARIABLES
  VRAI EST_DU_TYPE BOOLEEN
DEBUT_ALGORITHME
  ECRIRE VRAI
FIN_ALGORITHME
""")
