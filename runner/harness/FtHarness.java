import java.io.BufferedReader;
import java.io.FileOutputStream;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.TimeZone;

import org.junit.internal.runners.ErrorReportingRunner;
import org.junit.runner.Description;
import org.junit.runner.JUnitCore;
import org.junit.runner.Request;
import org.junit.runner.Runner;
import org.junit.runner.manipulation.Filter;
import org.junit.runner.notification.Failure;
import org.junit.runner.notification.RunListener;
import org.junit.runners.BlockJUnit4ClassRunner;
import org.junit.runners.JUnit4;

/**
 * Runs the tests listed on stdin ("Class#method", one per line) in that exact order, in this
 * one JVM, and writes one tab-separated result line per test to the file named in args[0].
 * With "--list <file>", reads class names instead and writes each class's test methods as
 * "Class#method", in the order JUnit would run them (ADR-004).
 * With "--env <file>", writes what this JVM runs the tests under, one "key\tvalue" per line (ADR-012 section 6).
 * "<file> --lifecycle class-grouped" runs each run of consecutive same-class tests as one JUnit
 * request, so @BeforeClass/@AfterClass run once per block as under Surefire (ADR-012 section 2);
 * the default, "per-method", runs every test as its own request.
 * Launched by runner/order_runner.py; see ADR-003.
 */
public class FtHarness {

    public static void main(String[] args) throws Exception {
        if (args[0].equals("--list")) {
            list(args[1]);
            System.exit(0);
        }
        if (args[0].equals("--env")) {
            env(args[1]);
            System.exit(0);
        }
        boolean grouped = args.length > 2 && args[1].equals("--lifecycle") && args[2].equals("class-grouped");
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in, "UTF-8"));
        List<String> specs = new ArrayList<String>();
        String line;
        while ((line = in.readLine()) != null) {
            line = line.trim();
            if (!line.isEmpty()) {
                specs.add(line);
            }
        }
        PrintStream out = new PrintStream(new FileOutputStream(args[0]), true, "UTF-8");
        int start = 0;
        while (start < specs.size()) {
            String cls = className(specs.get(start));
            int end = start + 1;
            while (end < specs.size() && className(specs.get(end)).equals(cls)) {
                end++;
            }
            if (!grouped || !runBlock(out, specs, start, end)) {
                for (int i = start; i < end; i++) {
                    out.println(i + "\t" + specs.get(i) + "\t" + runOne(specs.get(i)));
                }
            }
            start = end;
        }
        out.close();
        // Tests may leave non-daemon threads running; exit so the JVM never hangs after the last test.
        System.exit(0);
    }

    static String className(String spec) {
        return spec.substring(0, spec.indexOf('#'));
    }

    /**
     * Runs specs[start, end) -- one class -- as one request filtered to those methods, in that
     * order, writing each result line as the test finishes. Returns false, running nothing, when
     * the class is not on JUnit's default runner (JUnit 3, @RunWith, suite()): JUnit 3 silently
     * ignores sorting (ADR-012 section 2 spike), so those keep one request per test.
     */
    static boolean runBlock(final PrintStream out, final List<String> specs, final int start, int end) {
        Class<?> cls;
        try {
            cls = Class.forName(className(specs.get(start)));
        } catch (Throwable t) {
            // Report this first failure (e.g. ExceptionInInitializerError, whose cause would be lost
            // on a second load attempt), then the rest one by one, exactly as per-method does.
            out.println(start + "\t" + specs.get(start) + "\t" + format("FAIL", t));
            for (int i = start + 1; i < end; i++) {
                out.println(i + "\t" + specs.get(i) + "\t" + runOne(specs.get(i)));
            }
            return true;
        }
        Runner runner = Request.aClass(cls).getRunner();
        if (runner.getClass() != JUnit4.class && runner.getClass() != BlockJUnit4ClassRunner.class) {
            return false;
        }
        final List<String> methods = new ArrayList<String>();
        for (int i = start; i < end; i++) {
            methods.add(specs.get(i).substring(specs.get(i).indexOf('#') + 1));
        }
        final int n = methods.size();
        final Throwable[] failures = new Throwable[n];
        final boolean[] skipped = new boolean[n];
        final boolean[] written = new boolean[n];
        final boolean[] started = new boolean[1];
        final Throwable[] setupFailure = new Throwable[1];
        final boolean[] setupSkipped = new boolean[1];
        RunListener listener = new RunListener() {
            void write(Description d) {
                int i = methods.indexOf(d.getMethodName());
                if (i < 0 || written[i]) {
                    return;
                }
                String result = failures[i] != null ? format("FAIL", failures[i]) : skipped[i] ? "SKIP\t\t\t" : "PASS\t\t\t";
                out.println((start + i) + "\t" + specs.get(start + i) + "\t" + result);
                written[i] = true;
            }

            @Override
            public void testStarted(Description d) {
                started[0] = true;
            }

            @Override
            public void testFailure(Failure f) {
                int i = methods.indexOf(f.getDescription().getMethodName());
                if (i >= 0) {
                    failures[i] = f.getException();
                } else if (!started[0] && setupFailure[0] == null) {
                    setupFailure[0] = f.getException();  // @BeforeClass, or no test matched the filter
                }
            }

            @Override
            public void testAssumptionFailure(Failure f) {
                int i = methods.indexOf(f.getDescription().getMethodName());
                if (i >= 0) {
                    skipped[i] = true;
                } else if (!started[0]) {
                    setupSkipped[0] = true;  // an assumption failed in @BeforeClass: nothing runs
                }
            }

            @Override
            public void testIgnored(Description d) {
                int i = methods.indexOf(d.getMethodName());
                if (i >= 0) {
                    skipped[i] = true;
                }
                write(d);
            }

            @Override
            public void testFinished(Description d) {
                write(d);
            }
        };
        JUnitCore core = new JUnitCore();
        core.addListener(listener);
        core.run(Request.aClass(cls)
            .filterWith(new Filter() {
                @Override
                public boolean shouldRun(Description d) {
                    return !d.isTest() || methods.contains(d.getMethodName());
                }

                @Override
                public String describe() {
                    return "methods " + methods;
                }
            })
            .sortWith(new Comparator<Description>() {
                @Override
                public int compare(Description a, Description b) {
                    return methods.indexOf(a.getMethodName()) - methods.indexOf(b.getMethodName());
                }
            }));
        for (int i = 0; i < n; i++) {
            if (!written[i]) {
                // Never ran: the class setup failed or was skipped, or JUnit has no such test method.
                String result;
                if (setupFailure[0] != null) {
                    result = format("FAIL", setupFailure[0]);
                } else if (setupSkipped[0]) {
                    result = "SKIP\t\t\t";
                } else {
                    result = format("FAIL", new Exception(
                        "No tests found matching Method " + methods.get(i) + "(" + cls.getName() + ")"));
                }
                out.println((start + i) + "\t" + specs.get(start + i) + "\t" + result);
            }
        }
        return true;
    }

    static void list(String resultFile) throws Exception {
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in, "UTF-8"));
        PrintStream out = new PrintStream(new FileOutputStream(resultFile), true, "UTF-8");
        String line;
        while ((line = in.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty()) {
                continue;
            }
            Runner runner;
            try {
                runner = Request.aClass(Class.forName(line)).getRunner();
            } catch (Throwable t) {
                continue;  // a class that cannot even load cannot be run either
            }
            if (runner instanceof ErrorReportingRunner) {
                continue;  // abstract class, or no @Test methods
            }
            for (Description child : runner.getDescription().getChildren()) {
                if (child.isTest() && child.getMethodName() != null) {
                    out.println(line + "#" + child.getMethodName());
                }
            }
        }
        out.close();
    }

    static void env(String resultFile) throws Exception {
        PrintStream out = new PrintStream(new FileOutputStream(resultFile), true, "UTF-8");
        out.println("java.version\t" + escape(System.getProperty("java.version")));
        out.println("timezone\t" + escape(TimeZone.getDefault().getID()));
        out.println("locale\t" + escape(Locale.getDefault().toString()));
        out.println("file.encoding\t" + escape(System.getProperty("file.encoding")));
        out.println("junit.version\t" + escape(junit.runner.Version.id()));
        out.close();
    }

    static String runOne(String spec) {
        int hash = spec.indexOf('#');
        Class<?> cls;
        try {
            cls = Class.forName(spec.substring(0, hash));
        } catch (Throwable t) {
            return format("FAIL", t);
        }
        final Throwable[] failure = new Throwable[1];
        final boolean[] skipped = new boolean[1];
        JUnitCore core = new JUnitCore();
        core.addListener(new RunListener() {
            @Override
            public void testFailure(Failure f) {
                failure[0] = f.getException();
            }

            @Override
            public void testAssumptionFailure(Failure f) {
                skipped[0] = true;
            }

            @Override
            public void testIgnored(Description d) {
                skipped[0] = true;
            }
        });
        core.run(Request.method(cls, spec.substring(hash + 1)));
        if (failure[0] != null) {
            return format("FAIL", failure[0]);
        }
        return skipped[0] ? "SKIP\t\t\t" : "PASS\t\t\t";
    }

    static String format(String status, Throwable t) {
        StringBuilder frames = new StringBuilder();
        for (StackTraceElement e : t.getStackTrace()) {
            if (frames.length() > 0) {
                frames.append('|');
            }
            frames.append(e.getClassName()).append('.').append(e.getMethodName())
                  .append(':').append(e.getLineNumber());
        }
        String message = t.getMessage() == null ? "" : t.getMessage();
        return status + "\t" + t.getClass().getName() + "\t" + escape(message) + "\t" + escape(frames.toString());
    }

    static String escape(String s) {
        return s.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r");
    }
}
