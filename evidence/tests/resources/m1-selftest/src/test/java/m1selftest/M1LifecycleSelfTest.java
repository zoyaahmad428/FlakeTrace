package m1selftest;

import org.junit.After;
import org.junit.AfterClass;
import org.junit.BeforeClass;
import org.junit.Test;

/**
 * Member 1's extractor test input: every access here is in lifecycle code, none
 * in the test body. Expected attribution to emptyBody: static initialiser
 * (CLINIT), @BeforeClass, inherited @Before, @After, @AfterClass.
 */
public class M1LifecycleSelfTest extends M1LifecycleBase {
    static {
        System.setProperty("m1.selftest.clinit", "x");
    }

    @BeforeClass
    public static void beforeAll() {
        SelfTestState.counter = 2;
    }

    @After
    public void after() {
        System.clearProperty("m1.selftest.key");
    }

    @AfterClass
    public static void afterAll() {
        int seen = SelfTestState.counter;
    }

    @Test
    public void emptyBody() {
    }
}
