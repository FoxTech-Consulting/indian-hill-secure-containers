/* IHL Redis-only integration. Provider enforcement is not release qualification. */
#ifndef IHL_REDIS_CRYPTO_H
#define IHL_REDIS_CRYPTO_H
#include <openssl/crypto.h>
#include <openssl/evp.h>
#include <openssl/err.h>
#include <openssl/provider.h>
#include <openssl/rand.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define IHL_CRYPTO_CONFIG "/opt/openssl/ssl/redis-fips.cnf"
#define IHL_CRYPTO_MODULES "/opt/openssl/lib/ossl-modules"

/* Build-controlled default; assessment cannot disable this with an environment override. */
#ifndef IHL_REDIS_FIPS_VALIDATION
#define IHL_REDIS_FIPS_VALIDATION 1
#endif
#if IHL_REDIS_FIPS_VALIDATION != 0 && IHL_REDIS_FIPS_VALIDATION != 1
#error IHL_REDIS_FIPS_VALIDATION must be 0 or 1
#endif

static OSSL_PROVIDER *ihlCryptoFipsProvider;

static inline void ihlCryptoFail(void) {
    fputs("IHL Redis: required cryptographic provider check failed\n", stderr);
    exit(78);
}

static inline void ihlCryptoCheck(int ok) {
    if (!ok) ihlCryptoFail();
}

static inline void ihlCryptoSha256(const unsigned char *data, size_t len,
                                 unsigned char *hash) {
    size_t written = 0;
    ihlCryptoCheck(EVP_Q_digest(NULL, "SHA2-256", "fips=yes", data, len,
                               hash, &written) == 1 && written == 32);
}

static inline void ihlCryptoRandom(unsigned char *data, size_t len) {
    ihlCryptoCheck(RAND_bytes_ex(NULL, data, len, 256) == 1);
}

/* Explicit qualification assertions are separate from provider initialization. */
static inline void ihlCryptoValidate(void) {
    ihlCryptoCheck(ihlCryptoFipsProvider != NULL);
    ihlCryptoCheck(OSSL_PROVIDER_self_test(ihlCryptoFipsProvider) == 1);
    ihlCryptoCheck(EVP_default_properties_is_fips_enabled(NULL) == 1);
    EVP_MD *sha256 = EVP_MD_fetch(NULL, "SHA2-256", "fips=yes");
    ihlCryptoCheck(sha256 != NULL);
    ihlCryptoCheck(strcmp(OSSL_PROVIDER_get0_name(EVP_MD_get0_provider(sha256)), "fips") == 0);
    EVP_MD_free(sha256);
    EVP_MD *md5 = EVP_MD_fetch(NULL, "MD5", NULL);
    ihlCryptoCheck(md5 == NULL);
    ERR_clear_error();
    unsigned char random[32];
    ihlCryptoRandom(random, sizeof(random));
    EVP_RAND_CTX *rng = RAND_get0_public(NULL);
    ihlCryptoCheck(rng != NULL);
    ihlCryptoCheck(strcmp(OSSL_PROVIDER_get0_name(
        EVP_RAND_get0_provider(EVP_RAND_CTX_get0_rand(rng))), "fips") == 0);
    OPENSSL_cleanse(random, sizeof(random));
}

static inline void ihlCryptoStartup(void) {
    const char *config = getenv("OPENSSL_CONF");
    const char *modules = getenv("OPENSSL_MODULES");
    ihlCryptoCheck(!config || strcmp(config, IHL_CRYPTO_CONFIG) == 0);
    ihlCryptoCheck(!modules || strcmp(modules, IHL_CRYPTO_MODULES) == 0);
    OPENSSL_INIT_SETTINGS *settings = OPENSSL_INIT_new();
    ihlCryptoCheck(settings != NULL);
    ihlCryptoCheck(OPENSSL_INIT_set_config_filename(settings, IHL_CRYPTO_CONFIG) == 1);
    OPENSSL_INIT_set_config_file_flags(settings, 0);
    ihlCryptoCheck(OPENSSL_init_crypto(OPENSSL_INIT_LOAD_CONFIG, settings) == 1);
    OPENSSL_INIT_free(settings);
    ihlCryptoCheck(OSSL_PROVIDER_set_default_search_path(NULL, IHL_CRYPTO_MODULES) == 1);
    /* Retain provider references for the lifetime of the server. */
    OSSL_PROVIDER *base = OSSL_PROVIDER_load(NULL, "base");
    ihlCryptoFipsProvider = OSSL_PROVIDER_load(NULL, "fips");
    ihlCryptoCheck(base != NULL && ihlCryptoFipsProvider != NULL);
    ihlCryptoCheck(EVP_default_properties_enable_fips(NULL, 1) == 1);
#if IHL_REDIS_FIPS_VALIDATION
    ihlCryptoValidate();
#endif
}
#endif
