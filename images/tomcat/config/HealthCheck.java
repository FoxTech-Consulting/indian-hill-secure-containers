import java.net.HttpURLConnection;
import java.net.URI;
public final class HealthCheck {
    public static void main(String[] args) throws Exception {
        var connection = (HttpURLConnection) URI.create("http://127.0.0.1:8080/healthz").toURL().openConnection();
        connection.setConnectTimeout(2000);
        connection.setReadTimeout(2000);
        try {
            // A bare Tomcat server has no deployed context, including /healthz.
            if (connection.getResponseCode() != 404) System.exit(1);
        } finally { connection.disconnect(); }
    }
}
