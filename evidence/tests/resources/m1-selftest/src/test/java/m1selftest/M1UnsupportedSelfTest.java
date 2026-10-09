package m1selftest;

import org.junit.Test;

/**
 * Member 1's extractor test input: things depth-1 static analysis must report as
 * unsupported instead of guessing. A property key built at runtime, reflection,
 * and a project call that depth 1 does not follow.
 */
public class M1UnsupportedSelfTest {
    @Test
    public void tricky() throws Exception {
        String key = "m1.selftest." + System.nanoTime();
        String value = System.getProperty(key);
        SelfTestState.class.getField("counter").setInt(null, 9);
        helper();
    }

    private static void helper() {
        SelfTestState.counter = 4;
    }
}
