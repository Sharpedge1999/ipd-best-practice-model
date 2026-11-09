"""Print margin-numbered lines of a line-numbered draft guidance.
usage: python3 -I x1_lines.py <local_text> a-b [c-d ...]"""
import sys, re
raw = open('/home/claude/ipd/' + sys.argv[1], encoding='utf-8').read()
pages = raw.split('\f')
lines = {}
for pi, p in enumerate(pages):
    # printed page = last lone number on page
    pl = [l for l in p.split('\n') if l.strip()]
    printed = None
    for l in reversed(pl[-3:]):
        m = re.match(r'^\s*(\d{1,3})\s*$', l)
        if m:
            printed = m.group(1); break
    cur = None
    for l in p.split('\n'):
        m = re.match(r'^\s*(\d{1,4})(\s{2,}(.*))?$', l)
        if m and int(m.group(1)) < 2000 and (m.group(3) is not None or l.strip() == m.group(1)) and not re.match(r'^\s*\d{1,3}\s*$', l) or (m and m.group(3)):
            n = int(m.group(1))
            lines[n] = (m.group(3) or '', pi + 1, printed)
            cur = n
        elif cur is not None and l.strip() and not re.match(r'^\s*\d{1,3}\s*$', l):
            # footnote / unnumbered text: attach marker
            lines.setdefault(('fn', pi + 1), []).append(l.strip()) if False else None
for rg in sys.argv[2:]:
    a, b = [int(x) for x in rg.split('-')]
    print('== lines %d-%d' % (a, b))
    for n in range(a, b + 1):
        if n in lines:
            t, pdf, pr = lines[n]
            print('%4d [PDF %s / p.%s] %s' % (n, pdf, pr, t))
