"""Locators: map an item's loc to a raw-text passage (start, end) in the local text."""
import re
import sys
sys.path.insert(0, '/home/claude/ipd/verification/tools')
from x1lib import basic_norm

NUMHEAD = re.compile(r'^\s*(?:\d{1,4}\s{2,})?((?:[A-C]\.)?\d+(?:\.\d+)*)(\.?)\s+(\S.*)$')


def lines_with_offsets(raw, start=0, end=None):
    if end is None:
        end = len(raw)
    off = start
    for l in raw[start:end].split('\n'):
        yield off, l
        off += len(l) + 1


def is_toc(l):
    return bool(re.search(r'\.{5,}|…{3,}', l))


def find_numeric_section(raw, key, start=0, end=None, require_text=True, skip_toc=True, nth=0):
    """Find heading line beginning with section number key; return (s, e)."""
    if end is None:
        end = len(raw)
    pat = re.compile(r'^\s*(?:\d{1,4}\s{2,})?' + re.escape(key) + r'\.?\s+(\S)')
    hits = []
    for off, l in lines_with_offsets(raw, start, end):
        l2 = l.replace('\f', '')
        if pat.match(l2) and not (skip_toc and is_toc(l2)):
            hits.append(off)
    if len(hits) <= nth:
        return None
    s = hits[nth]
    # find end: next numeric heading not a descendant
    first = True
    for off, l in lines_with_offsets(raw, s, end):
        if first:
            first = False
            continue
        l2 = l.replace('\f', '')
        m = NUMHEAD.match(l2)
        if m and not is_toc(l2):
            num = m.group(1)
            dot = m.group(2)
            if '.' not in num and not dot:
                continue  # bare number, not a heading
            if num == key or num.startswith(key + '.'):
                continue
            # numbers must be plausible siblings: share structure
            return (s, off)
    return (s, end)


def find_line(raw, regex, start=0, end=None, skip_toc=True, flags=0):
    if end is None:
        end = len(raw)
    pat = re.compile(regex, flags)
    for off, l in lines_with_offsets(raw, start, end):
        l2 = basic_norm(l.replace('\f', ''))
        if pat.search(l2) and not (skip_toc and is_toc(l2)):
            return off
    return None


# ------------------------------------------------------------------ E6R3
E6_REGIONS = None


def e6_regions(raw):
    global E6_REGIONS
    if E6_REGIONS:
        return E6_REGIONS
    def lo(rx, after=0):
        return find_line(raw, rx, after)
    p = lo(r'^II\.\s+PRINCIPLES OF ICH GCP\s*$', 5000)
    a1 = lo(r'^III\.\s+ANNEX 1\s*$', p)
    a2 = lo(r'^IV\.\s+ANNEX 2\s*$', a1)
    apa = lo(r'^Appendix A\. INVESTIGATOR', a2)
    apb = lo(r'^Appendix B\. CLINICAL TRIAL PROTOCOL', apa)
    apc = lo(r'^Appendix C\. ESSENTIAL RECORDS', apb)
    gl = lo(r'^GLOSSARY\s*$', apc)
    E6_REGIONS = {'P': (p, a1), 'A1': (a1, a2), 'A2': (a2, apa), 'AppA': (apa, apb),
                  'AppB': (apb, apc), 'AppC': (apc, gl), 'GL': (gl, len(raw))}
    return E6_REGIONS


def split_subitems(loc):
    """'3.11.4.5.1(b)(ii)' -> ('3.11.4.5.1', ['(b)', '(ii)'])"""
    m = re.match(r'^([A-Z]?\.?[\d.]+?)((?:\([a-z0-9]+\))*)$', loc)
    if not m:
        return loc, []
    return m.group(1), re.findall(r'\([a-z0-9]+\)', m.group(2))


def find_subitem(raw, s, e, markers):
    """Narrow (s,e) to sub-item markers like (a), (ii) found at line starts."""
    for mk in markers:
        pat = re.compile(r'^\s*' + re.escape(mk) + r'\s')
        found = None
        for off, l in lines_with_offsets(raw, s, e):
            if pat.match(l.replace('\f', '')):
                found = off
                break
        if found is None:
            return (s, e, 'subitem %s not found at line start' % mk)
        # end at next marker of same type
        if re.match(r'^\([a-z]\)$', mk):
            nxt = re.compile(r'^\s*\([a-z]\)\s')
        elif re.match(r'^\([ivx]+\)$', mk):
            nxt = re.compile(r'^\s*\([ivx]+\)\s')
        else:
            nxt = re.compile(r'^\s*\(\d+\)\s')
        ee = e
        first = True
        for off, l in lines_with_offsets(raw, found, e):
            if first:
                first = False
                continue
            if nxt.match(l.replace('\f', '')) and not l.strip().startswith(mk):
                ee = off
                break
        s, e = found, ee
    return (s, e, '')


def loc_e6r3(raw, loc):
    R = e6_regions(raw)
    if loc.startswith('GL:'):
        term = loc[3:]
        gs, ge = R['GL']
        s = find_line(raw, r'^\s*' + re.escape(basic_norm(term)) + r'\s*:', gs, ge)
        if s is None:
            s = find_line(raw, r'^\s*' + re.escape(basic_norm(term)), gs, ge)
        if s is None:
            return None
        # end: next glossary term line at low indentation
        first = True
        for off, l in lines_with_offsets(raw, s, ge):
            if first:
                first = False
                continue
            if re.match(r'^\s{0,4}[A-Z][^:.]{2,110}:\s', basic_norm(l.replace('\f', ''))):
                return (s, off, '')
        return (s, ge, '')
    m = re.match(r'^(P|A1|A2|AppB|AppC)-?(.*)$', loc)
    reg, rest = m.group(1), m.group(2)
    rs, re_ = R[reg]
    if rest == 'Intro':
        return (rs, find_line(raw, r'^\s*B\.1\.?\s', rs, re_) or re_, '')
    key, subs = split_subitems(rest)
    r = find_numeric_section(raw, key, rs, re_)
    if r is None:
        return None
    s, e = r
    note = ''
    if subs:
        s, e, note = find_subitem(raw, s, e, subs)
    return (s, e, note)


# ------------------------------------------------------------------ generic numeric 'S' locs
def loc_numeric(raw, loc, start=0):
    key = loc[1:] if loc.startswith('S') else loc
    key = key.replace(' [verify]', '')
    r = find_numeric_section(raw, key, start)
    if r is None:
        return None
    return (r[0], r[1], '')


# ------------------------------------------------------------------ EU CTR
def loc_euctr(raw, loc):
    m = re.match(r'^Art\. (\d+)((?:\(\d+\))*)$', loc)
    art = m.group(1)
    paras = re.findall(r'\((\d+)\)', m.group(2))
    s = find_line(raw, r'^\s*Article ' + art + r'\s*$', 0)
    # skip recitals: find the article heading after 'HAVE ADOPTED THIS REGULATION'
    adopt = find_line(raw, r'HAVE ADOPTED THIS REGULATION', 0)
    s = find_line(raw, r'^\s*Article ' + art + r'\s*$', adopt)
    e = find_line(raw, r'^\s*Article ' + str(int(art) + 1) + r'\s*$', s + 10) or len(raw)
    note = ''
    if paras:
        # first level: paragraph 'n.' at line start
        p = paras[0]
        ps = find_line(raw, r'^\s*' + p + r'\.\s', s, e)
        if ps is not None:
            pe = find_line(raw, r'^\s*' + str(int(p) + 1) + r'\.\s', ps + 3, e) or e
            s, e = ps, pe
        else:
            note = 'paragraph %s. not found; ' % p
        if len(paras) > 1:
            q = paras[1]
            qs = find_line(raw, r'^\s*\(' + q + r'\)\s', s, e)
            if qs is not None:
                qe = find_line(raw, r'^\s*\(' + str(int(q) + 1) + r'\)\s', qs + 3, e) or e
                s, e = qs, qe
            else:
                note += 'point (%s) not found' % q
    return (s, e, note)


# ------------------------------------------------------------------ CFR
def loc_cfr(raw, loc):
    m = re.match(r'^21CFR(\d+\.\d+)(.*)$', loc)
    sec = m.group(1)
    s = find_line(raw, r'^§ ' + re.escape(sec) + r'\s', 0)
    if s is None:
        return None
    e = find_line(raw, r'^§ \d', s + 5) or len(raw)
    return (s, e, 'section-level passage; paragraph %s checked manually' % (m.group(2) or '-'))


# ------------------------------------------------------------------ roman (FDA)
def loc_roman(raw, loc, start=0):
    parts = loc[1:].split('.')
    s = start
    end = len(raw)
    pats = []
    for i, p in enumerate(parts):
        if re.match(r'^[IVX]+$', p):
            rx = r'^\s*(?:\d{1,4}\s+)?' + p + r'\.\s+[A-Z]'
        elif re.match(r'^[A-Z]$', p):
            rx = r'^\s*(?:\d{1,4}\s+)?' + p + r'\.\s+[A-Z]'
        else:
            rx = r'^\s*(?:\d{1,4}\s+)?' + p + r'\.\s+[A-Z]'
        pats.append(rx)
        f = find_line(raw, rx, s, end)
        if f is None:
            return (s, min(end, s + 4000), 'part %s not found' % p)
        s = f
        # end: next heading of the same type
        if re.match(r'^[IVX]+$', p):
            nrx = r'^\s*(?:\d{1,4}\s+)?[IVX]+\.\s+[A-Z]'
        elif re.match(r'^[A-Z]$', p):
            nrx = r'^\s*(?:\d{1,4}\s+)?([A-Z]\.|[IVX]+\.)\s+[A-Z]'
        else:
            nrx = r'^\s*(?:\d{1,4}\s+)?(\d+\.|[A-Z]\.|[IVX]+\.)\s+[A-Z]'
        ne = find_line(raw, nrx, s + 3, end)
        end = ne if ne else end
    return (s, end, '')


def page_range(doc, s, e):
    a = doc.page_of(s)
    b = doc.page_of(max(s, e - 1))
    return a, b
