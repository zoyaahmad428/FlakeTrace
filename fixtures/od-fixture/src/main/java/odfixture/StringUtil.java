package odfixture;

/** Benign utility: pure function, no shared state. Used as noise for the search. */
public class StringUtil {
    public static String reverse(String s) {
        return new StringBuilder(s).reverse().toString();
    }

    public static boolean isPalindrome(String s) {
        return s.equals(reverse(s));
    }
}
