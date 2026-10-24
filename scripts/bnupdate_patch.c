// Apply one Warcraft III BNUpdate patch record (a file from Patch_War3x.mpq)
// to the installed file, natively.
// Build: clang -O2 -Wall scripts/bnupdate_patch.c -o build/bnupdate_patch
// Usage: bnupdate_patch <record> <old_file|-> <new_file>
//
// Record layout (little-endian), as decoded from the 1.26a patch:
//   0x00 u16 header size (0x18)   0x02 u8 4   0x03 u8 type
//   0x04 u32 unknown (not a CRC32 of the old or new file)
//   0x08 u32 unknown              0x0C u32 new file size
//   0x10 FILETIME of the new file 0x18 payload
// Type 1: the payload is the whole new file.
// Type 4: u32 unpacked size, then an RLE stream (a byte with bit 7 set copies
// (b & 0x7F) + 1 literal bytes, any other byte emits b + 1 zero bytes) that
// unpacks to a BSDIFF40 blob with uncompressed blocks and 12-byte control
// entries: u32 add length, u32 extra length, u32 old seek (sign-magnitude,
// bit 31 = negative). This is the scheme StormLib applies as "BSD0".
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint8_t *read_file(const char *path, size_t *size) {
    FILE *f = fopen(path, "rb");
    if (!f)
        return NULL;
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    uint8_t *buf = malloc(n ? (size_t)n : 1);
    if (buf && fread(buf, 1, (size_t)n, f) != (size_t)n) {
        free(buf);
        buf = NULL;
    }
    fclose(f);
    *size = (size_t)n;
    return buf;
}

static uint32_t rd32(const uint8_t *p) {
    return p[0] | p[1] << 8 | p[2] << 16 | (uint32_t)p[3] << 24;
}

static uint64_t rd64(const uint8_t *p) {
    return rd32(p) | (uint64_t)rd32(p + 4) << 32;
}

static int fail(const char *msg) {
    fprintf(stderr, "bnupdate_patch: %s\n", msg);
    return 1;
}

// Unpacks the RLE stream; returns 0 if it would overrun either buffer.
static int unrle(const uint8_t *in, size_t in_size, uint8_t *out, size_t out_size) {
    size_t i = 0, o = 0;
    memset(out, 0, out_size);
    while (i < in_size && o < out_size) {
        uint8_t b = in[i++];
        size_t n = (b & 0x7F) + 1u;
        if (b & 0x80) {
            if (n > in_size - i || n > out_size - o)
                return 0;
            memcpy(out + o, in + i, n);
            i += n;
        } else if (n > out_size - o) {
            return 0;
        }
        o += n;
    }
    return 1;
}

static int bsdiff40(const uint8_t *blob, size_t blob_size, const uint8_t *old, size_t old_size,
                    uint8_t *new_data, size_t new_size) {
    if (blob_size < 32 || memcmp(blob, "BSDIFF40", 8) != 0)
        return fail("payload is not BSDIFF40");
    uint64_t ctrl_size = rd64(blob + 8), data_size = rd64(blob + 16);
    if (rd64(blob + 24) != new_size)
        return fail("BSDIFF40 size differs from the record header");
    if (ctrl_size % 12 || ctrl_size > blob_size - 32 || data_size > blob_size - 32 - ctrl_size)
        return fail("BSDIFF40 blocks overrun the payload");
    const uint8_t *ctrl = blob + 32, *ctrl_end = ctrl + ctrl_size;
    const uint8_t *data = ctrl_end, *data_end = data + data_size;
    const uint8_t *extra = data_end, *extra_end = blob + blob_size;
    size_t n_off = 0;
    int64_t o_off = 0;
    while (n_off < new_size) {
        if (ctrl == ctrl_end)
            return fail("control block ends before the new file");
        uint32_t add = rd32(ctrl), copy = rd32(ctrl + 4), seek = rd32(ctrl + 8);
        ctrl += 12;
        if (add > new_size - n_off || add > (size_t)(data_end - data))
            return fail("add run overruns");
        for (uint32_t i = 0; i < add; i++) {
            int64_t o = o_off + i;
            uint8_t base = (o >= 0 && (uint64_t)o < old_size) ? old[o] : 0;
            new_data[n_off + i] = (uint8_t)(data[i] + base);
        }
        data += add;
        n_off += add;
        o_off += add;
        if (copy > new_size - n_off || copy > (size_t)(extra_end - extra))
            return fail("extra run overruns");
        memcpy(new_data + n_off, extra, copy);
        extra += copy;
        n_off += copy;
        o_off += (seek & 0x80000000u) ? -(int64_t)(seek & 0x7FFFFFFFu) : (int64_t)seek;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: %s <record> <old_file|-> <new_file>\n", argv[0]);
        return 2;
    }
    size_t rec_size, old_size = 0;
    uint8_t *rec = read_file(argv[1], &rec_size);
    if (!rec || rec_size < 0x18 || (rec[0] | rec[1] << 8) != 0x18 || rec[2] != 4)
        return fail("not a BNUpdate record");
    uint8_t type = rec[3];
    size_t new_size = rd32(rec + 0x0C);
    const uint8_t *payload = rec + 0x18;
    size_t payload_size = rec_size - 0x18;
    uint8_t *new_data = malloc(new_size ? new_size : 1);
    if (!new_data)
        return fail("out of memory");

    if (type == 1) {
        if (payload_size != new_size)
            return fail("whole-file record has the wrong size");
        memcpy(new_data, payload, new_size);
    } else if (type == 4) {
        uint8_t *old = strcmp(argv[2], "-") ? read_file(argv[2], &old_size) : NULL;
        if (!old)
            return fail("delta record needs the old file");
        if (payload_size < 4)
            return fail("truncated delta record");
        size_t blob_size = rd32(payload);
        uint8_t *blob = malloc(blob_size ? blob_size : 1);
        if (!blob || !unrle(payload + 4, payload_size - 4, blob, blob_size))
            return fail("RLE stream overruns");
        if (bsdiff40(blob, blob_size, old, old_size, new_data, new_size))
            return 1;
    } else {
        return fail("unknown record type");
    }

    FILE *f = fopen(argv[3], "wb");
    if (!f || fwrite(new_data, 1, new_size, f) != new_size || fclose(f))
        return fail("cannot write the new file");
    return 0;
}
