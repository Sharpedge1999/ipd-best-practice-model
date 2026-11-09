"""usage: python3 -I x1_where.py <local_text> <src> "phrase" [context_chars]
Print every occurrence (clean-text match, then squash match) of phrase with page labels."""
import sys, re
sys.path.insert(0, '/home/claude/ipd/verification/tools')
from x1lib import get_doc, norm_quote, squash
path, src, phrase = sys.argv[1], sys.argv[2], sys.argv[3]
ctx = int(sys.argv[4]) if len(sys.argv) > 4 else 200
doc = get_doc(path, src)
q = norm_quote(phrase)
hits = [m.start() for m in re.finditer(re.escape(q), doc.clean)]
mode = 'exact'
if not hits:
    hits = [m.start() for m in re.finditer(re.escape(q.lower()), doc.clean.lower())]
    mode = 'casefold'
if not hits:
    sq = squash(phrase)
    hits = [doc.sqmap[m.start()] for m in re.finditer(re.escape(sq), doc.sq)]
    mode = 'squash'
print('%d hits (%s)' % (len(hits), mode))
for h in hits[:12]:
    r = doc.raw_of_clean(h)
    print('--', doc.page_label(r), ':', doc.clean[max(0, h - ctx // 2): h + len(q) + ctx])
