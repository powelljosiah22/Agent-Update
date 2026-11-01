#!/usr/bin/env python3
"""
Deterministic Morphological Decoder & Phonetic Transliterator
Supports:
  1. OpenScriptures Hebrew/Aramaic Morphology (OSHb / WLC: e.g., 'HR/Ncfsa', 'HVqp3ms')
  2. MorphGNT SBLGNT Greek Morphology (POS + 8-char parse code: e.g., 'V-' + '3AAI-S--')
  3. CATSS / Rahlfs LXX Greek Morphology & Robinson-Pierpont codes
  4. Academic Phonetic Transliteration for Biblical Hebrew/Aramaic and Koine Greek
"""
import re
import unicodedata

# ==============================================================================
# 1. PHONETIC TRANSLITERATION (HEBREW & GREEK)
# ==============================================================================

HEB_MAP = {
    '\u05d0': "'",    # Alef
    '\u05d1': 'b',    # Bet
    '\u05d2': 'g',    # Gimel
    '\u05d3': 'd',    # Dalet
    '\u05d4': 'h',    # He
    '\u05d5': 'w',    # Vav
    '\u05d6': 'z',    # Zayin
    '\u05d7': 'ch',   # Chet
    '\u05d8': 't',    # Tet
    '\u05d9': 'y',    # Yod
    '\u05da': 'k',    # Final Kaf
    '\u05db': 'k',    # Kaf
    '\u05dc': 'l',    # Lamed
    '\u05dd': 'm',    # Final Mem
    '\u05de': 'm',    # Mem
    '\u05df': 'n',    # Final Nun
    '\u05e0': 'n',    # Nun
    '\u05e1': 's',    # Samekh
    '\u05e2': '`',    # Ayin
    '\u05e3': 'p',    # Final Pe
    '\u05e4': 'p',    # Pe
    '\u05e5': 'ts',   # Final Tsadi
    '\u05e6': 'ts',   # Tsadi
    '\u05e7': 'q',    # Qof
    '\u05e8': 'r',    # Resh
    '\u05e9': 'sh',   # Shin/Sin
    '\u05ea': 't',    # Tav
    # Vowels
    '\u05b0': 'e',    # Sheva
    '\u05b1': 'e',    # Hataf Segol
    '\u05b2': 'a',    # Hataf Patah
    '\u05b3': 'o',    # Hataf Qamats
    '\u05b4': 'i',    # Hiriq
    '\u05b5': 'e',    # Tsere
    '\u05b6': 'e',    # Segol
    '\u05b7': 'a',    # Patah
    '\u05b8': 'a',    # Qamats
    '\u05b9': 'o',    # Holam
    '\u05ba': 'o',    # Holam Haser
    '\u05bb': 'u',    # Qubuts
    '\u05be': '-',    # Maqaf
    '/': '/',
}

GRK_MAP = {
    'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z',
    'η': 'ē', 'θ': 'th', 'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm',
    'ν': 'n', 'ξ': 'x', 'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's',
    'ς': 's', 'τ': 't', 'υ': 'y', 'φ': 'ph', 'χ': 'ch', 'ψ': 'ps',
    'ω': 'ō',
    'Α': 'A', 'Β': 'B', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E', 'Ζ': 'Z',
    'Η': 'Ē', 'Θ': 'Th', 'Ι': 'I', 'Κ': 'K', 'Λ': 'L', 'Μ': 'M',
    'Ν': 'N', 'Ξ': 'X', 'Ο': 'O', 'Π': 'P', 'Ρ': 'R', 'Σ': 'S',
    'Τ': 'T', 'Υ': 'Y', 'Φ': 'Ph', 'Χ': 'Ch', 'Ψ': 'Ps', 'Ω': 'Ō',
}


def transliterate_hebrew(text: str) -> str:
    if not text:
        return ""
    nfd = unicodedata.normalize('NFD', text)
    out = []
    i = 0
    while i < len(nfd):
        ch = nfd[i]
        # Check Shin vs Sin dot
        if ch == '\u05e9':
            if i + 1 < len(nfd) and nfd[i + 1] == '\u05c2':
                out.append('s')
                i += 2
                continue
            elif i + 1 < len(nfd) and nfd[i + 1] == '\u05c1':
                out.append('sh')
                i += 2
                continue
        if ch in HEB_MAP:
            out.append(HEB_MAP[ch])
        i += 1
    res = "".join(out)
    # Collapse duplicate vowels lightly
    return res.strip("'") if len(res) > 2 else res


def transliterate_greek(text: str) -> str:
    if not text:
        return ""
    nfd = unicodedata.normalize('NFD', text)
    out = []
    rough_breathing = False
    for ch in nfd:
        if ch == '\u0314':  # Rough breathing (dasia)
            rough_breathing = True
        elif ch in GRK_MAP:
            mapped = GRK_MAP[ch]
            if rough_breathing and mapped.lower() in ('a', 'e', 'ē', 'i', 'o', 'y', 'ō', 'r'):
                if mapped == 'r':
                    mapped = 'rh'
                elif mapped == 'R':
                    mapped = 'Rh'
                elif mapped[0].isupper():
                    mapped = 'H' + mapped.lower()
                else:
                    mapped = 'h' + mapped
                rough_breathing = False
            out.append(mapped)
    res = "".join(out)
    # γγ -> ng, γκ -> nk, γξ -> nx, γχ -> nch
    for src, dst in (('gg', 'ng'), ('gk', 'nk'), ('gx', 'nx'), ('gch', 'nch'), ('ay', 'au'), ('ey', 'eu'), ('oy', 'ou')):
        res = res.replace(src, dst)
    return res


def transliterate(text: str) -> str:
    if not text:
        return ""
    for ch in text:
        cp = ord(ch)
        if 0x0590 <= cp <= 0x05FF:
            return transliterate_hebrew(text)
        if (0x0370 <= cp <= 0x03FF) or (0x1F00 <= cp <= 0x1FFF):
            return transliterate_greek(text)
    return text


# ==============================================================================
# 2. OPENSCRIPTURES HEBREW/ARAMAIC MORPHOLOGY DECODER (OSHb)
# ==============================================================================

HEB_POS = {
    'A': 'Adjective',
    'C': 'Conjunction',
    'D': 'Adverb',
    'N': 'Noun',
    'P': 'Pronoun',
    'R': 'Preposition',
    'S': 'Suffix',
    'T': 'Particle',
    'V': 'Verb',
}

HEB_STEMS = {
    'q': 'Qal', 'N': 'Niphal', 'p': 'Piel', 'P': 'Pual',
    'h': 'Hiphil', 'H': 'Hophal', 't': 'Hithpael', 'o': 'Polel',
    'O': 'Polal', 'r': 'Hithpolel', 'm': 'Poel', 'M': 'Poal',
    'k': 'Palel', 'K': 'Pulal', 'Q': 'Qal Passive', 'l': 'Pilpel',
    'L': 'Polpal', 'f': 'Hithpalpel', 'D': 'Nithpael', 'j': 'Pealal',
    'i': 'Pilel', 'u': 'Hothpaal', 'c': 'Tiphil', 'v': 'Hishtaphel',
}

ARAM_STEMS = {
    'q': 'Peal', 'Q': 'Peil', 'u': 'Hithpeel', 'p': 'Pael',
    'P': 'Ithpaal', 'M': 'Hithpaal', 'a': 'Aphel', 'h': 'Haphel',
    's': 'Shaphel', 'e': 'Shaphel', 'H': 'Hophal', 'i': 'Ithpeel',
    't': 'Hishtaphel', 'v': 'Ithpoel', 'w': 'Hithpolel',
}

HEB_VERB_TYPE = {
    'p': 'Perfect (Qatal)',
    'q': 'Sequential Perfect (Weqatal)',
    'i': 'Imperfect (Yiqtol)',
    'w': 'Sequential Imperfect (Wayyiqtol)',
    'h': 'Cohortative',
    'j': 'Jussive',
    'v': 'Imperative',
    'r': 'Participle Active',
    's': 'Participle Passive',
    'a': 'Infinitive Absolute',
    'c': 'Infinitive Construct',
}

HEB_NOUN_TYPE = {'c': 'Common', 'p': 'Proper', 'g': 'Gentilic'}
HEB_ADJ_TYPE = {'a': 'Adjective', 'c': 'Cardinal Number', 'g': 'Gentilic', 'o': 'Ordinal Number'}
HEB_PRON_TYPE = {'d': 'Demonstrative', 'f': 'Indefinite', 'i': 'Interrogative', 'p': 'Personal', 'r': 'Relative'}
HEB_PART_TYPE = {
    'a': 'Affirmation', 'd': 'Definite Article', 'e': 'Exhortation',
    'i': 'Interrogative', 'j': 'Interjection', 'm': 'Demonstrative',
    'n': 'Negative', 'o': 'Direct Object Marker (et)', 'r': 'Relative',
}
HEB_SFX_TYPE = {'d': 'Directional He', 'h': 'Paragogic He', 'n': 'Paragogic Nun', 'p': 'Pronominal Suffix'}

HEB_PERSON = {'1': '1st Person', '2': '2nd Person', '3': '3rd Person'}
HEB_GENDER = {'b': 'Both', 'c': 'Common', 'f': 'Feminine', 'm': 'Masculine'}
HEB_NUMBER = {'d': 'Dual', 'p': 'Plural', 's': 'Singular'}
HEB_STATE = {'a': 'Absolute', 'c': 'Construct', 'd': 'Determined'}


def _decode_oshb_segment(seg: str, lang: str = 'H') -> str:
    if not seg:
        return ""
    pos_code = seg[0]
    pos = HEB_POS.get(pos_code, pos_code)
    rest = seg[1:]
    parts = [pos]

    if pos_code == 'V' and rest:
        stems = ARAM_STEMS if lang == 'A' else HEB_STEMS
        if len(rest) >= 1:
            parts.append(stems.get(rest[0], rest[0]))
        if len(rest) >= 2:
            parts.append(HEB_VERB_TYPE.get(rest[1], rest[1]))
        idx = 2
        if idx < len(rest) and rest[idx] in HEB_PERSON:
            parts.append(HEB_PERSON[rest[idx]])
            idx += 1
        if idx < len(rest) and rest[idx] in HEB_GENDER:
            parts.append(HEB_GENDER[rest[idx]])
            idx += 1
        if idx < len(rest) and rest[idx] in HEB_NUMBER:
            parts.append(HEB_NUMBER[rest[idx]])
            idx += 1
        if idx < len(rest) and rest[idx] in HEB_STATE:
            parts.append(HEB_STATE[rest[idx]])
    elif pos_code in ('N', 'A') and rest:
        tmap = HEB_NOUN_TYPE if pos_code == 'N' else HEB_ADJ_TYPE
        if len(rest) >= 1 and rest[0] in tmap:
            parts.append(tmap[rest[0]])
        if len(rest) >= 2 and rest[1] in HEB_GENDER:
            parts.append(HEB_GENDER[rest[1]])
        if len(rest) >= 3 and rest[2] in HEB_NUMBER:
            parts.append(HEB_NUMBER[rest[2]])
        if len(rest) >= 4 and rest[3] in HEB_STATE:
            parts.append(HEB_STATE[rest[3]])
    elif pos_code == 'P' and rest:
        if len(rest) >= 1 and rest[0] in HEB_PRON_TYPE:
            parts.append(HEB_PRON_TYPE[rest[0]])
        idx = 1
        if idx < len(rest) and rest[idx] in HEB_PERSON:
            parts.append(HEB_PERSON[rest[idx]])
            idx += 1
        if idx < len(rest) and rest[idx] in HEB_GENDER:
            parts.append(HEB_GENDER[rest[idx]])
            idx += 1
        if idx < len(rest) and rest[idx] in HEB_NUMBER:
            parts.append(HEB_NUMBER[rest[idx]])
    elif pos_code == 'T' and rest:
        if rest[0] in HEB_PART_TYPE:
            parts.append(HEB_PART_TYPE[rest[0]])
    elif pos_code == 'S' and rest:
        if rest[0] in HEB_SFX_TYPE:
            parts.append(HEB_SFX_TYPE[rest[0]])
        idx = 1
        if idx < len(rest) and rest[idx] in HEB_PERSON:
            parts.append(HEB_PERSON[rest[idx]])
            idx += 1
        if idx < len(rest) and rest[idx] in HEB_GENDER:
            parts.append(HEB_GENDER[rest[idx]])
            idx += 1
        if idx < len(rest) and rest[idx] in HEB_NUMBER:
            parts.append(HEB_NUMBER[rest[idx]])

    return " ".join(parts)


def decode_hebrew_morph(morph_code: str) -> str:
    if not morph_code:
        return ""
    lang = 'H'
    code = morph_code
    if code[0] in ('H', 'A'):
        lang = code[0]
        code = code[1:]
    lang_prefix = "[Aram] " if lang == 'A' else ""
    segs = [_decode_oshb_segment(s, lang) for s in code.split('/') if s]
    return lang_prefix + " + ".join(segs)


# ==============================================================================
# 3. GREEK MORPHOLOGY DECODER (MorphGNT & Robinson / CATSS LXX)
# ==============================================================================

GRK_POS = {
    'A-': 'Adjective', 'C-': 'Conjunction', 'D-': 'Adverb',
    'I-': 'Interjection', 'N-': 'Noun', 'P-': 'Preposition',
    'RA': 'Definite Article', 'RD': 'Demonstrative Pronoun',
    'RI': 'Interrogative/Indefinite Pronoun', 'RP': 'Personal Pronoun',
    'RR': 'Relative Pronoun', 'V-': 'Verb', 'X-': 'Particle',
    'A': 'Adjective', 'C': 'Conjunction', 'D': 'Adverb',
    'I': 'Interjection', 'N': 'Noun', 'P': 'Preposition',
    'R': 'Pronoun/Article', 'V': 'Verb', 'X': 'Particle', 'T': 'Article',
}

GRK_PERSON = {'1': '1st Person', '2': '2nd Person', '3': '3rd Person'}
GRK_TENSE = {
    'P': 'Present', 'I': 'Imperfect', 'F': 'Future',
    'A': 'Aorist', 'X': 'Perfect', 'Y': 'Pluperfect', 'R': 'Perfect', 'L': 'Pluperfect'
}
GRK_VOICE = {'A': 'Active', 'M': 'Middle', 'P': 'Passive', 'E': 'Middle/Passive', 'D': 'Middle Deponent', 'O': 'Passive Deponent', 'N': 'Middle/Passive Deponent'}
GRK_MOOD = {'I': 'Indicative', 'D': 'Imperative', 'S': 'Subjunctive', 'O': 'Optative', 'N': 'Infinitive', 'P': 'Participle'}
GRK_CASE = {'N': 'Nominative', 'G': 'Genitive', 'D': 'Dative', 'A': 'Accusative', 'V': 'Vocative'}
GRK_NUMBER = {'S': 'Singular', 'P': 'Plural', 'D': 'Dual'}
GRK_GENDER = {'M': 'Masculine', 'F': 'Feminine', 'N': 'Neuter'}
GRK_DEGREE = {'C': 'Comparative', 'S': 'Superlative'}


def decode_morphgnt(pos: str, parse_code: str) -> str:
    """Decodes MorphGNT 2-char POS and 8-char parse_code (Person, Tense, Voice, Mood, Case, Number, Gender, Degree)."""
    parts = []
    if pos:
        parts.append(GRK_POS.get(pos, pos))
    if parse_code and len(parse_code) == 8:
        p, t, v, m, c, n, g, d = list(parse_code)
        if t in GRK_TENSE:
            parts.append(GRK_TENSE[t])
        if v in GRK_VOICE:
            parts.append(GRK_VOICE[v])
        if m in GRK_MOOD:
            parts.append(GRK_MOOD[m])
        if p in GRK_PERSON:
            parts.append(GRK_PERSON[p])
        if c in GRK_CASE:
            parts.append(GRK_CASE[c])
        if n in GRK_NUMBER:
            parts.append(GRK_NUMBER[n])
        if g in GRK_GENDER:
            parts.append(GRK_GENDER[g])
        if d in GRK_DEGREE:
            parts.append(GRK_DEGREE[d])
    return " ".join(parts)


def decode_lxx_morph(pos_or_morph: str) -> str:
    """Decodes CATSS / Rahlfs LXX morph codes (e.g., 'V.AAI3S', 'N.NSM', 'RA.NSM', 'P', 'C')."""
    if not pos_or_morph:
        return ""
    code = pos_or_morph.strip()
    simple_map = {
        'P': 'Preposition', 'PREP': 'Preposition',
        'C': 'Conjunction', 'CONJ': 'Conjunction',
        'D': 'Adverb', 'ADV': 'Adverb',
        'X': 'Particle', 'PRT': 'Particle',
        'I': 'Interjection', 'INJ': 'Interjection',
        'HEB': 'Indeclinable Hebrew Loanword',
        'ARAM': 'Indeclinable Aramaic Loanword',
    }
    if code in simple_map:
        return simple_map[code]

    # Split on '.' or '-' if present (e.g. 'RA.NSM', 'V.AAI3S', 'N.DSF')
    if '.' in code or '-' in code:
        segs = re.split(r'[.\-]', code)
        pos_seg = segs[0]
        rest = "".join(segs[1:])
    else:
        pos_seg = code[:2] if code[:2] in GRK_POS else code[:1]
        rest = code[len(pos_seg):]

    parts = [GRK_POS.get(pos_seg, simple_map.get(pos_seg, pos_seg))]

    if pos_seg.startswith('V') and len(rest) >= 3:
        if rest[0].isdigit() and len(rest) >= 4:
            rest = rest[1:]
        t, v, m = rest[0], rest[1], rest[2]
        if t in GRK_TENSE:
            parts.append(GRK_TENSE[t])
        if v in GRK_VOICE:
            parts.append(GRK_VOICE[v])
        if m in GRK_MOOD:
            parts.append(GRK_MOOD[m])
        tail = rest[3:]
        if m == 'P':  # Participle: Case, Number, Gender
            for ch in tail:
                if ch in GRK_CASE:
                    parts.append(GRK_CASE[ch])
                elif ch in GRK_NUMBER:
                    parts.append(GRK_NUMBER[ch])
                elif ch in GRK_GENDER:
                    parts.append(GRK_GENDER[ch])
        else:
            for ch in tail:
                if ch in GRK_PERSON:
                    parts.append(GRK_PERSON[ch])
                elif ch in GRK_NUMBER:
                    parts.append(GRK_NUMBER[ch])
    else:
        for ch in rest:
            if ch in GRK_CASE:
                parts.append(GRK_CASE[ch])
            elif ch in GRK_NUMBER:
                parts.append(GRK_NUMBER[ch])
            elif ch in GRK_GENDER:
                parts.append(GRK_GENDER[ch])
            elif ch in GRK_DEGREE:
                parts.append(GRK_DEGREE[ch])

    return " ".join(parts) if len(parts) >= 1 else code
