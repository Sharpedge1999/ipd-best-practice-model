"""Assemble X1_results.yaml from the verifier's judgement files (work/judg_*.yaml).

For every worklist item: verdict/severity/note/correction come from the judgement file
(default: confirmed). Evidence loc/page/snippet are derived from the local text
(quote hit inside the cited passage, else best-matching sentence) unless overridden.
Also prints a page cross-check list (cited page vs page where the evidence was found).
"""
import sys
import re
import glob
import yaml
sys.path.insert(0, '/home/claude/ipd/verification/tools')
from x1lib import load_worklist, get_doc, find_quote, best_match, clean_index_of_raw
import x1_report

OUT = '/home/claude/ipd/verification/X1_results.yaml'

# hand-written evidence for items checked without usable local text (verbatim, from WebFetch)
WEB_SNIPS = {
    'R5-045': 'Conduct a "lessons learned" session.',
    'R5-046': 'We recommend that finalization occur after the last study data has been reviewed.',
    'R5-048': 'In parallel, sponsors should define appropriate risk management strategies',
    'R5-068': 'An events domain that contains protocol violations and deviations',
}
WEB_PAGES = {
    'R5-045': 'web page, closeout best-practice task list',
    'R5-046': 'web page, closeout paragraph',
    'R5-048': 'publisher HTML, section How QTLs Fit in a Quality Management System',
    'R5-068': 'mirror web page dated 03/11/2026',
}

# words that must never appear in an evidence snippet (person / company names seen in source metadata or bylines)
BLOCK = None


def load_block():
    global BLOCK
    if BLOCK is None:
        BLOCK = set()
        p = '/home/claude/ipd/verification/work/name_block.txt'
        try:
            for l in open(p, encoding='utf-8'):
                l = l.strip()
                if l:
                    BLOCK.add(l.lower())
        except FileNotFoundError:
            pass
    return BLOCK


def snippet_ok(s):
    low = s.lower()
    return not any(b in low for b in load_block())


def words(s, n=12):
    w = s.split()
    return ' '.join(w[:n])


def parse_cited(page):
    """Return dict with sets of acceptable printed and pdf page numbers."""
    res = {'printed': set(), 'pdf': set(), 'oj': set(), 'raw': page}
    if not page:
        return res
    for m in re.finditer(r'printed\s+([0-9ivx]+)(?:\s*-\s*([0-9ivx]+))?', page):
        a, b = m.group(1), m.group(2)
        if a.isdigit():
            b = int(b) if b and b.isdigit() else int(a)
            res['printed'].update(str(x) for x in range(int(a), b + 1))
        else:
            res['printed'].add(a)
            if b:
                res['printed'].add(b)
    for m in re.finditer(r'PDF\s+(\d+)(?:\s*-\s*(\d+))?', page):
        a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else a
        res['pdf'].update(range(a, b + 1))
    for m in re.finditer(r'L 158/(\d+)', page):
        res['oj'].add(m.group(1))
    for m in re.finditer(r'(?:slides?|Page)\s+(\d+)(?:\s*(?:-|,)\s*(\d+))?', page):
        a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else a
        res['printed'].update(str(x) for x in range(min(a, b), max(a, b) + 1))
    for m in re.finditer(r'(\d+)\s+(?:or\s+(\d+)\s+)?of\s+\d+', page):
        res['printed'].add(m.group(1))
        if m.group(2):
            res['printed'].add(m.group(2))
    return res


def main():
    wl = load_worklist()
    items = wl['items']
    judg = {}
    for f in sorted(glob.glob('/home/claude/ipd/verification/work/judg_*.yaml')):
        d = yaml.safe_load(open(f, encoding='utf-8'))
        judg[d['src']] = d
    results = []
    page_checks = []
    global_snips = yaml.safe_load(open('/home/claude/ipd/verification/work/evsnip_all.yaml', encoding='utf-8'))
    snip_fail = []
    for it in items:
        j = judg.get(it['src'])
        if j is None:
            raise SystemExit('no judgement file for %s' % it['src'])
        ex = (j.get('except') or {}).get(it['id'], {})
        notes = j.get('notes') or {}
        note = ex.get('note') or notes.get(it['id']) or ''
        if not ex.get('note') and notes.get('_all'):
            note = (notes['_all'] + ' ' + note).strip()
        elif ex.get('note') and notes.get('_all'):
            note = (notes['_all'] + ' ' + note).strip()
        method = (j.get('methods') or {}).get(it['id']) or j.get('method', 'local-text')
        verdict = ex.get('v', 'confirmed')
        sev = ex.get('s') if verdict != 'confirmed' else None
        ev_loc = ex.get('ev_loc') or it['loc']
        ev_page = ex.get('ev_page') or (j.get('evpage') or {}).get(it['id'])
        snip = None
        found_label = None
        if it['local_text'] and method.startswith('local-text'):
            doc = get_doc(it['local_text'], it['src'])
            q = find_quote(doc, it.get('quote'))
            L = x1_report.locate(doc, it['src'], it['loc'])
            pos = None
            if q['level'] in ('exact', 'casefold', 'squash') and q.get('hits'):
                cand = q.get('all') or q['hits']
                inside = [h for h in cand if L and L[0] <= h < L[1]]
                pos = (inside or q['hits'])[0]
                ci = clean_index_of_raw(doc, pos)
                qn = re.sub(r'\s+', ' ', it['quote']).strip()
                snip = words(doc.clean[ci:ci + len(qn) + 40], min(12, len(qn.split())))
            else:
                text = it['paraphrase'] + ' ' + (it.get('quote') or '')
                bm = []
                if L and L[1] > L[0]:
                    cs = clean_index_of_raw(doc, L[0]); ce = clean_index_of_raw(doc, L[1])
                    bm = best_match(doc, text, cs, ce, top=1)
                if not bm or bm[0][0] < 0.5:
                    bm2 = best_match(doc, text, top=1)
                    if bm2 and (not bm or bm2[0][0] > bm[0][0]):
                        bm = bm2
                if bm:
                    sc, a, b = bm[0]
                    pos = doc.raw_of_clean(a)
                    snip = words(doc.clean[a:b], 12)
            if pos is not None:
                found_label = doc.page_label(pos)
                if ev_page:
                    found_label = ev_page if re.match(r'PDF \d+ / printed', ev_page) else found_label
                else:
                    ev_page = found_label
                # page cross-check
                cited = parse_cited(it['page'])
                m = re.match(r'PDF (\d+) / printed (\S+)', found_label)
                pdfn, prn = int(m.group(1)), m.group(2)
                ok = None
                if cited['pdf']:
                    ok = pdfn in cited['pdf']
                if cited['printed']:
                    pr = prn.replace('L158/', '')
                    ok2 = pr in cited['printed']
                    ok = ok2 if ok is None else (ok and ok2) if cited['pdf'] else ok2
                if cited['oj']:
                    ok = prn.replace('L158/', '') in cited['oj']
                if ok is False:
                    page_checks.append((it['id'], it['page'], found_label, verdict))
        if it['id'] in WEB_SNIPS:
            snip = WEB_SNIPS[it['id']]
            ev_page = WEB_PAGES[it['id']]
        if (j.get('evsnip') or {}).get(it['id']):
            snip = j['evsnip'][it['id']]
        if it['id'] in global_snips:
            snip = global_snips[it['id']]
        # verify snippet is verbatim in the local text (whitespace/quote-normalised; squash fallback for column layouts)
        if snip and it['local_text'] and method.startswith('local-text'):
            from x1lib import norm_quote, squash
            dchk = get_doc(it['local_text'], it['src'])
            alt = None
            if it['id'] == 'R3-088':
                alt = get_doc('vendor/sources/EMA-E6R3/doc_13.txt', 'EMA-E6R3')
            okv = any(norm_quote(snip) in dd.clean or squash(snip) in dd.sq for dd in ([dchk] + ([alt] if alt else [])))
            if not okv:
                snip_fail.append((it['id'], snip))
            if len(snip.split()) >= 15:
                snip_fail.append((it['id'], 'TOO LONG'))
        if ev_page and 'printed None' in ev_page:
            if it['src'].startswith('21CFR'):
                ev_page = 'unpaginated (eCFR API text)'
            elif it['src'] in ('TCB-PD-TIRS',):
                ev_page = 'unpaginated (PMC HTML text)'
            elif it['src'] == 'EMA-E6R3' and it['id'] != 'R3-088':
                ev_page = 'unpaginated (EMA web page)'
            else:
                ev_page = ev_page.replace(' / printed None', ' (no printed page number)')
        if it['id'] == 'R3-088':
            ev_page = 'EMA web page (unpaginated); cover table on PDF 1 of EMA/CHMP/ICH/162879/2026'
        if snip and not snippet_ok(snip):
            snip = None
        ev = {'loc': ev_loc, 'page': ev_page or it['page']}
        if snip:
            ev['snippet'] = snip
        # quote status
        qstat = None
        if it.get('quote'):
            if it['id'] in ('R2-066', 'R2-067', 'R3-080', 'R5-058'):
                qstat = 'verbatim (multi-column table; verified by reading the column)'
            elif it['id'] == 'R3-088':
                qstat = 'verbatim on the EMA web page (doc_13), not on the cited cover'
            elif it['id'] in ('R5-046', 'R5-048'):
                qstat = 'verbatim per two WebFetch calls'
            elif it['local_text'] and method.startswith('local-text'):
                qq = find_quote(get_doc(it['local_text'], it['src']), it['quote'])
                qstat = {'exact': 'verbatim', 'casefold': 'verbatim except case', 'squash': 'verbatim except punctuation/spacing'}.get(qq['level'], 'NOT verbatim (' + qq['level'] + ')')
            else:
                qstat = 'checked via WebFetch'
        rec = {
            'id': it['id'],
            'src': it['src'],
            'verdict': verdict,
            'severity': sev,
            'evidence': ev,
            'correction': ex.get('corr'),
            'method': method,
            'quote_check': qstat,
            'note': note or None,
        }
        results.append(rec)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('# X1 blind verification results - one record per worklist item (427).\n')
        f.write('# verdicts: confirmed | loc-wrong | page-wrong | paraphrase-distorted | quote-mismatch | binding-wrong | not-found\n')
        f.write('# evidence.page = page where the verifier found the content (PDF page / printed page label from the local text).\n')
        yaml.safe_dump({'results': results}, f, allow_unicode=True, sort_keys=False, width=140)
    print('written', len(results))
    print('SNIPPET CHECK FAILURES:', snip_fail)
    print('PAGE CROSS-CHECK (cited page differs from found page):')
    for pc in page_checks:
        print('  ', pc)


if __name__ == '__main__':
    main()
