import java.awt.Desktop;
import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.nio.file.Path;

/**
 * Starts the Python/Flask calculator backend and opens the web interface.
 * Run this from the project folder after installing requirements.txt.
 */
public class CalculatorLauncher {
    public static void main(String[] args) throws Exception {
        Path project = Path.of("").toAbsolutePath();
        String python = System.getProperty("os.name").toLowerCase().contains("win")
                ? "python" : "python3";

        ProcessBuilder builder = new ProcessBuilder(python, "app.py");
        builder.directory(new File(project.toString()));
        builder.inheritIO();
        Process server = builder.start();

        Runtime.getRuntime().addShutdownHook(new Thread(() -> server.destroy()));

        // Give Flask a moment to start before opening the local web app.
        Thread.sleep(1600);
        if (Desktop.isDesktopSupported()) {
            Desktop.getDesktop().browse(new URI("http://127.0.0.1:5000"));
        } else {
            System.out.println("Open http://127.0.0.1:5000 in your browser.");
        }
        System.out.println("SmartCalc is running. Keep this terminal open; press Ctrl+C to stop.");
        int exitCode = server.waitFor();
        if (exitCode != 0) {
            System.err.println("The Python server stopped. Check that Python and Flask are installed.");
        }
    }
}
