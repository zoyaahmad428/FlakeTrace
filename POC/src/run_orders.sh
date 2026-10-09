#!/bin/sh
# Runs INSIDE the container. Executes a batch of test orders, ONE FRESH JVM PER
# ORDER so no static state leaks between orders.
#
#   /w    = subject project      /out = poc/runner/<project>
#   $1    = orders file: "<order_id><TAB><spec> <spec> ..." per line
#   $2    = per-order timeout in seconds
#
# Emits to stdout, one line per executed test:
#   <order_id><TAB>FT<TAB>idx<TAB>spec<TAB>PASS|FAIL<TAB>exc<TAB>msg<TAB>frames<TAB>ms
# plus a synthetic TIMEOUT/CRASH line when the JVM does not complete cleanly.
set -u

ORDERS="$1"
TMO="${2:-120}"
SETUP="${3:--}"
CP="/out:/w/target/classes:/w/target/test-classes:$(cat /out/ft_cp.txt)"

while IFS=bogus read -r line; do
    [ -z "$line" ] && continue
    oid=$(printf '%s' "$line" | cut -f1)
    specs=$(printf '%s' "$line" | cut -f2)

    out=$(timeout "$TMO" java -XX:+UseSerialGC -Xmx1g -cp "$CP" FtRunner -s "$SETUP" -e $specs 2>/dev/null)
    rc=$?

    if [ $rc -eq 124 ]; then
        printf '%s\tFT\t0\t-\tFAIL\tFtTimeout\tjvm exceeded %ss\t\t0\n' "$oid" "$TMO"
    elif [ -z "$out" ]; then
        printf '%s\tFT\t0\t-\tFAIL\tFtCrash\tjvm exit %s with no output\t\t0\n' "$oid" "$rc"
    else
        printf '%s\n' "$out" | sed "s/^/${oid}\t/"
    fi
done < "$ORDERS"
