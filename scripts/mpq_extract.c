// Extract every file from an MPQ archive (StormLib).
// Build: clang -O2 -I/opt/homebrew/opt/stormlib/include scripts/mpq_extract.c \
//          -L/opt/homebrew/opt/stormlib/lib -lstorm -o build/mpq_extract
// Usage: mpq_extract <archive> <out_dir> [listfile]
#include <StormLib.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>

static void make_parents(char *path) {
    for (char *p = path + 1; *p; p++) {
        if (*p == '/') {
            *p = '\0';
            mkdir(path, 0755);
            *p = '/';
        }
    }
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: %s <archive> <out_dir> [listfile]\n", argv[0]);
        return 2;
    }
    HANDLE mpq;
    if (!SFileOpenArchive(argv[1], 0, STREAM_FLAG_READ_ONLY, &mpq)) {
        fprintf(stderr, "open %s: error %u\n", argv[1], SErrGetLastError());
        return 1;
    }
    if (argc > 3)
        SFileAddListFile(mpq, argv[3]);

    SFILE_FIND_DATA fd;
    HANDLE find = SFileFindFirstFile(mpq, "*", &fd, NULL);
    int ok = 0, failed = 0;
    for (bool more = find != NULL; more; more = SFileFindNextFile(find, &fd)) {
        char out[4096];
        snprintf(out, sizeof out, "%s/%s", argv[2], fd.cFileName);
        for (char *p = out + strlen(argv[2]); *p; p++)
            if (*p == '\\')
                *p = '/';
        make_parents(out);
        if (SFileExtractFile(mpq, fd.cFileName, out, SFILE_OPEN_FROM_MPQ)) {
            ok++;
        } else {
            failed++;
            fprintf(stderr, "extract %s: error %u\n", fd.cFileName, SErrGetLastError());
        }
    }
    if (find)
        SFileFindClose(find);
    SFileCloseArchive(mpq);
    printf("%d extracted, %d failed\n", ok, failed);
    return failed ? 1 : 0;
}
