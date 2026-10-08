package odfixture;

/** Benign utility: pure function, no shared state. Used as noise for the search. */
public class MathUtil {
    public static int add(int a, int b) {
        return a + b;
    }

    public static int square(int x) {
        return x * x;
    }
}
