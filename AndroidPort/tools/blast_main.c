/* Harness: decompress a DCL-implode file using the reference blast.c. */
#include <stdio.h>
#include <stdlib.h>
#include "blast.h"

static FILE *g_in;
static unsigned char g_buf[16384];
static unsigned g_len;

static unsigned char *g_out;
static size_t g_outlen, g_outcap;

static unsigned infun(void *how, unsigned char **buf)
{
    (void)how;
    *buf = g_buf;
    if (g_len == 0)
        g_len = fread(g_buf, 1, sizeof(g_buf), g_in);
    unsigned n = g_len;
    g_len = 0;
    return n;
}

static int outfun(void *how, unsigned char *buf, unsigned len)
{
    (void)how;
    if (g_outlen + len > g_outcap) {
        g_outcap = (g_outlen + len) * 2;
        g_out = realloc(g_out, g_outcap);
    }
    memcpy(g_out + g_outlen, buf, len);
    g_outlen += len;
    return 0;
}

int main(int argc, char **argv)
{
    if (argc < 3) {
        fprintf(stderr, "usage: blast_main <in> <out> [expected]\n");
        return 2;
    }
    g_in = fopen(argv[1], "rb");
    if (!g_in) { perror("open"); return 2; }
    unsigned left = 0;
    unsigned char *inptr = NULL;
    if (argc > 3) {
        /* prefill: not needed here */
    }
    int err = blast(infun, NULL, outfun, NULL, &left, &inptr);
    FILE *fo = fopen(argv[2], "wb");
    fwrite(g_out, 1, g_outlen, fo);
    fclose(fo);
    fprintf(stderr, "blast err=%d wrote %zu bytes\n", err, g_outlen);
    return err ? 1 : 0;
}
