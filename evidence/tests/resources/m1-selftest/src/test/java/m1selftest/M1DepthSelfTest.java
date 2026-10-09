package m1selftest;

import org.junit.Test;

/**
 * Member 1's extractor test input for call depth (Phase 3). Expected:
 * callsDown: counter WRITE at depth 2 (level2), property WRITE at depth 3 (level3);
 *            level4's READ is at depth 4, so never reported (max depth 3).
 * recursion: ping/pong call each other; the cycle must terminate.
 * dispatch:  the call names SelfTestBase.work but SelfTestChild.work runs; only the
 *            named target can be followed statically, so this is reported as unsupported.
 */
public class M1DepthSelfTest {
    @Test
    public void callsDown() {
        level2();
    }

    static void level2() {
        SelfTestState.counter = 6;
        level3();
    }

    static void level3() {
        System.setProperty("m1.selftest.deep", "y");
        level4();
    }

    static void level4() {
        int seen = SelfTestState.counter;
    }

    @Test
    public void recursion() {
        ping(3);
    }

    static void ping(int n) {
        if (n > 0) {
            pong(n - 1);
        }
    }

    static void pong(int n) {
        SelfTestState.counter = n;
        ping(n);
    }

    @Test
    public void dispatch() {
        SelfTestBase task = new SelfTestChild();
        task.work();
    }
}
