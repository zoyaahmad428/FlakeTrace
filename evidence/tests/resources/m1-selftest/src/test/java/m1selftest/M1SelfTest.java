package m1selftest;

import org.junit.Test;

/**
 * Member 1's extractor test input (Phase 2 acceptance case). The test body has
 * exactly four supported accesses and nothing else that touches shared state:
 * one static write, one static read, one setProperty, one getProperty.
 */
public class M1SelfTest {
    @Test
    public void writesAndReads() {
        SelfTestState.counter = 5;
        int seen = SelfTestState.counter;
        System.setProperty("m1.selftest.key", "on");
        String value = System.getProperty("m1.selftest.key");
    }
}
