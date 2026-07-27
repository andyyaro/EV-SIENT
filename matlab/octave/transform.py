#!/usr/bin/env python3
"""Mechanical MATLAB->Octave source transformation for the FCF matlab layer.
Rules are token-level and reversible-by-inspection. Emits a per-rule audit log."""
import os,re,sys,json,collections

AUDIT=collections.Counter()
AUDIT_LINES=collections.defaultdict(list)

def tokenize(src):
    """Split source into (kind, text) tokens: 'str' (dq literal), 'sq' (sq literal),
    'cmt' (comment to EOL), 'code'."""
    toks=[];i=0;n=len(src);buf=[]
    def flush():
        if buf: toks.append(('code',''.join(buf))); buf.clear()
    while i<n:
        c=src[i]
        if c=='"':
            j=i+1
            while j<n:
                if src[j]=='"':
                    if j+1<n and src[j+1]=='"': j+=2; continue
                    break
                j+=1
            flush(); toks.append(('str',src[i:j+1])); i=j+1; continue
        if c=="'":
            # transpose vs literal
            k=len(''.join(buf))-1
            prev=''.join(buf)[-1] if buf and ''.join(buf) else ''
            if prev and (prev.isalnum() or prev in ")]}._'"):
                buf.append(c); i+=1; continue
            j=i+1
            while j<n:
                if src[j]=="'":
                    if j+1<n and src[j+1]=="'": j+=2; continue
                    break
                if src[j]=='\n': break
                j+=1
            flush(); toks.append(('sq',src[i:j+1])); i=j+1; continue
        if c=='%':
            j=src.find('\n',i); j=n if j<0 else j
            flush(); toks.append(('cmt',src[i:j])); i=j; continue
        buf.append(c); i+=1
    flush()
    return toks

def detok(toks): return ''.join(t for _,t in toks)

def lit_value(tok):
    return tok[1:-1].replace('""','"')

def mk_lit(v):
    return '"'+v.replace('"','""')+'"'

def strip_continuations(toks):
    """Join '...' continuations inside CODE tokens so + chains are contiguous.
    Returns new toks with a marker recording removed newlines (we re-emit \n later
    only to preserve line count in the audit; simpler: we keep them)."""
    return toks

def rule_fold_plus(toks, fname):
    """R1: fold '+' chains of adjacent dq literals into one literal (constant folding).
       R2: '+' chains mixing literals and expressions -> cc(...)."""
    out=[]; i=0
    while i<len(toks):
        k,t=toks[i]
        if k!='str': out.append(toks[i]); i+=1; continue
        # try to extend a chain: str ( ws/cont '+' ws/cont str )+
        chain=[toks[i]]; j=i+1; consumed=i
        while j<len(toks):
            # code token that is only whitespace/continuation/newline then '+'
            if toks[j][0]=='cmt':
                j+=1; continue
            if toks[j][0]!='code': break
            c=toks[j][1]
            m=re.fullmatch(r'[\s]*\.\.\.[\s]*\+[\s]*|[\s]*\+[\s]*\.\.\.[\s]*|[\s]*\+[\s]*|[\s]*\.\.\.[\s]*', c)
            if not m: break
            if '+' not in c:
                # bare continuation; look ahead for '+'
                j+=1; continue
            # next non-cmt token must be str
            k2=j+1
            while k2<len(toks) and toks[k2][0]=='cmt': k2+=1
            if k2<len(toks) and toks[k2][0]=='str':
                chain.append(toks[k2]); consumed=k2; j=k2+1; continue
            break
        if len(chain)>1:
            folded=mk_lit(''.join(lit_value(c[1]) for c in chain))
            out.append(('str',folded))
            AUDIT['R1_fold_literal_plus']+=len(chain)-1
            AUDIT_LINES['R1_fold_literal_plus'].append(fname)
            i=consumed+1; continue
        out.append(toks[i]); i+=1
    return out

def rule_bracket_list(src, fname):
    """R3: [ "a", "b", ... ] literal LIST -> { "a", "b", ... }.
       Only when every top-level element is a dq literal and there are >=2,
       or exactly 1 element used where MATLAB would make a 1x1 string array."""
    out=[];i=0;n=len(src)
    while i<n:
        if src[i]!='[':
            out.append(src[i]); i+=1; continue
        # find matching ]
        d=0;j=i;instr=None
        while j<n:
            c=src[j]
            if instr:
                if c==instr:
                    if j+1<n and src[j+1]==instr: j+=2; continue
                    instr=None
                j+=1; continue
            if c in '"\'':
                if c=="'" and j>i and (src[j-1].isalnum() or src[j-1] in ")]}._"): j+=1; continue
                instr=c; j+=1; continue
            if c=='%':
                k=src.find('\n',j); j=n if k<0 else k; continue
            if c in '[({': d+=1
            elif c in '])}':
                d-=1
                if d==0: break
            j+=1
        if j>=n: out.append(src[i]); i+=1; continue
        inner=src[i+1:j]
        # strip comments+continuations for the element test
        test=re.sub(r'%[^\n]*','',inner)
        test=test.replace('...','').replace('\n',' ')
        parts=[p.strip() for p in split_top(test)]
        if len(parts)>=2 and all(re.fullmatch(r'"(?:[^"]|"")*"',p) for p in parts):
            out.append('{'+inner+'}')
            AUDIT['R3_bracket_list_to_cellstr']+=1
            AUDIT_LINES['R3_bracket_list_to_cellstr'].append(fname)
            i=j+1; continue
        out.append(src[i]); i+=1
    return ''.join(out)

def split_top(s):
    parts=[];d=0;cur=[];instr=None;i=0
    while i<len(s):
        c=s[i]
        if instr:
            cur.append(c)
            if c==instr:
                if i+1<len(s) and s[i+1]==instr: cur.append(s[i+1]); i+=2; continue
                instr=None
            i+=1; continue
        if c in '"\'': instr=c; cur.append(c); i+=1; continue
        if c in '[({': d+=1
        elif c in '])}': d-=1
        if c==',' and d==0: parts.append(''.join(cur)); cur=[]; i+=1; continue
        cur.append(c); i+=1
    parts.append(''.join(cur))
    return [p for p in parts if p.strip()!='']

def rule_str_eq(src, fname):
    """R11: `EXPR == "lit"` / `EXPR ~= "lit"` -> fcf_eq(EXPR, "lit") (negated)."""
    toks=tokenize(src); out=[]; i=0
    while i<len(toks):
        k,t=toks[i]
        if k=='code' and i+1<len(toks) and toks[i+1][0]=='str':
            m=re.search(r'([A-Za-z_][\w.]*(?:\([^()]*\))?)\s*(==|~=)\s*$', t)
            if m:
                neg = '~' if m.group(2)=='~=' else ''
                out.append(('code', t[:m.start()] + '%sfcf_eq(%s, %s)' % (neg, m.group(1), toks[i+1][1])))
                AUDIT['R11_string_eq']+=1; AUDIT_LINES['R11_string_eq'].append(fname)
                i+=2; continue
        if k=='str' and i+1<len(toks) and toks[i+1][0]=='code':
            m=re.match(r'^\s*(==|~=)\s*([A-Za-z_][\w.]*)', toks[i+1][1])
            if m:
                neg = '~' if m.group(1)=='~=' else ''
                out.append(('code','%sfcf_eq(%s, %s)' % (neg, t, m.group(2))))
                toks[i+1]=('code', toks[i+1][1][m.end():])
                AUDIT['R11_string_eq']+=1; AUDIT_LINES['R11_string_eq'].append(fname)
                i+=1; continue
        out.append(toks[i]); i+=1
    return detok(out)

def rule_cat_plus(src, fname):
    """R2: remaining '+' with a dq-literal operand -> fcf_cat(a, b)."""
    toks=tokenize(src); out=[]; i=0
    while i<len(toks):
        k,t=toks[i]
        if k=='str' and i+1<len(toks) and toks[i+1][0]=='code':
            m=re.match(r'^(\s*)\+(\s*)([A-Za-z_]\w*)', toks[i+1][1])
            if m:
                rest=toks[i+1][1][m.end():]
                out.append(('code', 'fcf_cat(%s, %s)' % (t, m.group(3))))
                toks[i+1]=('code', rest)
                AUDIT['R2_cat_literal_plus_expr']+=1; AUDIT_LINES['R2_cat_literal_plus_expr'].append(fname)
                i+=1; continue
        if k=='code':
            m=re.search(r'([A-Za-z_][\w.]*)\s*\+\s*$', t)
            if m and i+1<len(toks) and toks[i+1][0]=='str':
                out.append(('code', t[:m.start()] + 'fcf_cat(%s, %s)' % (m.group(1), toks[i+1][1])))
                AUDIT['R2_cat_literal_plus_expr']+=1; AUDIT_LINES['R2_cat_literal_plus_expr'].append(fname)
                i+=2; continue
        out.append(toks[i]); i+=1
    return detok(out)

SIMPLE_SUBS=[
 (r'\bstring\.empty\b', '{}', 'R4_string_empty'),
 (r'\bstruct\.empty\b', 'struct([])', 'R4_struct_empty'),
 (r'(?<![\w.])string\s*\(', 'fcf_str(', 'R5_string_call'),
 (r'(?<![\w.])strings\s*\(', 'fcf_strings(', 'R6_strings_call'),
 (r'(?<![\w.])readtable\s*\(', 'fcf_readtable(', 'R8_table_io'),
 (r'(?<![\w.])writetable\s*\(', 'fcf_writetable(', 'R8_table_io'),
 (r'(?<![\w.])detectImportOptions\s*\(', 'fcf_detectImportOptions(', 'R8_table_io'),
 (r'(?<![\w.])setvartype\s*\(', 'fcf_setvartype(', 'R8_table_io'),
 (r'(?<![\w.])datetime\s*\(', 'fcf_datetime(', 'R9_datetime'),
 (r'(?<![\w.])ismissing\s*\(', 'fcf_ismissing(', 'R10_missing_fns'),
 (r'(?<![\w.])strlength\s*\(', 'fcf_strlength(', 'R10_missing_fns'),
 (r'(?<![\w.])contains\s*\(', 'fcf_contains(', 'R10_missing_fns'),
 (r'(?<![\w.])strjoin\s*\(', 'fcf_strjoin(', 'R10_missing_fns'),
 (r'(?<![\w.])timeseries\s*\(', 'fcf_timeseries(', 'R10_missing_fns'),
 (r'(?<![\w.\'"])struct\s*\(', 'fcf_struct(', 'R12_struct_cell_shape'),
 (r'(?<![\w.])localSha256\s*\(', 'fcf_sha256(', 'R13_java_sha256'),
]

def transform(path, rel):
    src=open(path,encoding='utf-8').read()
    toks=tokenize(src)
    toks=rule_fold_plus(toks, rel)
    src=detok(toks)
    src=rule_bracket_list(src, rel)
    src=rule_cat_plus(src, rel)
    src=rule_str_eq(src, rel)
    src2,c=re.subn(r'version\s*\(\s*"-release"\s*\)','fcf_release()',src)
    if c: AUDIT['R7_version_release']+=c; AUDIT_LINES['R7_version_release'].append(rel); src=src2
    # simple subs, but never inside literals/comments
    toks=tokenize(src); out=[]
    for k,t in toks:
        if k=='code':
            for rx,rep,name in SIMPLE_SUBS:
                t2,cnt=re.subn(rx,rep,t)
                if cnt: AUDIT[name]+=cnt; AUDIT_LINES[name].append(rel); t=t2
        out.append((k,t))
    src=detok(out)
    # R13b: a rewritten call must not also rename the LOCAL definition, or the
    # dead local shadows the shim.
    src2,c=re.subn(r'function\s+(\w+)\s*=\s*fcf_sha256\s*\(', r'function \1 = localSha256_superseded(', src)
    if c: AUDIT['R13b_unshadow_local_def']+=c; AUDIT_LINES['R13b_unshadow_local_def'].append(rel); src=src2
    return src

if __name__=='__main__':
    ROOT=sys.argv[1]; DEST=sys.argv[2]
    for d in ('src','tests'):
        os.makedirs(os.path.join(DEST,d),exist_ok=True)
        for f in sorted(os.listdir(os.path.join(ROOT,d))):
            if not f.endswith('.m'): continue
            rel=f'{d}/{f}'
            open(os.path.join(DEST,rel),'w',encoding='utf-8').write(transform(os.path.join(ROOT,rel),rel))
    EXPECTED=['R1_fold_literal_plus','R2_cat_literal_plus_expr','R3_bracket_list_to_cellstr',
              'R4_string_empty','R4_struct_empty','R5_string_call','R6_strings_call',
              'R7_version_release','R8_table_io','R9_datetime','R10_missing_fns',
              'R11_string_eq','R12_struct_cell_shape','R13_java_sha256','R13b_unshadow_local_def']
    print("=== TRANSFORM AUDIT ===")
    dead=[r for r in EXPECTED if AUDIT.get(r,0)==0]
    if dead: print("!! RULES THAT FIRED ZERO TIMES (treat as FAILURE):", dead)
    for k,v in sorted(AUDIT.items()):
        files=collections.Counter(AUDIT_LINES[k])
        print(f"{k:34s} {v:4d}   files: {dict(files)}")
