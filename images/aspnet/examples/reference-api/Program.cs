using System.Security.Cryptography;
using System.Runtime.InteropServices;
using System.Text;

var builder = WebApplication.CreateSlimBuilder(args);
var app = builder.Build();
var assuranceLevel = Environment.GetEnvironmentVariable("IHL_ASSURANCE_LEVEL") ?? "unknown";

app.MapGet("/", () => Results.Ok(new
{
    artifact = "IHL-CTR-0001",
    assuranceLevel,
    message = "Indian Hill ASP.NET 10 Runtime reference application"
}));

app.MapGet("/healthz", () => Results.Ok(new { status = "ok" }));

// Lab-only diagnostics used by the manual hardening checks. Do not copy this
// endpoint into a production application without an explicit need and review.
app.MapGet("/diagnostics/security", () => Results.Ok(new
{
    effectiveUid = NativeIdentity.GetEffectiveUserId(),
    assuranceLevel,
    dotnetDiagnosticsDisabled =
        Environment.GetEnvironmentVariable("DOTNET_EnableDiagnostics") == "0",
    dotnetDiagnosticSocketPresent = DiagnosticProbe.HasDiagnosticSocket(),
    rootFilesystemWriteSucceeded = FileProbe.CanWrite("/ihl-root-write-probe"),
    temporaryFilesystemWriteSucceeded = FileProbe.CanWrite("/tmp/ihl-tmp-write-probe")
}));

// This endpoint is emitted by the reference application only. The Validated
// pipeline uses it to bind provider identity and approved-mode application
// behavior to the exact reference-image digest under test.
app.MapGet("/diagnostics/crypto", () => Results.Ok(CryptoProbe.Observe(assuranceLevel)));

app.Run();

internal static class NativeIdentity
{
    [DllImport("libc", EntryPoint = "geteuid")]
    private static extern uint GetEffectiveUserIdLinux();

    internal static uint? GetEffectiveUserId() =>
        OperatingSystem.IsLinux() ? GetEffectiveUserIdLinux() : null;
}

internal static class FileProbe
{
    internal static bool CanWrite(string path)
    {
        try
        {
            File.WriteAllText(path, "probe");
            File.Delete(path);
            return true;
        }
        catch (UnauthorizedAccessException)
        {
            return false;
        }
        catch (IOException)
        {
            return false;
        }
    }
}

internal static class DiagnosticProbe
{
    internal static bool HasDiagnosticSocket()
    {
        try
        {
            return Directory.Exists("/tmp") &&
                Directory.EnumerateFileSystemEntries(
                    "/tmp",
                    "dotnet-diagnostic-*-socket"
                ).Any();
        }
        catch (IOException)
        {
            return false;
        }
        catch (UnauthorizedAccessException)
        {
            return false;
        }
    }
}

internal static class CryptoProbe
{
    private const string LibCrypto = "libcrypto.so.3";

    [DllImport(LibCrypto, CallingConvention = CallingConvention.Cdecl)]
    private static extern IntPtr OpenSSL_version(int type);

    [DllImport(LibCrypto, CallingConvention = CallingConvention.Cdecl)]
    private static extern int EVP_default_properties_is_fips_enabled(IntPtr libctx);

    [DllImport(LibCrypto, CallingConvention = CallingConvention.Cdecl, CharSet = CharSet.Ansi)]
    private static extern IntPtr OSSL_PROVIDER_load(IntPtr libctx, string name);

    [DllImport(LibCrypto, CallingConvention = CallingConvention.Cdecl)]
    private static extern int OSSL_PROVIDER_self_test(IntPtr provider);

    [DllImport(LibCrypto, CallingConvention = CallingConvention.Cdecl)]
    private static extern int OSSL_PROVIDER_unload(IntPtr provider);

    [DllImport(LibCrypto, CallingConvention = CallingConvention.Cdecl, CharSet = CharSet.Ansi)]
    private static extern IntPtr EVP_MD_fetch(
        IntPtr libctx,
        string algorithm,
        string properties
    );

    [DllImport(LibCrypto, CallingConvention = CallingConvention.Cdecl)]
    private static extern void EVP_MD_free(IntPtr digest);

    internal static object Observe(string assuranceLevel)
    {
        if (!OperatingSystem.IsLinux() || assuranceLevel != "validated")
        {
            return new
            {
                applicable = false,
                assuranceLevel,
                reason = "The FIPS approved-mode probe applies only to the Validated Linux image."
            };
        }

        var fipsProvider = OSSL_PROVIDER_load(IntPtr.Zero, "fips");
        var baseProvider = OSSL_PROVIDER_load(IntPtr.Zero, "base");
        IntPtr approvedSha256 = IntPtr.Zero;
        IntPtr prohibitedMd5 = IntPtr.Zero;

        try
        {
            if (fipsProvider != IntPtr.Zero)
            {
                approvedSha256 = EVP_MD_fetch(IntPtr.Zero, "SHA2-256", "fips=yes");
                prohibitedMd5 = EVP_MD_fetch(IntPtr.Zero, "MD5", "fips=yes");
            }

            var moduleDirectory = Environment.GetEnvironmentVariable("OPENSSL_MODULES") ?? "";
            var modulePath = Path.Combine(moduleDirectory, "fips.so");
            var configPath = Environment.GetEnvironmentVariable("OPENSSL_CONF") ?? "";
            var moduleSha256 = File.Exists(modulePath)
                ? Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(modulePath))).ToLowerInvariant()
                : "missing";

            return new
            {
                applicable = true,
                assuranceLevel,
                standard = Environment.GetEnvironmentVariable("IHL_FIPS_STANDARD"),
                moduleName = Environment.GetEnvironmentVariable("IHL_FIPS_MODULE_NAME"),
                moduleVersion = Environment.GetEnvironmentVariable("IHL_FIPS_MODULE_VERSION"),
                cmvpCertificate = Environment.GetEnvironmentVariable("IHL_FIPS_CMVP_CERTIFICATE"),
                sourceArchiveSha256 = Environment.GetEnvironmentVariable("IHL_FIPS_SOURCE_SHA256"),
                baseLibraryName = Environment.GetEnvironmentVariable("IHL_OPENSSL_BASE_NAME"),
                baseLibraryVersion = Environment.GetEnvironmentVariable("IHL_OPENSSL_BASE_VERSION"),
                baseLibrarySourceArchiveSha256 =
                    Environment.GetEnvironmentVariable("IHL_OPENSSL_BASE_SOURCE_SHA256"),
                opensslVersion = Marshal.PtrToStringAnsi(OpenSSL_version(0)),
                modulePath,
                moduleSha256,
                configPath,
                fipsProviderLoaded = fipsProvider != IntPtr.Zero,
                baseProviderLoaded = baseProvider != IntPtr.Zero,
                defaultPropertiesFipsEnabled =
                    EVP_default_properties_is_fips_enabled(IntPtr.Zero) == 1,
                integrityAndSelfTestsPassed =
                    fipsProvider != IntPtr.Zero && OSSL_PROVIDER_self_test(fipsProvider) == 1,
                approvedSha256FetchPassed = approvedSha256 != IntPtr.Zero,
                prohibitedMd5FetchBlocked = prohibitedMd5 == IntPtr.Zero,
                applicationSha256Passed = ApplicationSha256Passed(),
                applicationAesGcmPassed = ApplicationAesGcmPassed(),
                selfTestsOnLoad = ConfigRequiresSelfTestsOnLoad(configPath)
            };
        }
        finally
        {
            if (approvedSha256 != IntPtr.Zero)
            {
                EVP_MD_free(approvedSha256);
            }
            if (prohibitedMd5 != IntPtr.Zero)
            {
                EVP_MD_free(prohibitedMd5);
            }
            if (baseProvider != IntPtr.Zero)
            {
                OSSL_PROVIDER_unload(baseProvider);
            }
            if (fipsProvider != IntPtr.Zero)
            {
                OSSL_PROVIDER_unload(fipsProvider);
            }
        }
    }

    private static bool ApplicationSha256Passed()
    {
        var input = Encoding.UTF8.GetBytes("Indian Hill Labs FIPS application probe");
        var expected = Convert.FromHexString(
            "E16A97085159BCF928FF8C37E7151F86DE7BCF72E04801DC15B172CBB378DA65"
        );
        return SHA256.HashData(input).SequenceEqual(expected);
    }

    private static bool ApplicationAesGcmPassed()
    {
        var key = Enumerable.Range(0, 32).Select(value => (byte)value).ToArray();
        var nonce = Enumerable.Range(0, 12).Select(value => (byte)(value + 32)).ToArray();
        var plaintext = Encoding.UTF8.GetBytes("IHL FIPS AES-GCM application probe");
        var ciphertext = new byte[plaintext.Length];
        var recovered = new byte[plaintext.Length];
        var tag = new byte[16];

        using var aes = new AesGcm(key, tag.Length);
        aes.Encrypt(nonce, plaintext, ciphertext, tag);
        aes.Decrypt(nonce, ciphertext, tag, recovered);
        return plaintext.SequenceEqual(recovered);
    }

    private static bool ConfigRequiresSelfTestsOnLoad(string configPath)
    {
        var moduleConfig = Path.Combine(Path.GetDirectoryName(configPath) ?? "", "fipsmodule.cnf");
        if (!File.Exists(moduleConfig))
        {
            return false;
        }

        var text = File.ReadAllText(moduleConfig);
        return !text.Contains("install-status", StringComparison.OrdinalIgnoreCase) &&
            !text.Contains("install-mac", StringComparison.OrdinalIgnoreCase);
    }
}
