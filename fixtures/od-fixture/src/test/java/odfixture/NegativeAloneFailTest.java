package odfixture;

import org.junit.Test;
import static org.junit.Assert.assertEquals;

/** N1 negative control: fails every time, including when run alone. Not order-dependent. */
public class NegativeAloneFailTest {
    @Test
    public void alwaysFails() {
        assertEquals(2, 1 + 1 - 1);
    }
}
