package odfixture;

import org.junit.Test;
import static org.junit.Assert.assertEquals;

/** Benign noise test: touches no shared state. */
public class MathUtilTest {
    @Test
    public void addsTwoNumbers() {
        assertEquals(5, MathUtil.add(2, 3));
    }

    @Test
    public void squaresANumber() {
        assertEquals(9, MathUtil.square(3));
    }
}
