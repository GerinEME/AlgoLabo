# -*- coding: utf-8 -*-
"""AlgoLabo : moteur d'interpretation de pseudo-code, en Python pur (sans dependance externe)."""

import re
import random
import math


class AlgoError(Exception):
    def __init__(self, message, line):
        super().__init__(message)
        self.message = message
        self.line = line


class UserCancelError(Exception):
    """Levee quand l'utilisateur ferme une boite LIRE sans saisir de valeur."""
    pass


class RetourException(Exception):
    """Levee par RETOUR pour remonter la valeur de retour hors de la fonction."""
    def __init__(self, value, line):
        self.value = value
        self.line = line


# ---------- Tokenizer d'expressions ----------
def tokenize_expr(src, line_num):
    tokens = []
    i = 0
    n = len(src)
    ident_start_re = re.compile(r'[A-Za-zÀ-ÿ_]')
    ident_part_re = re.compile(r'[A-Za-zÀ-ÿ0-9_]')
    kw_words = {'ET', 'OU', 'NON', 'MOD', 'DIV', 'VRAI', 'FAUX'}

    while i < n:
        c = src[i]
        if c in (' ', '\t'):
            i += 1
            continue
        if c == '"':
            j = i + 1
            buf = []
            while j < n and src[j] != '"':
                buf.append(src[j])
                j += 1
            if j >= n:
                raise AlgoError('Chaine de caracteres non fermee (guillemet manquant)', line_num)
            tokens.append({'type': 'string', 'value': ''.join(buf)})
            i = j + 1
            continue
        if c.isdigit() or (c == '.' and i + 1 < n and src[i + 1].isdigit()):
            j = i
            buf = []
            while j < n and (src[j].isdigit() or src[j] == '.'):
                buf.append(src[j])
                j += 1
            tokens.append({'type': 'number', 'value': float(''.join(buf))})
            i = j
            continue
        if ident_start_re.match(c):
            j = i
            buf = []
            while j < n and ident_part_re.match(src[j]):
                buf.append(src[j])
                j += 1
            word = ''.join(buf)
            upper = word.upper()
            if upper in kw_words:
                tokens.append({'type': 'kw', 'value': upper})
            else:
                tokens.append({'type': 'ident', 'value': word})
            i = j
            continue
        if c == '<' and i + 1 < n and src[i + 1] == '=':
            tokens.append({'type': 'op', 'value': '<='}); i += 2; continue
        if c == '>' and i + 1 < n and src[i + 1] == '=':
            tokens.append({'type': 'op', 'value': '>='}); i += 2; continue
        if c == '=' and i + 1 < n and src[i + 1] == '=':
            tokens.append({'type': 'op', 'value': '=='}); i += 2; continue
        if c == '!' and i + 1 < n and src[i + 1] == '=':
            tokens.append({'type': 'op', 'value': '!='}); i += 2; continue
        if c in '+-*/()<>=![],':
            tokens.append({'type': 'op', 'value': c}); i += 1; continue
        raise AlgoError('Caractere non reconnu : "' + c + '"', line_num)
    return tokens


# ---------- Parser d'expressions (recursive descent, precedence) ----------
def parse_expr(tokens, line_num):
    pos_box = [0]

    def peek():
        return tokens[pos_box[0]] if pos_box[0] < len(tokens) else None

    def advance():
        t = peek()
        pos_box[0] += 1
        return t

    def expect_op(val):
        t = advance()
        if not t or t['value'] != val:
            raise AlgoError('Expression invalide, "' + val + '" attendu', line_num)
        return t

    def parse_ou():
        left = parse_et()
        while peek() and peek()['type'] == 'kw' and peek()['value'] == 'OU':
            advance()
            right = parse_et()
            left = {'type': 'logic', 'op': 'OU', 'left': left, 'right': right}
        return left

    def parse_et():
        left = parse_egalite()
        while peek() and peek()['type'] == 'kw' and peek()['value'] == 'ET':
            advance()
            right = parse_egalite()
            left = {'type': 'logic', 'op': 'ET', 'left': left, 'right': right}
        return left

    def parse_egalite():
        left = parse_comparaison()
        while peek() and peek()['type'] == 'op' and peek()['value'] in ('==', '!='):
            op = advance()['value']
            right = parse_comparaison()
            left = {'type': 'compare', 'op': op, 'left': left, 'right': right}
        return left

    def parse_comparaison():
        left = parse_addition()
        while peek() and peek()['type'] == 'op' and peek()['value'] in ('<', '>', '<=', '>='):
            op = advance()['value']
            right = parse_addition()
            left = {'type': 'compare', 'op': op, 'left': left, 'right': right}
        return left

    def parse_addition():
        left = parse_mult()
        while peek() and peek()['type'] == 'op' and peek()['value'] in ('+', '-'):
            op = advance()['value']
            right = parse_mult()
            left = {'type': 'arith', 'op': op, 'left': left, 'right': right}
        return left

    def parse_mult():
        left = parse_unaire()
        while peek() and ((peek()['type'] == 'op' and peek()['value'] in ('*', '/')) or
                           (peek()['type'] == 'kw' and peek()['value'] in ('MOD', 'DIV'))):
            op = advance()['value']
            right = parse_unaire()
            left = {'type': 'arith', 'op': op, 'left': left, 'right': right}
        return left

    def parse_unaire():
        if peek() and peek()['type'] == 'op' and peek()['value'] == '-':
            advance()
            return {'type': 'neg', 'expr': parse_unaire()}
        if peek() and peek()['type'] == 'kw' and peek()['value'] == 'NON':
            advance()
            return {'type': 'not', 'expr': parse_unaire()}
        return parse_primaire()

    def parse_primaire():
        t = peek()
        if not t:
            raise AlgoError('Expression incomplete', line_num)
        if t['type'] == 'number':
            advance(); return {'type': 'num', 'value': t['value']}
        if t['type'] == 'string':
            advance(); return {'type': 'str', 'value': t['value']}
        if t['type'] == 'kw' and t['value'] == 'VRAI':
            advance(); return {'type': 'bool', 'value': True}
        if t['type'] == 'kw' and t['value'] == 'FAUX':
            advance(); return {'type': 'bool', 'value': False}
        if t['type'] == 'ident':
            upper_name = t['value'].upper()
            after = tokens[pos_box[0] + 1] if pos_box[0] + 1 < len(tokens) else None
            if upper_name == 'LONGUEUR' and after and after['type'] == 'op' and after['value'] == '(':
                advance()  # LONGUEUR
                advance()  # (
                arg_tok = advance()
                if not arg_tok or arg_tok['type'] != 'ident':
                    raise AlgoError('LONGUEUR attend le nom d\'une liste ou d\'une chaine entre parentheses, ex : LONGUEUR(maListe)', line_num)
                expect_op(')')
                return {'type': 'longueur', 'name': arg_tok['value']}
            if upper_name == 'ALEA' and after and after['type'] == 'op' and after['value'] == '(':
                advance()  # ALEA
                advance()  # (
                if peek() and peek()['type'] == 'op' and peek()['value'] == ')':
                    advance()
                    return {'type': 'alea'}
                arg1 = parse_ou()
                if not peek() or peek()['value'] != ',':
                    raise AlgoError('ALEA attend deux bornes separees par une virgule, ex : ALEA(1, 100), ou aucun argument : ALEA()', line_num)
                advance()  # ,
                arg2 = parse_ou()
                expect_op(')')
                return {'type': 'alea', 'fromExpr': arg1, 'toExpr': arg2}
            advance()  # consomme l'identifiant
            if peek() and peek()['type'] == 'op' and peek()['value'] == '[':
                advance()
                idx_expr = parse_ou()
                expect_op(']')
                return {'type': 'index', 'name': t['value'], 'indexExpr': idx_expr}
            # Appel de fonction utilisateur
            if peek() and peek()['type'] == 'op' and peek()['value'] == '(':
                advance()  # (
                args = []
                if not (peek() and peek()['type'] == 'op' and peek()['value'] == ')'):
                    args.append(parse_ou())
                    while peek() and peek()['type'] == 'op' and peek()['value'] == ',':
                        advance()  # ,
                        args.append(parse_ou())
                expect_op(')')
                return {'type': 'call', 'name': t['value'], 'args': args}
            return {'type': 'var', 'name': t['value']}
        if t['type'] == 'op' and t['value'] == '(':
            advance()
            e = parse_ou()
            expect_op(')')
            return e
        raise AlgoError('Expression invalide pres de "' + str(t['value']) + '"', line_num)

    result = parse_ou()
    if pos_box[0] < len(tokens):
        raise AlgoError('Symboles inattendus en fin d\'expression : "' + str(tokens[pos_box[0]]['value']) + '"', line_num)
    return result


def parse_expr_string(src, line_num):
    tokens = tokenize_expr(src, line_num)
    if len(tokens) == 0:
        raise AlgoError('Expression vide', line_num)
    return parse_expr(tokens, line_num)


# ---------- Evaluateur d'expressions ----------
def fmt_num(x):
    if float(x).is_integer():
        return str(int(x))
    return str(round(x, 9))


def fmt_val(v):
    if isinstance(v, bool):
        return 'VRAI' if v else 'FAUX'
    if isinstance(v, (int, float)):
        return fmt_num(v)
    return str(v)


def eval_expr(node, env, line_num, call_fn=None):
    t = node['type']
    if t == 'num':
        return node['value']
    if t == 'str':
        return node['value']
    if t == 'bool':
        return node['value']
    if t == 'var':
        if node['name'] not in env:
            raise AlgoError('Variable "' + node['name'] + '" non declaree (absente du bloc VARIABLES ou des parametres de la fonction)', line_num)
        v = env[node['name']]
        if isinstance(v, dict):
            raise AlgoError('"' + node['name'] + '" est une liste : precise un indice (ex. ' + node['name'] + '[i]) ou utilise LONGUEUR(' + node['name'] + ')', line_num)
        return v
    if t == 'index':
        if node['name'] not in env:
            raise AlgoError('Variable "' + node['name'] + '" non declaree (absente du bloc VARIABLES)', line_num)
        target = env[node['name']]
        idx = eval_expr(node['indexExpr'], env, line_num, call_fn)
        if isinstance(idx, bool) or not isinstance(idx, (int, float)) or not float(idx).is_integer() or idx < 0:
            raise AlgoError('L\'indice doit etre un nombre entier positif ou nul', line_num)
        idx = int(idx)
        if isinstance(target, dict):
            if idx not in target:
                raise AlgoError('Aucune valeur a l\'indice ' + str(idx) + ' de la liste "' + node['name'] + '" (initialise-la avant de la lire)', line_num)
            return target[idx]
        if isinstance(target, str):
            if idx >= len(target):
                raise AlgoError('L\'indice ' + str(idx) + ' depasse la longueur de la chaine "' + node['name'] + '" (longueur ' + str(len(target)) + ', derniere lettre a l\'indice ' + str(len(target) - 1) + ')', line_num)
            return target[idx]
        raise AlgoError('"' + node['name'] + '" n\'est pas une liste ni une chaine de caracteres, on ne peut pas l\'indexer', line_num)
    if t == 'longueur':
        if node['name'] not in env:
            raise AlgoError('Variable "' + node['name'] + '" non declaree (absente du bloc VARIABLES)', line_num)
        target = env[node['name']]
        if isinstance(target, dict):
            return (max(target.keys()) + 1) if target else 0
        if isinstance(target, str):
            return len(target)
        raise AlgoError('LONGUEUR ne s\'applique qu\'a une liste ou a une chaine de caracteres', line_num)
    if t == 'alea':
        if 'fromExpr' not in node:
            return random.random()
        frm = eval_expr(node['fromExpr'], env, line_num, call_fn)
        to = eval_expr(node['toExpr'], env, line_num, call_fn)
        if isinstance(frm, bool) or isinstance(to, bool) or not isinstance(frm, (int, float)) or not isinstance(to, (int, float)):
            raise AlgoError('ALEA attend des bornes numeriques, ex : ALEA(1, 100)', line_num)
        if not float(frm).is_integer() or not float(to).is_integer():
            raise AlgoError('ALEA attend des bornes entieres, ex : ALEA(1, 100)', line_num)
        frm, to = int(frm), int(to)
        if frm > to:
            raise AlgoError('ALEA : la borne de depart doit etre inferieure ou egale a la borne de fin', line_num)
        return float(random.randint(frm, to))
    if t == 'call':
        if call_fn is None:
            raise AlgoError('Appel de fonction "' + node['name'] + '" impossible dans ce contexte', line_num)
        return call_fn(node['name'], node['args'], env, line_num)
    if t == 'neg':
        v = eval_expr(node['expr'], env, line_num, call_fn)
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise AlgoError('Impossible d\'appliquer "-" a une valeur non numerique', line_num)
        return -v
    if t == 'not':
        return not eval_expr(node['expr'], env, line_num, call_fn)
    if t == 'logic':
        l = eval_expr(node['left'], env, line_num, call_fn)
        r = eval_expr(node['right'], env, line_num, call_fn)
        return (l and r) if node['op'] == 'ET' else (l or r)
    if t == 'compare':
        l = eval_expr(node['left'], env, line_num, call_fn)
        r = eval_expr(node['right'], env, line_num, call_fn)
        op = node['op']
        if op == '<': return l < r
        if op == '>': return l > r
        if op == '<=': return l <= r
        if op == '>=': return l >= r
        if op == '==': return l == r
        if op == '!=': return l != r
    if t == 'arith':
        l = eval_expr(node['left'], env, line_num, call_fn)
        r = eval_expr(node['right'], env, line_num, call_fn)
        op = node['op']
        if op == '+':
            if isinstance(l, str) or isinstance(r, str):
                def as_text(v):
                    if isinstance(v, bool):
                        return 'VRAI' if v else 'FAUX'
                    if isinstance(v, (int, float)):
                        return fmt_num(v)
                    return v
                return as_text(l) + as_text(r)
            return l + r
        if isinstance(l, bool) or isinstance(r, bool) or not isinstance(l, (int, float)) or not isinstance(r, (int, float)):
            raise AlgoError('Operation "' + op + '" impossible sur une valeur non numerique', line_num)
        if op == '-': return l - r
        if op == '*': return l * r
        if op == '/':
            if r == 0: raise AlgoError('Division par zero', line_num)
            return l / r
        if op == 'MOD':
            if r == 0: raise AlgoError('Division par zero (MOD)', line_num)
            return float(l) % float(r)
        if op == 'DIV':
            if r == 0: raise AlgoError('Division par zero (DIV)', line_num)
            return float(math.floor(l / r))
    raise AlgoError('Expression non evaluable', line_num)


# ---------- Parseur de programme (blocs) ----------
def prep_lines(source):
    raw = source.split('\n')
    lines = []
    for idx, text in enumerate(raw):
        in_str = False
        c_idx = -1
        for k, ch in enumerate(text):
            if ch == '"':
                in_str = not in_str
            elif not in_str and ch == '/' and k + 1 < len(text) and text[k + 1] == '/':
                c_idx = k
                break
        if c_idx != -1:
            text = text[:c_idx]
        text = text.strip()
        if len(text) > 0:
            lines.append({'text': text, 'num': idx + 1})
    return lines


def split_first_word(text):
    m = re.match(r'^(\S+)\s*(.*)$', text)
    if not m:
        return text, ''
    return m.group(1), m.group(2)


TYPES_CONNUS = ['NOMBRE', 'TEXTE', 'BOOLEEN', 'LISTE']

RESERVED_WORDS = {
    'VARIABLES', 'DEBUT_ALGORITHME', 'FIN_ALGORITHME',
    'EST_DU_TYPE', 'PREND_LA_VALEUR',
    'NOMBRE', 'TEXTE', 'BOOLEEN', 'LISTE',
    'LIRE', 'ECRIRE', 'AFFICHER',
    'SI', 'ALORS', 'SINON', 'DEBUT_SI', 'FIN_SI', 'DEBUT_SINON', 'FIN_SINON',
    'POUR', 'ALLANT_DE', 'FAIRE', 'DEBUT_POUR', 'FIN_POUR',
    'TANT_QUE', 'DEBUT_TANT_QUE', 'FIN_TANT_QUE',
    'ET', 'OU', 'NON', 'MOD', 'DIV',
    'VRAI', 'FAUX',
    'ALEA', 'LONGUEUR',
    'FONCTION', 'DEBUT_FONCTION', 'FIN_FONCTION', 'RETOUR',
}


def parse_program(source):
    lines = prep_lines(source)
    pos_box = [0]

    def cur():
        return lines[pos_box[0]] if pos_box[0] < len(lines) else None

    def expect_word_line(word):
        l = cur()
        if not l:
            raise AlgoError('Fin de programme inattendue, "' + word + '" attendu', lines[-1]['num'] if lines else 1)
        if l['text'].upper() != word:
            raise AlgoError('"' + word + '" attendu, trouve : "' + l['text'] + '"', l['num'])
        pos_box[0] += 1
        return l

    def find_keyword_end(text, word):
        m = re.search(r'\b' + word + r'\b\s*$', text, re.IGNORECASE)
        return m.start() if m else -1

    def strip_parens(text):
        text = text.strip()
        if text.startswith('(') and text.endswith(')'):
            depth = 0
            ok = True
            for idx, ch in enumerate(text):
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
                    if depth == 0 and idx != len(text) - 1:
                        ok = False
                        break
            if ok:
                return text[1:-1]
        return text

    def parse_block(stop_words):
        stmts = []
        while cur() and cur()['text'].upper() not in stop_words:
            stmts.append(parse_statement())
        return stmts

    def parse_statement():
        l = cur()
        if not l:
            raise AlgoError('Instruction attendue mais fin de programme atteinte', lines[-1]['num'] if lines else 1)
        first_word_raw, rest = split_first_word(l['text'])
        first_word = first_word_raw.upper()

        if first_word == 'LIRE':
            pos_box[0] += 1
            target = rest.strip()
            idx_match = re.match(r'^([A-Za-zÀ-ÿ_][A-Za-zÀ-ÿ0-9_]*)\s*\[(.+)\]$', target)
            if idx_match:
                list_name = idx_match.group(1)
                index_expr = parse_expr_string(idx_match.group(2), l['num'])
                return {'type': 'LIRE_INDEX', 'name': list_name, 'indexExpr': index_expr, 'line': l['num']}
            if not re.match(r'^[A-Za-zÀ-ÿ_][A-Za-zÀ-ÿ0-9_]*$', target):
                raise AlgoError('LIRE doit etre suivi du nom d\'une variable (ou d\'un element de liste comme L[i]), trouve : "' + rest + '"', l['num'])
            return {'type': 'LIRE', 'name': target, 'line': l['num']}

        if first_word in ('AFFICHER', 'ECRIRE'):
            pos_box[0] += 1
            expr = parse_expr_string(rest, l['num'])
            return {'type': 'ECRIRE', 'expr': expr, 'line': l['num']}

        if first_word == 'SI':
            pos_box[0] += 1
            cond = rest.strip()
            alors_idx = find_keyword_end(cond, 'ALORS')
            if alors_idx == -1:
                raise AlgoError('SI doit se terminer par ALORS', l['num'])
            cond_src = cond[:alors_idx].strip()
            cond_expr = parse_expr_string(strip_parens(cond_src), l['num'])
            expect_word_line('DEBUT_SI')
            then_block = parse_block(['FIN_SI'])
            expect_word_line('FIN_SI')
            else_block = []
            if cur() and cur()['text'].upper() == 'SINON':
                pos_box[0] += 1
                expect_word_line('DEBUT_SINON')
                else_block = parse_block(['FIN_SINON'])
                expect_word_line('FIN_SINON')
            return {'type': 'SI', 'cond': cond_expr, 'thenBlock': then_block, 'elseBlock': else_block, 'line': l['num']}

        if first_word == 'POUR':
            pos_box[0] += 1
            m = re.match(r'^([A-Za-zÀ-ÿ_][A-Za-zÀ-ÿ0-9_]*)\s+ALLANT_DE\s+(.+?)\s+A\s+(.+)$', rest, re.IGNORECASE)
            if not m:
                raise AlgoError('POUR doit avoir la forme : POUR var ALLANT_DE debut A fin', l['num'])
            var_name = m.group(1)
            from_expr = parse_expr_string(m.group(2), l['num'])
            to_expr = parse_expr_string(m.group(3), l['num'])
            expect_word_line('DEBUT_POUR')
            block = parse_block(['FIN_POUR'])
            expect_word_line('FIN_POUR')
            return {'type': 'POUR', 'varName': var_name, 'fromExpr': from_expr, 'toExpr': to_expr, 'block': block, 'line': l['num']}

        if first_word == 'TANT_QUE':
            pos_box[0] += 1
            cond = rest.strip()
            faire_idx = find_keyword_end(cond, 'FAIRE')
            if faire_idx == -1:
                raise AlgoError('TANT_QUE doit se terminer par FAIRE', l['num'])
            cond_src = cond[:faire_idx].strip()
            cond_expr = parse_expr_string(strip_parens(cond_src), l['num'])
            expect_word_line('DEBUT_TANT_QUE')
            block = parse_block(['FIN_TANT_QUE'])
            expect_word_line('FIN_TANT_QUE')
            return {'type': 'TANT_QUE', 'cond': cond_expr, 'block': block, 'line': l['num']}

        if first_word == 'RETOUR':
            pos_box[0] += 1
            expr = parse_expr_string(rest.strip(), l['num']) if rest.strip() else None
            return {'type': 'RETOUR', 'expr': expr, 'line': l['num']}

        pv_match = re.match(r'^(.+?)\s+PREND_LA_VALEUR\s+(.+)$', l['text'], re.IGNORECASE)
        if pv_match:
            pos_box[0] += 1
            lhs = pv_match.group(1).strip()
            rhs_expr = parse_expr_string(pv_match.group(2), l['num'])
            idx_match = re.match(r'^([A-Za-zÀ-ÿ_][A-Za-zÀ-ÿ0-9_]*)\s*\[(.+)\]$', lhs)
            if idx_match:
                list_name = idx_match.group(1)
                index_expr = parse_expr_string(idx_match.group(2), l['num'])
                return {'type': 'AFFECT_INDEX', 'name': list_name, 'indexExpr': index_expr, 'expr': rhs_expr, 'line': l['num']}
            if not re.match(r'^[A-Za-zÀ-ÿ_][A-Za-zÀ-ÿ0-9_]*$', lhs):
                raise AlgoError('Affectation invalide : "' + lhs + '" n\'est pas un nom de variable valide', l['num'])
            return {'type': 'AFFECT', 'name': lhs, 'expr': rhs_expr, 'line': l['num']}

        # Appel de fonction nu : nom(arg1, arg2)
        if re.match(r'^[A-Za-zÀ-ÿ_][A-Za-zÀ-ÿ0-9_]*\s*\(', l['text']):
            call_expr = parse_expr_string(l['text'], l['num'])
            if call_expr.get('type') == 'call':
                pos_box[0] += 1
                return {'type': 'APPEL_FONCTION', 'call_expr': call_expr, 'line': l['num']}

        raise AlgoError('Instruction non reconnue (hors du programme officiel) : "' + l['text'] + '"', l['num'])

    # ----- Blocs FONCTION optionnels (avant VARIABLES) -----
    functions = {}
    while cur() and re.match(r'^FONCTION\b', cur()['text'], re.IGNORECASE):
        func_line = cur()
        pos_box[0] += 1
        m = re.match(r'^FONCTION\s+([A-Za-zÀ-ÿ_][A-Za-zÀ-ÿ0-9_]*)\s*\(([^)]*)\)\s*$', func_line['text'], re.IGNORECASE)
        if not m:
            raise AlgoError('Declaration de fonction invalide. Syntaxe attendue : FONCTION nom(param1, param2)', func_line['num'])
        func_name = m.group(1)
        if func_name.upper() in RESERVED_WORDS:
            raise AlgoError('"' + func_name + '" est un mot reserve et ne peut pas etre utilise comme nom de fonction', func_line['num'])
        params_str = m.group(2).strip()
        params = [p.strip() for p in params_str.split(',') if p.strip()] if params_str else []
        for p in params:
            if not re.match(r'^[A-Za-zÀ-ÿ_][A-Za-zÀ-ÿ0-9_]*$', p):
                raise AlgoError('Nom de parametre invalide : "' + p + '"', func_line['num'])
        expect_word_line('DEBUT_FONCTION')
        func_body = parse_block(['FIN_FONCTION'])
        expect_word_line('FIN_FONCTION')
        if func_name in functions:
            raise AlgoError('Fonction "' + func_name + '" declaree plusieurs fois', func_line['num'])
        functions[func_name] = {'params': params, 'body': func_body, 'line': func_line['num']}

    # ----- Bloc VARIABLES -----
    if not cur() or cur()['text'].upper() != 'VARIABLES':
        raise AlgoError('Le programme doit commencer par VARIABLES (ou par des blocs FONCTION avant VARIABLES)', cur()['num'] if cur() else 1)
    pos_box[0] += 1

    declarations = []
    seen_decl = set()
    while cur() and cur()['text'].upper() != 'DEBUT_ALGORITHME':
        l = cur()
        m = re.match(r'^([A-Za-zÀ-ÿ_][A-Za-zÀ-ÿ0-9_]*)\s+EST_DU_TYPE\s+([A-Za-zÀ-ÿ_]+)$', l['text'], re.IGNORECASE)
        if not m:
            raise AlgoError('Declaration de variable invalide (attendu : nom EST_DU_TYPE NOMBRE/TEXTE/BOOLEEN/LISTE) : "' + l['text'] + '"', l['num'])
        var_name = m.group(1)
        if var_name.upper() in RESERVED_WORDS:
            raise AlgoError('"' + var_name + '" est un mot reserve du langage et ne peut pas etre utilise comme nom de variable', l['num'])
        if var_name in seen_decl:
            raise AlgoError('Variable "' + var_name + '" declaree plusieurs fois dans le bloc VARIABLES', l['num'])
        seen_decl.add(var_name)
        var_type = m.group(2).upper()
        if var_type not in TYPES_CONNUS:
            raise AlgoError('Type inconnu "' + var_type + '" (types autorises : NOMBRE, TEXTE, BOOLEEN, LISTE)', l['num'])
        declarations.append({'name': var_name, 'vtype': var_type, 'line': l['num']})
        pos_box[0] += 1

    if len(declarations) == 0:
        raise AlgoError('Le bloc VARIABLES doit declarer au moins une variable', cur()['num'] if cur() else 1)
    expect_word_line('DEBUT_ALGORITHME')

    body = parse_block(['FIN_ALGORITHME'])
    expect_word_line('FIN_ALGORITHME')
    if pos_box[0] != len(lines):
        raise AlgoError('Instructions presentes apres FIN_ALGORITHME', lines[pos_box[0]]['num'])

    return {'declarations': declarations, 'body': body, 'functions': functions}


# ---------- Execution ----------
MAX_STEPS = 200000


def run_program(source, trace=False, read_input=None, write_output=None):
    if read_input is None:
        read_input = lambda name, vtype: '0'
    if write_output is None:
        write_output = lambda text: None

    output = []
    trace_list = []
    step_count_box = [0]

    program = parse_program(source)
    functions = program['functions']
    env = {}
    decl = {}
    for d in program['declarations']:
        decl[d['name']] = d['vtype']
        if d['vtype'] == 'NOMBRE':
            env[d['name']] = 0
        elif d['vtype'] == 'BOOLEEN':
            env[d['name']] = False
        elif d['vtype'] == 'LISTE':
            env[d['name']] = {}
        else:
            env[d['name']] = ''

    def snapshot():
        return dict(env)

    def push_trace(line, action):
        if trace:
            trace_list.append({'line': line, 'action': action, 'state': snapshot()})

    def tick(line):
        step_count_box[0] += 1
        if step_count_box[0] > MAX_STEPS:
            raise AlgoError('Execution interrompue : trop d\'etapes (protection contre les boucles infinies)', line)

    def exec_block(stmts):
        for s in stmts:
            exec_stmt(s)

    def coerce_input_value(raw, vtype):
        if vtype == 'NOMBRE':
            try:
                return float(str(raw).replace(',', '.'))
            except ValueError:
                return None
        if vtype == 'BOOLEEN':
            up = str(raw).strip().upper()
            return up in ('VRAI', '1', 'TRUE')
        return str(raw)

    def guess_value(raw_str):
        raw_str = raw_str.strip()
        if re.match(r'^-?[0-9]+(\.[0-9]+)?$', raw_str):
            return float(raw_str)
        if raw_str.upper() == 'VRAI':
            return True
        if raw_str.upper() == 'FAUX':
            return False
        return raw_str

    def call_fn(name, arg_nodes, caller_env, line_num):
        if name not in functions:
            raise AlgoError(
                'Fonction "' + name + '" non definie. Declare-la avec FONCTION ' + name + '(...) avant VARIABLES',
                line_num)
        func = functions[name]
        if len(arg_nodes) != len(func['params']):
            raise AlgoError(
                'Fonction "' + name + '" attend ' + str(len(func['params'])) + ' argument(s), ' +
                str(len(arg_nodes)) + ' fourni(s)',
                line_num)
        # Evaluer les arguments dans le scope appelant
        arg_vals = [eval_expr(a, caller_env, line_num, call_fn) for a in arg_nodes]
        # Sauvegarder le scope courant
        saved_env = dict(env)
        saved_decl = dict(decl)
        # Installer le scope local (parametres uniquement)
        env.clear()
        decl.clear()
        for param, val in zip(func['params'], arg_vals):
            env[param] = val
            decl[param] = None  # pas de verification de type sur les parametres
        result = None
        try:
            exec_block(func['body'])
        except RetourException as e:
            result = e.value
        finally:
            env.clear()
            env.update(saved_env)
            decl.clear()
            decl.update(saved_decl)
        return result

    def exec_stmt(s):
        tick(s['line'])
        t = s['type']
        if t == 'LIRE':
            if decl.get(s['name']) == 'LISTE':
                raise AlgoError('Impossible de LIRE une liste entiere : precise un indice, par exemple LIRE ' + s['name'] + '[i]', s['line'])
            raw = read_input(s['name'], decl.get(s['name']))
            if decl.get(s['name']) == 'NOMBRE':
                val = coerce_input_value(raw, 'NOMBRE')
                if val is None:
                    raise AlgoError('Valeur saisie invalide pour la variable numerique "' + s['name'] + '"', s['line'])
            else:
                val = coerce_input_value(raw, decl.get(s['name']))
            env[s['name']] = val
            push_trace(s['line'], 'LIRE ' + s['name'] + ' = ' + fmt_val(val))
        elif t == 'LIRE_INDEX':
            if decl.get(s['name']) != 'LISTE':
                raise AlgoError('"' + s['name'] + '" n\'est pas une liste (declare-la avec EST_DU_TYPE LISTE)', s['line'])
            idx = eval_expr(s['indexExpr'], env, s['line'], call_fn)
            if isinstance(idx, bool) or not isinstance(idx, (int, float)) or not float(idx).is_integer() or idx < 0:
                raise AlgoError('L\'indice d\'une liste doit etre un nombre entier positif ou nul', s['line'])
            idx = int(idx)
            raw = read_input(s['name'] + '[' + str(idx) + ']', 'LISTE')
            val = guess_value(str(raw))
            env[s['name']][idx] = val
            push_trace(s['line'], 'LIRE ' + s['name'] + '[' + str(idx) + '] = ' + fmt_val(val))
        elif t == 'ECRIRE':
            v = eval_expr(s['expr'], env, s['line'], call_fn)
            output.append(fmt_val(v))
            write_output(fmt_val(v))
            push_trace(s['line'], 'ECRIRE ' + fmt_val(v))
        elif t == 'AFFECT':
            if s['name'] not in env:
                raise AlgoError('Variable "' + s['name'] + '" non declaree', s['line'])
            if decl.get(s['name']) == 'LISTE':
                raise AlgoError('Impossible d\'affecter une liste entiere : precise un indice, par exemple ' + s['name'] + '[i] PREND_LA_VALEUR ...', s['line'])
            v = eval_expr(s['expr'], env, s['line'], call_fn)
            vtype = decl.get(s['name'])
            if vtype == 'NOMBRE':
                if isinstance(v, bool) or not isinstance(v, (int, float)):
                    raise AlgoError('La variable "' + s['name'] + '" est de type NOMBRE : impossible de lui affecter "' + fmt_val(v) + '" (valeur non numerique)', s['line'])
            elif vtype == 'TEXTE':
                if not isinstance(v, str):
                    raise AlgoError('La variable "' + s['name'] + '" est de type TEXTE : impossible de lui affecter une valeur numerique ou booleenne (utilise ECRIRE pour convertir)', s['line'])
            elif vtype == 'BOOLEEN':
                if not isinstance(v, bool):
                    raise AlgoError('La variable "' + s['name'] + '" est de type BOOLEEN : affecter VRAI ou FAUX uniquement (ex : ' + s['name'] + ' PREND_LA_VALEUR VRAI)', s['line'])
            env[s['name']] = v
            push_trace(s['line'], s['name'] + ' PREND_LA_VALEUR ' + fmt_val(v))
        elif t == 'AFFECT_INDEX':
            if decl.get(s['name']) != 'LISTE':
                raise AlgoError('"' + s['name'] + '" n\'est pas une liste (declare-la avec EST_DU_TYPE LISTE)', s['line'])
            idx = eval_expr(s['indexExpr'], env, s['line'], call_fn)
            if isinstance(idx, bool) or not isinstance(idx, (int, float)) or not float(idx).is_integer() or idx < 0:
                raise AlgoError('L\'indice d\'une liste doit etre un nombre entier positif ou nul', s['line'])
            idx = int(idx)
            v = eval_expr(s['expr'], env, s['line'], call_fn)
            env[s['name']][idx] = v
            push_trace(s['line'], s['name'] + '[' + str(idx) + '] PREND_LA_VALEUR ' + fmt_val(v))
        elif t == 'SI':
            c = eval_expr(s['cond'], env, s['line'], call_fn)
            push_trace(s['line'], 'SI -> ' + ('VRAI (branche ALORS)' if c else 'FAUX (branche SINON)'))
            exec_block(s['thenBlock'] if c else s['elseBlock'])
        elif t == 'POUR':
            frm = eval_expr(s['fromExpr'], env, s['line'], call_fn)
            to = eval_expr(s['toExpr'], env, s['line'], call_fn)
            if isinstance(frm, bool) or isinstance(to, bool) or not isinstance(frm, (int, float)) or not isinstance(to, (int, float)):
                raise AlgoError('Les bornes de POUR doivent etre numeriques', s['line'])
            if not float(frm).is_integer() or not float(to).is_integer():
                raise AlgoError('Les bornes de POUR doivent etre des entiers (ex : POUR i ALLANT_DE 1 A 10)', s['line'])
            if s['varName'] not in env:
                raise AlgoError('La variable de boucle "' + s['varName'] + '" doit etre declaree dans le bloc VARIABLES', s['line'])
            for val in range(int(frm), int(to) + 1):
                env[s['varName']] = float(val)
                push_trace(s['line'], s['varName'] + ' = ' + str(val))
                exec_block(s['block'])
                tick(s['line'])
        elif t == 'TANT_QUE':
            while eval_expr(s['cond'], env, s['line'], call_fn):
                tick(s['line'])
                exec_block(s['block'])
            push_trace(s['line'], 'TANT_QUE termine')
        elif t == 'RETOUR':
            v = eval_expr(s['expr'], env, s['line'], call_fn) if s['expr'] is not None else None
            raise RetourException(v, s['line'])
        elif t == 'APPEL_FONCTION':
            eval_expr(s['call_expr'], env, s['line'], call_fn)  # valeur de retour ignoree

    try:
        exec_block(program['body'])
    except RetourException as e:
        raise AlgoError('RETOUR utilise en dehors d\'une fonction', e.line)

    return {'output': output, 'trace': trace_list, 'declarations': program['declarations']}
