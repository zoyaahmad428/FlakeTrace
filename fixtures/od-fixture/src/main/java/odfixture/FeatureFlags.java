package odfixture;

/** F2 fixture: production code that reads a system property, never writes it. */
public class FeatureFlags {
    public static boolean isTurboEnabled() {
        return System.getProperty("odfixture.turbo") != null;
    }
}
