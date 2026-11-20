package pkg;

import org.junit.Test;

/** Has a default test name but lies outside bvt/, so this project's build never runs it. */
public class OutsideTest {
    @Test public void notRunByThisProject() {}
}
