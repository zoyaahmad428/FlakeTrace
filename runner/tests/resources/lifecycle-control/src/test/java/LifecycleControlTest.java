import static org.junit.Assert.assertEquals;

import org.junit.BeforeClass;
import org.junit.Test;

/** ADR-012 section 3. Passes when @BeforeClass runs once for the class, as under Maven Surefire. */
public class LifecycleControlTest {
    static int classSetups = 0;

    @BeforeClass public static void once() { classSetups++; }

    @Test public void first() { assertEquals(1, classSetups); }
    @Test public void second() { assertEquals(1, classSetups); }
}
