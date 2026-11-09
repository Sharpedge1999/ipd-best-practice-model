"""X1 verification helper library (blind verification of worklist items).

Loads the worklist and local source texts, normalises text, maps offsets to
PDF / printed pages, checks quotes verbatim and locates cited sections.
Semantic judgement of paraphrases is NOT done here - it is done by the
verifier reading the located passages.

Run with: python3 -I <script>  (scripts add this folder to sys.path explicitly)
"""
import re
import unicodedata
import difflib
import yaml

BASE = '/home/claude/ipd/'
WORKLIST = BASE + 'synthesis/verification_worklist.yaml'

# documents with margin line numbers (draft FDA guidances)
LINE_NUMBERED = {'FDA-PD24', 'FDA-ESTUDY', 'FDA-E6R3-A2'}

QUOTE_MAP = {
    '‘': "'", '’': "'", '‚': "'", '‛': "'", '′': "'",
    '“': '"', '”': '"', '„': '"', '″': '"',
    '–': '-', '—': '-', '‐': '-', '‑': '-', '‒': '-', '−': '-',
    ' ': ' ', '­': '', '•': ' ', '': ' ', '▪': ' ', '': ' ',
    'â\u0080\u0099': "'",
}


def load_worklist():
    with open(WORKLIST, encoding='utf-8') as f:
        d = yaml.safe_load(f)
    return d


def basic_norm(s):
    s = unicodedata.normalize('NFKC', s)
    for k, v in QUOTE_MAP.items():
        s = s.replace(k, v)
    return s


HEADER_PATTERNS = [
    r'^\s*ICH E6\(R3\) Guideline\s*$',
    r'^\s*ICH E8\(R1\) Guideline\s*$',
    r'^\s*ICH E9\(R1\) Guideline\s*$',
    r'^\s*Structure and Content of Clinical Study Reports\s*$',
    r'^\s*STRUCTURE AND CONTENT OF CLINICAL STUDY REPORTS\s*$',
    r'^\s*Statistical Principles for Clinical Trials\s*$',
    r'^\s*Contains Nonbinding Recommendations\s*$',
    r'^\s*Draft\s*[-—–]\s*Not for Implementation\s*$',
    r'^\s*Last Update\s*:.*$',
    r'^\s*E3 Q&As \(R1\)\s*$',
    r'^\s*EMA/698382/2021\s+Page \d+/\d+\s*$',
    r'^\s*Guideline for the notification of serious breaches of Regulation \(EU\) No 536/2014 or\s*$',
    r'^\s*the clinical trial protocol\s*$',
    r'^\s*L 158/\d+\s+EN\s+Official Journal of the European Union.*$',
    r'^\s*\d+\.\d+\.\d{4}\s+EN\s+Official Journal of the European Union\s+L 158/\d+\s*$',
    r'^\s*[ivxlc]+\s*$',
    r'^\s*\d{1,3}\s*$',
    r'^\s*Classified as public by the European Medicines Agency\s*$',
    r'^\s*\d+\s+Clinical Trials Information System\s*$',
]
HEADER_RE = [re.compile(p) for p in HEADER_PATTERNS]


class Doc:
    def __init__(self, path, src=None):
        self.path = path
        self.src = src
        with open(BASE + path, encoding='utf-8', errors='replace') as f:
            self.raw = f.read()
        self.pages = self.raw.split('\f')
        # page start offsets in raw
        self.page_starts = []
        off = 0
        for p in self.pages:
            self.page_starts.append(off)
            off += len(p) + 1
        self.printed = [self._printed_label(p) for p in self.pages]
        self._build_clean()

    @staticmethod
    def _printed_label(p):
        lines = [l for l in p.split('\n') if l.strip()]
        if not lines:
            return None
        cand = lines[-4:] + lines[:3]
        for l in cand:
            m = re.search(r'Page\s+(\d+)\s*/\s*\d+', l)
            if m:
                return m.group(1)
            m = re.search(r'L 158/(\d+)', l)
            if m:
                return 'L158/' + m.group(1)
            m = re.match(r'^\s*(\d{1,3}) of \d+\s', l)
            if m:
                return m.group(1)
        for l in reversed(lines[-3:]):
            m = re.match(r'^\s*(\d{1,3}|[ivxlc]{1,6})\s*$', l)
            if m:
                return m.group(1)
            m = re.match(r'^\s*(\d{1,3})\s+Clinical Trials Information System', l)
            if m:
                return m.group(1)
        return None

    def page_of(self, raw_off):
        # PDF page number (1-based)
        lo, hi = 0, len(self.page_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.page_starts[mid] <= raw_off:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    def page_label(self, raw_off):
        p = self.page_of(raw_off)
        return 'PDF %d / printed %s' % (p, self.printed[p - 1])

    def _build_clean(self):
        """Clean text: headers/footers dropped, margin line numbers stripped,
        whitespace collapsed; keep map clean index -> raw offset."""
        out = []
        cmap = []
        off = 0
        for line in self.raw.split('\n'):
            raw_line = line
            line_start = off
            off += len(raw_line) + 1
            l = raw_line.replace('\f', '')
            if any(r.match(basic_norm(l)) for r in HEADER_RE):
                continue
            lead = 0
            if self.src in LINE_NUMBERED:
                m = re.match(r'^\s*\d{1,4}(\s{2,}|\s*$)', l)
                if m:
                    lead = m.end()
            seg = l[lead:]
            base = line_start + lead + (1 if raw_line.startswith('\f') else 0)
            for i, ch in enumerate(seg):
                c = basic_norm(ch)
                for cc in c:
                    out.append(cc)
                    cmap.append(base + i)
            out.append(' ')
            cmap.append(base + len(seg))
        # collapse whitespace
        s2 = []
        m2 = []
        prev_space = True
        for ch, m in zip(out, cmap):
            if ch.isspace():
                if prev_space:
                    continue
                s2.append(' ')
                m2.append(m)
                prev_space = True
            else:
                s2.append(ch)
                m2.append(m)
                prev_space = False
        self.clean = ''.join(s2)
        self.cmap = m2
        # squashed alnum-lowercase
        sq = []
        sqm = []
        for i, ch in enumerate(self.clean):
            if ch.isalnum():
                sq.append(ch.lower())
                sqm.append(i)
        self.sq = ''.join(sq)
        self.sqmap = sqm

    def raw_of_clean(self, ci):
        ci = max(0, min(ci, len(self.cmap) - 1))
        return self.cmap[ci]


def norm_quote(q):
    q = basic_norm(q)
    q = re.sub(r'\s+', ' ', q).strip()
    return q


def squash(q):
    return ''.join(ch.lower() for ch in basic_norm(q) if ch.isalnum())


def find_quote(doc, quote):
    """Return dict: level exact|squash|dehyphen|fuzzy|none, positions (raw), nearest text."""
    res = {'level': 'none', 'hits': [], 'nearest': None, 'ratio': None}
    if not quote:
        res['level'] = 'n/a'
        return res
    q = norm_quote(quote)
    # strip leading/trailing ellipsis markers
    q2 = re.sub(r'^(\.\.\.|…)\s*|\s*(\.\.\.|…)$', '', q)
    parts = [p.strip() for p in re.split(r'\s*(?:\.\.\.|…|\[\.\.\.\])\s*', q2) if p.strip()]
    if not parts:
        parts = [q2]
    # exact clean match (all parts, in order)
    def find_parts(hay, ps, fold=False):
        pos = []
        start = 0
        h = hay.lower() if fold else hay
        for p in ps:
            pp = p.lower() if fold else p
            i = h.find(pp, start)
            if i < 0:
                i = h.find(pp)
                if i < 0:
                    return None
            pos.append(i)
            start = i + len(pp)
        return pos
    pos = find_parts(doc.clean, parts)
    if pos is not None:
        res['level'] = 'exact'
        res['hits'] = [doc.raw_of_clean(p) for p in pos]
        # all occurrences of the longest part
        lp = max(parts, key=len)
        allp = [m.start() for m in re.finditer(re.escape(lp), doc.clean)]
        res['all'] = [doc.raw_of_clean(p) for p in allp]
        res['count'] = len(allp)
        return res
    pos = find_parts(doc.clean, parts, fold=True)
    if pos is not None:
        res['level'] = 'casefold'
        res['hits'] = [doc.raw_of_clean(p) for p in pos]
        return res
    sparts = [squash(p) for p in parts]
    pos = find_parts(doc.sq, sparts)
    if pos is not None:
        res['level'] = 'squash'
        res['hits'] = [doc.raw_of_clean(doc.sqmap[p]) for p in pos]
        # show the clean text at that location for manual comparison
        c0 = doc.sqmap[pos[0]]
        c1 = doc.sqmap[min(pos[0] + len(sparts[0]) - 1, len(doc.sqmap) - 1)]
        res['nearest'] = doc.clean[c0:c1 + 1]
        return res
    # fuzzy: locate best window for longest part
    p0 = max(parts, key=len)
    sp = squash(p0)
    best = None
    if len(sp) >= 12:
        # anchor search using 12-char shingles
        L = len(sp)
        anchors = {}
        step = max(1, L // 10)
        for k in range(0, max(1, L - 12), step):
            sh = sp[k:k + 12]
            i = doc.sq.find(sh)
            while i >= 0:
                anchors.setdefault(i - k, 0)
                anchors[i - k] += 1
                i = doc.sq.find(sh, i + 1)
                if len(anchors) > 500:
                    break
        for a, cnt in sorted(anchors.items(), key=lambda x: -x[1])[:20]:
            a0 = max(0, a)
            win = doc.sq[a0:a0 + L + 20]
            r = difflib.SequenceMatcher(None, sp, win, autojunk=False).ratio()
            if best is None or r > best[0]:
                best = (r, a0)
    if best:
        r, a0 = best
        c0 = doc.sqmap[a0]
        c1 = doc.sqmap[min(a0 + len(sp) + 10, len(doc.sqmap) - 1)]
        res['level'] = 'fuzzy'
        res['ratio'] = round(r, 3)
        res['hits'] = [doc.raw_of_clean(c0)]
        res['nearest'] = doc.clean[c0:c1 + 1]
    return res


STOP = set('''a an the of to and or in on for by with be is are was were should shall must may can
that this these those it its as at from not no any all each which who whom their there such than
into if when where whether other also has have had been being per under within''' .split())


def tokens(s):
    return [w for w in re.findall(r'[a-z0-9]+', basic_norm(s).lower()) if w not in STOP and len(w) > 1]


def sentences_with_offsets(doc, c0, c1):
    """Split clean text [c0,c1) into sentence-ish chunks; return (cstart, cend, text)."""
    seg = doc.clean[c0:c1]
    out = []
    start = 0
    for m in re.finditer(r'(?<=[.;:])\s+(?=[A-Z(•\-0-9])', seg):
        out.append((c0 + start, c0 + m.start(), seg[start:m.start()]))
        start = m.end()
    out.append((c0 + start, c1, seg[start:]))
    return out


def best_match(doc, text, c0=0, c1=None, top=2):
    """Token-overlap ranking of sentences in clean range for paraphrase text."""
    if c1 is None:
        c1 = len(doc.clean)
    qt = set(tokens(text))
    if not qt:
        return []
    sents = sentences_with_offsets(doc, c0, c1)
    scored = []
    for i, (a, b, s) in enumerate(sents):
        # use window of 2 sentences
        st = set(tokens(s))
        if i + 1 < len(sents):
            st2 = st | set(tokens(sents[i + 1][2]))
        else:
            st2 = st
        sc = len(qt & st2) / max(1, len(qt))
        scored.append((sc, a, b if i + 1 >= len(sents) else sents[i + 1][1]))
    scored.sort(key=lambda x: -x[0])
    return scored[:top]


def clean_index_of_raw(doc, raw_off):
    # binary search in cmap
    lo, hi = 0, len(doc.cmap) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if doc.cmap[mid] < raw_off:
            lo = mid + 1
        else:
            hi = mid
    return lo


_DOCS = {}


def get_doc(path, src):
    k = (path, src)
    if k not in _DOCS:
        _DOCS[k] = Doc(path, src)
    return _DOCS[k]
