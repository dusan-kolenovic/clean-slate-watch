import csv, re
csv.field_size_limit(10**9)
def load(p): return list(csv.DictReader(open(p, encoding='utf-8-sig', errors='replace')))

ANCHOR  = re.compile(r'(expung\w*|expunction|\bseal\w*|set[- ]aside|record relief|clean slate|nondisclosure)', re.I)
CONTEXT = re.compile(r'(criminal|convict\w*|arrest\w*|charge[ds]?|offense|misdemeanor|felony|court record\w*|police record\w*|criminal history|dismissal|acquitt\w*|deferred)', re.I)
VETO    = re.compile(r'(sealed bid|competitive sealed|diploma seal|seal of the Commonwealth|notary|sealed container)', re.I)
AUTO    = re.compile(r'(automat\w*|without.{0,20}petition|clean slate)', re.I)
DATE    = re.compile(r'(delayed effective date|effective date|postpon\w*|deferred until)', re.I)
CRA     = re.compile(r'(consumer report\w*|background check|screening|disseminat\w*|employer|licensing)', re.I)

def run(bp, sp, label):
    bills = {b['Bill_id']: b for b in load(bp)}
    sums = {}
    for s in load(sp): sums.setdefault(s['SUM_BILNO'].strip(), []).append(s['SUMMARY_TEXT'])
    out=[]
    for bid,b in bills.items():
        desc=b['Bill_description']; body=' '.join(sums.get(bid,[]))[:8000]; text=desc+' '+body
        if not (ANCHOR.search(text) and CONTEXT.search(text)): continue
        if VETO.search(desc) and not CONTEXT.search(desc): continue
        s=1
        if ANCHOR.search(desc) and CONTEXT.search(desc): s+=3      # signal in the title itself
        if AUTO.search(text): s+=3
        if DATE.search(text): s+=2
        if CRA.search(text):  s+=1
        out.append((s,bid,b))
    out.sort(key=lambda x:(-x[0],x[1]))
    print(f"\n### {label} — {len(bills)} bills scanned, {len(out)} candidates")
    for s,bid,b in out:
        st = f"ENACTED {b['Chapter_id']}" if b.get('Approved')=='Y' else ('VETOED' if b.get('Vetoed')=='Y' else ('PASSED' if b.get('Passed')=='Y' else 'died/pending'))
        tier = 'P1' if s>=7 else ('P2' if s>=5 else 'P3')
        print(f"  {tier} score={s:<2} {bid:8} {st:18} {b['Bill_description'][:92]}")
run('va_20261.csv','va_sum_2026.csv','Virginia 2026 Regular Session')
run('va_20251.csv','va_sum_2025.csv','Virginia 2025 Regular Session')
