package pkg.bvt;

import org.junit.Test;

/** Matches the include and Surefire's default name, but the project's exclude removes it. */
public class SkipMeTest {
    @Test public void excluded() {}
}
