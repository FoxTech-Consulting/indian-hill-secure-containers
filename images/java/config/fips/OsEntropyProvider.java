package com.indianhilllabs.crypto;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.Provider;
import java.security.ProviderException;
import java.security.SecureRandomSpi;
import java.security.SecureRandom;
import java.security.GeneralSecurityException;
import java.util.List;
import java.util.Map;

/** External Linux entropy adapter, not a cryptographic module or DRBG. */
public final class OsEntropyProvider extends Provider {
    public OsEntropyProvider() {
        super("IHL-ENTROPY", 1.0, "Linux /dev/random seed collection; outside the BC-FJA boundary");
        putService(new Service(this, "SecureRandom", "OS-ENTROPY", SeedSource.class.getName(),
                java.util.Collections.emptyList(), java.util.Collections.emptyMap()));
    }

    public static final class SeedSource extends SecureRandomSpi {
        @Override protected void engineSetSeed(byte[] ignored) {
            // Caller material cannot replace or weaken the OS entropy source.
        }
        @Override protected void engineNextBytes(byte[] bytes) {
            try {
                // Applications calling getInstanceStrong still receive BCFIPS DRBG output.
                // BCFIPS itself calls generateSeed below, so this does not recurse.
                SecureRandom.getInstance("DEFAULT", "BCFIPS").nextBytes(bytes);
            } catch (GeneralSecurityException failure) {
                throw new ProviderException("BCFIPS random output unavailable", failure);
            }
        }
        @Override protected byte[] engineGenerateSeed(int count) {
            if (count < 0 || count > 1048576) throw new IllegalArgumentException("Invalid seed request");
            try (InputStream input = Files.newInputStream(Paths.get("/dev/random"))) {
                byte[] bytes = new byte[count];
                new java.io.DataInputStream(input).readFully(bytes);
                return bytes;
            } catch (IOException failure) {
                throw new ProviderException("OS entropy source unavailable", failure);
            }
        }
    }
}
