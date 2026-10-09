#!/bin/sh
# Runs INSIDE the maven:3.9-eclipse-temurin-8 container.
#   /w      = subject project (bind mount, writable)
#   /src    = poc/src  (read-only)
#   /out    = poc/runner/<project>  (bind mount, writable)
# Produces in /out: ft_cp.txt (classpath), ft_tests.txt (candidate specs),
# and the compiled FtRunner/FtList classes.
set -e

echo "== resolving test classpath"
mvn -B -q dependency:build-classpath \
    -Dmdep.outputFile=/out/ft_cp.txt \
    -Dmdep.includeScope=test

CP="/w/target/classes:/w/target/test-classes:$(cat /out/ft_cp.txt)"

echo "== compiling runner"
javac -nowarn -d /out -cp "$CP" /src/runner/FtRunner.java /src/runner/FtList.java

echo "== enumerating test methods"
java -cp "/out:$CP" FtList /w/target/test-classes > /out/ft_tests.txt 2>/out/ft_list.err
echo "candidates: $(wc -l < /out/ft_tests.txt)"
tail -1 /out/ft_list.err
