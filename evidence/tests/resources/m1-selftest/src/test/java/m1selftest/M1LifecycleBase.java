package m1selftest;

import org.junit.Before;

/** Member 1's extractor test input: a superclass whose @Before is inherited. */
public abstract class M1LifecycleBase {
    @Before
    public void baseBefore() {
        SelfTestState.counter = 1;
    }
}
