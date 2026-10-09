import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.List;

import org.junit.runner.JUnitCore;
import org.junit.runner.Request;
import org.junit.runner.Result;
import org.junit.runner.notification.Failure;

/**
 * Executes a declared sequence of test methods in ONE JVM, in the given order,
 * and prints one machine-readable line per test.
 *
 * Usage:  FtRunner <specfile>        # one "pkg.Class#method" per line
 *         FtRunner -e spec [spec..]  # specs on the command line
 *
 * Output (tab separated, prefix FT):
 *   FT<TAB>idx<TAB>spec<TAB>PASS|FAIL<TAB>excFqcn<TAB>message<TAB>topFrames<TAB>millis
 *
 * Frames are joined with "|". Newlines/tabs inside message and frames are
 * escaped so each test always occupies exactly one line.
 */
public class FtRunner {

    public static void main(String[] args) throws Exception {
        List<String> specs = new ArrayList<String>();

        // -s <SetupClass> reproduces the project's declared execution context by
        // invoking that class's @BeforeClass methods before any test runs.
        // jsoniter's Surefire config never runs test classes directly: it runs
        // suite classes (e.g. com.jsoniter.suite.StreamingTests) whose
        // @BeforeClass selects the codegen mode. Without this, generated-codec
        // collisions surface as LinkageError for nearly every order, which is a
        // harness artifact rather than order dependence.
        if (args.length >= 2 && "-s".equals(args[0])) {
            String setupClass = args[1];
            String[] rest = new String[args.length - 2];
            System.arraycopy(args, 2, rest, 0, rest.length);
            args = rest;
            if (!"-".equals(setupClass)) runSetup(setupClass);
        }

        if (args.length >= 1 && "-e".equals(args[0])) {
            for (int i = 1; i < args.length; i++) specs.add(args[i]);
        } else if (args.length == 1) {
            BufferedReader r = new BufferedReader(new FileReader(args[0]));
            String line;
            while ((line = r.readLine()) != null) {
                line = line.trim();
                if (line.length() > 0 && !line.startsWith("#")) specs.add(line);
            }
            r.close();
        } else {
            System.err.println("usage: FtRunner <specfile> | -e spec [spec..]");
            System.exit(2);
        }

        int idx = 0;
        for (String spec : specs) {
            idx++;
            int h = spec.indexOf('#');
            if (h < 0) { emit(idx, spec, "FAIL", "BadSpec", "no # in spec", "", 0); continue; }
            String cls = spec.substring(0, h);
            String mth = spec.substring(h + 1);

            long t0 = System.currentTimeMillis();
            try {
                Class<?> c = Class.forName(cls, true, FtRunner.class.getClassLoader());
                // Request.method drives JUnit 3 TestCase classes through
                // JUnit38ClassRunner, so JUnit 3 and 4 share this path.
                Result res = new JUnitCore().run(Request.method(c, mth));
                long ms = System.currentTimeMillis() - t0;

                if (res.getRunCount() == 0) {
                    emit(idx, spec, "FAIL", "NotRun",
                         "no test executed (missing method or filtered out)", "", ms);
                } else if (res.wasSuccessful()) {
                    emit(idx, spec, "PASS", "", "", "", ms);
                } else {
                    Failure f = res.getFailures().get(0);
                    Throwable t = f.getException();
                    emit(idx, spec, "FAIL",
                         t == null ? "Unknown" : t.getClass().getName(),
                         t == null ? "" : String.valueOf(t.getMessage()),
                         frames(t), ms);
                }
            } catch (Throwable t) {
                long ms = System.currentTimeMillis() - t0;
                emit(idx, spec, "FAIL", t.getClass().getName(),
                     String.valueOf(t.getMessage()), frames(t), ms);
            }
        }
        // Never let a lingering non-daemon thread from a subject test hang the run.
        System.out.flush();
        Runtime.getRuntime().halt(0);
    }

    /** Invoke every @BeforeClass on the named suite class, in declaration order. */
    private static void runSetup(String setupClass) {
        try {
            Class<?> sc = Class.forName(setupClass);
            for (java.lang.reflect.Method m : sc.getMethods()) {
                if (m.getAnnotation(org.junit.BeforeClass.class) != null) {
                    m.setAccessible(true);
                    m.invoke(null);
                    System.out.println("FTSETUP\t" + setupClass + "." + m.getName() + "\tOK");
                }
            }
        } catch (Throwable t) {
            System.out.println("FTSETUP\t" + setupClass + "\tFAILED\t"
                    + t.getClass().getName() + "\t" + t.getMessage());
        }
        System.out.flush();
    }

    /** Top 12 stack frames; signature normalisation happens offline in Python. */
    private static String frames(Throwable t) {
        if (t == null) return "";
        StackTraceElement[] st = t.getStackTrace();
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < st.length && i < 12; i++) {
            if (sb.length() > 0) sb.append('|');
            sb.append(st[i].getClassName()).append('.').append(st[i].getMethodName());
        }
        return sb.toString();
    }

    private static void emit(int idx, String spec, String status,
                             String exc, String msg, String frames, long ms) {
        System.out.println("FT\t" + idx + "\t" + spec + "\t" + status + "\t"
                + clean(exc) + "\t" + clean(msg) + "\t" + clean(frames) + "\t" + ms);
        System.out.flush();
    }

    private static String clean(String s) {
        if (s == null) return "";
        return s.replace("\\", "\\\\").replace("\t", "\\t")
                .replace("\r", "").replace("\n", "\\n");
    }
}
