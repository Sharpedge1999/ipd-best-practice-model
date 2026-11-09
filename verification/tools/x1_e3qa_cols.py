"""De-columnise the E3 Q&A local text (pdftotext -layout table) and check phrases in the answer column.
usage: python3 -I x1_e3qa_cols.py "phrase" ["phrase2" ...]"""
import sys, re
sys.path.insert(0, '/home/claude/ipd/verification/tools')
from x1lib import basic_norm, squash
raw = open('/home/claude/ipd/vendor/sources/E3QA/doc_5.txt', encoding='utf-8').read()
pages = raw.split('\f')
ans_by_page = []
for pi, p in enumerate(pages):
    lines = p.split('\n')
    b = None
    for l in lines:
        if 'Answers' in l and 'Questions' in l:
            b = l.index('Answers')
            break
    if b is None:
        # reuse previous boundary heuristically
        b = ans_by_page[-1][1] if ans_by_page and ans_by_page[-1][1] else None
    right = []
    left = []
    for l in lines:
        if b:
            # find a split point: nearest run of >=2 spaces at or before b+2
            cut = b - 2
            m = None
            for mm in re.finditer(r'\s{2,}', l):
                if mm.end() >= b - 8 and mm.start() <= b + 2:
                    m = mm
            if m:
                cut = m.end()
            right.append(l[cut:].strip())
            left.append(l[:cut].strip())
        else:
            right.append(l.strip())
    ans_by_page.append((' '.join(x for x in right if x), b, ' '.join(x for x in left if x)))
for ph in sys.argv[1:]:
    q = squash(ph)
    found = []
    for i, (a, b, lft) in enumerate(ans_by_page):
        if q in squash(a):
            found.append(('answer col', i + 1))
        if q in squash(lft):
            found.append(('question col', i + 1))
    print(repr(ph[:60]), '->', found or 'NOT FOUND in single column')
if len(sys.argv) == 1:
    for i, (a, b, l) in enumerate(ans_by_page):
        print('#### PDF', i + 1, 'boundary', b)
        print('Q:', re.sub(r'\s+', ' ', basic_norm(l))[:3000])
        print('A:', re.sub(r'\s+', ' ', basic_norm(a))[:3000])
