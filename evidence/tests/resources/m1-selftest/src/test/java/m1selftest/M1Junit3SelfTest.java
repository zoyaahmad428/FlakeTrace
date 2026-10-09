package m1selftest;

import junit.framework.TestCase;

/** Member 1's extractor test input: JUnit 3 style, accesses only in setUp/tearDown. */
public class M1Junit3SelfTest extends TestCase {
    protected void setUp() {
        SelfTestState.counter = 3;
    }

    protected void tearDown() {
        boolean flag = Boolean.getBoolean("m1.selftest.flag");
    }

    public void testNothing() {
    }
}
