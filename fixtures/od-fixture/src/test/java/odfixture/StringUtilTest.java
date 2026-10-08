package odfixture;

import org.junit.Test;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

/** Benign noise test: touches no shared state. */
public class StringUtilTest {
    @Test
    public void reversesAString() {
        assertEquals("cba", StringUtil.reverse("abc"));
    }

    @Test
    public void detectsPalindrome() {
        assertTrue(StringUtil.isPalindrome("racecar"));
    }
}
