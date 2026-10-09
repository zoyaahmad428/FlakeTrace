#!/bin/sh
# Runs INSIDE the container. Disassembles the classes needed for static-field
# extraction and writes one big dump to /out/javap_<which>.txt
#
#   $1 = "test" (classes listed in /out/javap_targets.txt) or "main"
#        (everything under target/classes, for the one-hop callee expansion)
set -u
CP="/w/target/classes:/w/target/test-classes:$(cat /out/ft_cp.txt)"
WHICH="$1"

if [ "$WHICH" = "main" ]; then
    ( cd /w/target/classes && find . -name '*.class' ) \
        | sed 's|^\./||; s|\.class$||; s|/|.|g' > /out/javap_main_list.txt
    LIST=/out/javap_main_list.txt
else
    LIST=/out/javap_targets.txt
fi

echo "classes to disassemble: $(wc -l < $LIST)"
# -p includes private members; -c gives bytecode with resolved // Field comments
xargs -a "$LIST" -n 200 javap -p -c -cp "$CP" > "/out/javap_${WHICH}.txt" 2>/dev/null
echo "dump bytes: $(wc -c < /out/javap_${WHICH}.txt)"
