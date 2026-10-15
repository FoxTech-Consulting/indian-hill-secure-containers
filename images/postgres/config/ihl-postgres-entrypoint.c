/*
 * Minimal rootless PostgreSQL bootstrapper.
 *
 * The delivered image retains the minimal POSIX shell required by upstream
 * initdb during first-run initialization. This small launcher creates a
 * checksum-enabled cluster only when PGDATA is empty, then execs postgres
 * against the immutable reviewed configuration. Production deployments must
 * provide credentials through POSTGRES_PASSWORD_FILE; POSTGRES_PASSWORD is
 * retained only for isolated candidate-pipeline testing.
 */
#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#define PG_BIN "/opt/postgresql/bin"
#define PG_CONFIG "/opt/ihl/postgresql/postgresql.conf"

static void fail(const char *message) {
    perror(message);
    exit(1);
}

static const char *required_env(const char *name) {
    const char *value = getenv(name);
    if (value == NULL || value[0] == '\0') {
        fprintf(stderr, "ERROR: %s is required when initializing PGDATA.\n", name);
        exit(2);
    }
    return value;
}

static int initialized(const char *pgdata) {
    char version[PATH_MAX];
    if (snprintf(version, sizeof(version), "%s/PG_VERSION", pgdata) >= (int)sizeof(version)) {
        fprintf(stderr, "ERROR: PGDATA path is too long.\n");
        exit(2);
    }
    return access(version, R_OK) == 0;
}

static void ensure_directory(const char *path) {
    struct stat info;
    if (mkdir(path, 0700) != 0 && errno != EEXIST) {
        fail("mkdir PGDATA");
    }
    if (chmod(path, 0700) != 0) {
        fail("chmod PGDATA");
    }
    if (stat(path, &info) != 0) {
        fail("stat PGDATA");
    }
    if (!S_ISDIR(info.st_mode) || (info.st_mode & 0077) != 0) {
        fprintf(stderr, "ERROR: PGDATA must be a directory with mode 0700.\n");
        exit(2);
    }
}

static const char *password_file(void) {
    const char *file = getenv("POSTGRES_PASSWORD_FILE");
    if (file != NULL && file[0] != '\0') {
        if (access(file, R_OK) != 0) {
            fail("POSTGRES_PASSWORD_FILE");
        }
        return file;
    }
    const char *password = getenv("POSTGRES_PASSWORD");
    if (password == NULL || password[0] == '\0') {
        fprintf(stderr, "ERROR: POSTGRES_PASSWORD_FILE is required for deployment.\n");
        fprintf(stderr, "POSTGRES_PASSWORD is permitted only for the isolated candidate test.\n");
        exit(2);
    }
    const char *temporary = "/tmp/ihl-postgres-initdb-password";
    int descriptor = open(temporary, O_WRONLY | O_CREAT | O_TRUNC, 0600);
    if (descriptor < 0) {
        fail("create candidate password file");
    }
    size_t remaining = strlen(password);
    const char *cursor = password;
    while (remaining > 0) {
        ssize_t written = write(descriptor, cursor, remaining);
        if (written < 0) {
            close(descriptor);
            fail("write candidate password file");
        }
        cursor += written;
        remaining -= (size_t)written;
    }
    if (write(descriptor, "\n", 1) != 1 || close(descriptor) != 0) {
        fail("finalize candidate password file");
    }
    return temporary;
}

static void initialize_cluster(const char *pgdata) {
    const char *username = getenv("POSTGRES_USER");
    if (username == NULL || username[0] == '\0') {
        username = "postgres";
    }
    const char *database = getenv("POSTGRES_DB");
    (void)database; /* Database creation belongs to the deployment bootstrap job. */
    const char *pwfile = password_file();
    pid_t child = fork();
    if (child < 0) {
        fail("fork initdb");
    }
    if (child == 0) {
        char pgdata_arg[PATH_MAX + 16];
        char user_arg[256];
        snprintf(pgdata_arg, sizeof(pgdata_arg), "--pgdata=%s", pgdata);
        snprintf(user_arg, sizeof(user_arg), "--username=%s", username);
        char pwfile_arg[PATH_MAX + 32];
        snprintf(pwfile_arg, sizeof(pwfile_arg), "--pwfile=%s", pwfile);
        char *const args[] = {
            PG_BIN "/initdb", pgdata_arg, user_arg, pwfile_arg,
            "--auth-host=scram-sha-256", "--auth-local=peer", "--encoding=UTF8",
            "--data-checksums", "--no-locale", "--no-instructions", NULL
        };
        execv(args[0], args);
        fail("exec initdb");
    }
    int status = 0;
    if (waitpid(child, &status, 0) < 0) {
        fail("wait initdb");
    }
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) {
        fprintf(stderr, "ERROR: initdb did not complete successfully.\n");
        exit(1);
    }
    if (strcmp(pwfile, "/tmp/ihl-postgres-initdb-password") == 0) {
        if (unlink(pwfile) != 0) {
            fail("remove candidate password file");
        }
    }
}

int main(int argc, char **argv) {
    const char *pgdata = getenv("PGDATA");
    if (pgdata == NULL || pgdata[0] == '\0') {
        pgdata = "/var/lib/postgresql/data";
    }
    ensure_directory(pgdata);
    if (!initialized(pgdata)) {
        initialize_cluster(pgdata);
    }
    char data_arg[PATH_MAX + 4];
    snprintf(data_arg, sizeof(data_arg), "-D%s", pgdata);
    char config_arg[] = "config_file=" PG_CONFIG;
    size_t forwarded = argc > 1 ? (size_t)argc - 1 : 0;
    char **command = calloc(forwarded + 6, sizeof(char *));
    if (command == NULL) {
        fail("allocate postgres command");
    }
    command[0] = PG_BIN "/postgres";
    command[1] = data_arg;
    command[2] = "-c";
    command[3] = config_arg;
    for (size_t index = 0; index < forwarded; index++) {
        command[index + 4] = argv[index + 1];
    }
    execv(command[0], command);
    fail("exec postgres");
}
