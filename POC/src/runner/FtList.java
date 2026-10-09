import java.io.File;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Enumerates candidate test methods from a compiled test-classes directory,
 * using the frozen definition:
 *
 *   "a test method is a public no-arg method named test* in a
 *    junit.framework.TestCase subclass"
 *
 * Prints one "pkg.Class#method" per line, sorted. Classes are loaded WITHOUT
 * initialisation so no subject <clinit> runs during enumeration.
 *
 * Usage: FtList <test-classes-dir>
 */
public class FtList {

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            System.err.println("usage: FtList <test-classes-dir>");
            System.exit(2);
        }
        File root = new File(args[0]);
        List<String> classNames = new ArrayList<String>();
        collect(root, root, classNames);
        Collections.sort(classNames);

        Class<?> testCase = Class.forName("junit.framework.TestCase");
        Class<? extends java.lang.annotation.Annotation> testAnn =
                Class.forName("org.junit.Test")
                     .asSubclass(java.lang.annotation.Annotation.class);
        List<String> out = new ArrayList<String>();

        for (String cn : classNames) {
            Class<?> c;
            try {
                c = Class.forName(cn, false, FtList.class.getClassLoader());
            } catch (Throwable t) {
                System.err.println("SKIP_LOAD\t" + cn + "\t" + t.getClass().getSimpleName());
                continue;
            }
            if (Modifier.isAbstract(c.getModifiers())) continue;
            if (!Modifier.isPublic(c.getModifiers())) continue;

            // A class qualifies under either convention: a JUnit 3 TestCase
            // subclass, or any class carrying @Test methods (JUnit 4). Both are
            // driven identically by Request.method() in FtRunner.
            boolean junit3 = testCase.isAssignableFrom(c);
            boolean junit4 = false;
            try {
                for (Method m : c.getMethods()) {
                    if (m.getAnnotation(testAnn) != null) { junit4 = true; break; }
                }
            } catch (Throwable ignored) { }
            if (!junit3 && !junit4) continue;

            Method[] ms;
            try {
                ms = c.getMethods();   // includes inherited, matching TestSuite
            } catch (Throwable t) {
                System.err.println("SKIP_METHODS\t" + cn + "\t" + t.getClass().getSimpleName());
                continue;
            }
            for (Method m : ms) {
                boolean annotated = m.getAnnotation(testAnn) != null;
                // JUnit 3 names the test; JUnit 4 annotates it.
                if (!annotated && !(junit3 && m.getName().startsWith("test"))) continue;
                if (m.getParameterTypes().length != 0) continue;
                if (!Modifier.isPublic(m.getModifiers())) continue;
                if (Modifier.isStatic(m.getModifiers())) continue;
                if (!m.getReturnType().equals(Void.TYPE)) continue;
                out.add(c.getName() + "#" + m.getName());
            }
        }
        Collections.sort(out);
        for (String s : out) System.out.println(s);
        System.err.println("TOTAL\t" + out.size());
    }

    private static void collect(File root, File dir, List<String> acc) {
        File[] fs = dir.listFiles();
        if (fs == null) return;
        for (File f : fs) {
            if (f.isDirectory()) {
                collect(root, f, acc);
            } else if (f.getName().endsWith(".class") && f.getName().indexOf('$') < 0) {
                String rel = f.getAbsolutePath().substring(root.getAbsolutePath().length() + 1);
                acc.add(rel.substring(0, rel.length() - 6).replace(File.separatorChar, '.'));
            }
        }
    }
}
