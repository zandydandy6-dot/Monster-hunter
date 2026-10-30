import com.sun.source.util.JavacTask;
import javax.tools.*;
import java.io.File;
import java.util.*;

/** Syntax-checks Java files with the JDK's own parser (no Minecraft/Forge needed). Usage: java ParseCheck.java <files...> */
public class ParseCheck {
    public static void main(String[] args) throws Exception {
        JavaCompiler c = ToolProvider.getSystemJavaCompiler();
        DiagnosticCollector<JavaFileObject> diags = new DiagnosticCollector<>();
        StandardJavaFileManager fm = c.getStandardFileManager(diags, null, null);
        List<File> files = new ArrayList<>();
        for (String a : args) files.add(new File(a));
        JavacTask task = (JavacTask) c.getTask(null, fm, diags, List.of("-proc:none"), null, fm.getJavaFileObjectsFromFiles(files));
        int units = 0;
        for (var u : task.parse()) units++;
        int errors = 0;
        for (Diagnostic<? extends JavaFileObject> d : diags.getDiagnostics()) {
            if (d.getKind() == Diagnostic.Kind.ERROR) {
                errors++;
                System.out.println("SYNTAX ERROR " + d.getSource().getName() + ":" + d.getLineNumber() + ": " + d.getMessage(null));
            }
        }
        System.out.println("parsed " + units + " files, " + errors + " syntax errors");
        System.exit(errors == 0 ? 0 : 1);
    }
}
