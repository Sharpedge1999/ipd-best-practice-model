#!/usr/bin/env bash
# Download official source documents into one directory per source key (untrusted data),
# extract plain text, and log status. Usage: tools/fetch_sources.sh <urls.tsv>
# urls.tsv lines: KEY<TAB>URL
set -u
BASE=/home/claude/ipd/vendor/sources
LOG=$BASE/fetch_log.tsv
mkdir -p "$BASE"
printf "key\turl\thttp\tbytes\tsha256\ttext_chars\tfile\n" > "$LOG"
n=0
while IFS=$'\t' read -r key url; do
  [ -z "$key" ] && continue
  n=$((n+1))
  dir="$BASE/$key"; mkdir -p "$dir"
  out="$dir/doc_$n.bin"
  code=$(curl -sSL --max-time 90 -A "Mozilla/5.0 (research; document retrieval)" -o "$out" -w "%{http_code}" "$url" 2>/dev/null || echo "ERR")
  bytes=$(stat -c %s "$out" 2>/dev/null || echo 0)
  sha=$(sha256sum "$out" 2>/dev/null | cut -d' ' -f1)
  kind=$(file -b "$out" | cut -c1-12)
  chars=0
  if [[ "$kind" == PDF* ]]; then
    mv "$out" "$dir/doc_$n.pdf"; out="$dir/doc_$n.pdf"
    pdftotext -layout "$out" "$dir/doc_$n.txt" 2>/dev/null && chars=$(wc -c < "$dir/doc_$n.txt")
  elif grep -qi "<html" "$out" 2>/dev/null; then
    mv "$out" "$dir/doc_$n.html"; out="$dir/doc_$n.html"
    python3 -I -c "import sys,lxml.html as h; t=h.parse(sys.argv[1]).getroot(); [e.drop_tree() for e in t.xpath('//script|//style')]; open(sys.argv[2],'w').write('\n'.join(l.strip() for l in t.text_content().splitlines() if l.strip()))" "$out" "$dir/doc_$n.txt" 2>/dev/null && chars=$(wc -c < "$dir/doc_$n.txt")
  fi
  printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$key" "$url" "$code" "$bytes" "$sha" "$chars" "$(basename "$out")" >> "$LOG"
done < "$1"
column -t -s $'\t' "$LOG" | cut -c1-220
