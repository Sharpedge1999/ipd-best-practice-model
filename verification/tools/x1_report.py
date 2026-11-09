"""Print review blocks for worklist items (by src or ids) for manual judgement.

usage: python3 -I x1_report.py SRC [--ids id1,id2] [--width N] > out.txt
"""
import sys
import re
import json
sys.path.insert(0, '/home/claude/ipd/verification/tools')
from x1lib import load_worklist, get_doc, find_quote, best_match, clean_index_of_raw, basic_norm
import x1loc

ROMAN_SRC = {'FDA-PD24', 'FDA-RBM13', 'FDA-E6R3', 'FDA-ESTUDY'}


def locate(doc, src, loc):
    raw = doc.raw
    try:
        if src == 'E6R3':
            return x1loc.loc_e6r3(raw, loc)
        if src == 'EUCTR':
            return x1loc.loc_euctr(raw, loc)
        if src.startswith('21CFR'):
            return x1loc.loc_cfr(raw, loc)
        if src in ROMAN_SRC and re.match(r'^S[IVX]+(\.|$)', loc):
            return x1loc.loc_roman(raw, loc)
        if re.match(r'^S(A\.)?\d+(\.\d+)*( \[verify\])?$', loc):
            return x1loc.loc_numeric(raw, loc)
    except Exception as ex:  # noqa
        return (0, 0, 'locator error %r' % ex)
    return None


def excerpt(doc, cs, ce, width):
    t = doc.clean[cs:ce]
    if len(t) > width:
        t = t[:width] + ' [...]'
    return t


def main():
    args = sys.argv[1:]
    src = args[0]
    ids = None
    width = 900
    if '--ids' in args:
        ids = set(args[args.index('--ids') + 1].split(','))
    if '--width' in args:
        width = int(args[args.index('--width') + 1])
    wl = load_worklist()
    items = [i for i in wl['items'] if (src == 'ALL' or i['src'] == src) and (ids is None or i['id'] in ids)]
    auto = {}
    shown = set()
    for it in items:
        lt = it['local_text']
        print('=' * 100)
        print('%s | %s | loc=%s | page=%s' % (it['id'], it['src'], it['loc'], it['page']))
        print('PARA: ' + it['paraphrase'])
        if it.get('quote'):
            print('QUOTE: ' + it['quote'])
        if not lt:
            print('NO LOCAL TEXT')
            auto[it['id']] = {'local': False}
            continue
        doc = get_doc(lt, it['src'])
        rec = {'local': True}
        q = find_quote(doc, it.get('quote'))
        if q['level'] != 'n/a':
            pages = sorted(set(doc.page_label(h) for h in q['hits']))
            print('QCHECK: %s %s %s' % (q['level'], pages, ('ratio=%s' % q['ratio']) if q['ratio'] else ''))
            if q['nearest'] and q['level'] != 'exact':
                print('  NEAREST: ' + q['nearest'][:400])
            rec['quote_level'] = q['level']
            rec['quote_pages'] = pages
        L = locate(doc, it['src'], it['loc'])
        if L is None:
            print('LOC: not located automatically')
            rec['loc_found'] = False
            bm = best_match(doc, it['paraphrase'] + ' ' + (it.get('quote') or ''), top=2)
            for sc, a, b in bm:
                ra = doc.raw_of_clean(a)
                print('  DOCBEST %.2f @ %s: %s' % (sc, doc.page_label(ra), doc.clean[a:b][:500]))
        else:
            s, e, note = L
            cs = clean_index_of_raw(doc, s)
            ce = clean_index_of_raw(doc, e)
            pa, pb = x1loc.page_range(doc, s, e)
            print('LOC: found %s .. %s (%d chars) %s' % (doc.page_label(s), doc.page_label(max(s, e - 1)), ce - cs, note))
            rec['loc_found'] = True
            rec['loc_pages'] = [doc.page_label(s), doc.page_label(max(s, e - 1))]
            if q.get('hits'):
                inside = all(s <= h < e for h in q['hits']) or any(s <= h < e for h in q.get('all', []))
                if q.get('count', 1) > 1:
                    print('  quote occurrences: %d at %s' % (q['count'], sorted(set(doc.page_label(h) for h in q['all']))))
                print('  quote inside loc passage: %s' % inside)
                rec['quote_in_loc'] = inside
            bm = best_match(doc, it['paraphrase'] + ' ' + (it.get('quote') or ''), cs, ce, top=1)
            bmd = best_match(doc, it['paraphrase'] + ' ' + (it.get('quote') or ''), top=1)
            key = (it['src'], it['loc'])
            if ce - cs <= width:
                if key in shown:
                    print('  PASSAGE: (as above)')
                else:
                    print('  PASSAGE: ' + doc.clean[cs:ce])
            else:
                if bm:
                    sc, a, b = bm[0]
                    a0 = max(cs, a - 250)
                    b0 = min(ce, max(b, a + width - 250))
                    print('  PASSAGE-HEAD: ' + doc.clean[cs:cs + 160])
                    print('  WINDOW %.2f @ %s: %s' % (sc, doc.page_label(doc.raw_of_clean(a)), doc.clean[a0:b0]))
            if bmd:
                sc, a, b = bmd[0]
                ra = doc.raw_of_clean(a)
                if not (s <= ra < e) and (not bm or sc > bm[0][0] + 0.1):
                    print('  DOCBEST-OUTSIDE %.2f @ %s: %s' % (sc, doc.page_label(ra), doc.clean[a:b][:400]))
            shown.add(key)
        auto[it['id']] = rec
    with open('/home/claude/ipd/verification/work/auto_%s.json' % src, 'w') as f:
        json.dump(auto, f, indent=1)


if __name__ == '__main__':
    main()
