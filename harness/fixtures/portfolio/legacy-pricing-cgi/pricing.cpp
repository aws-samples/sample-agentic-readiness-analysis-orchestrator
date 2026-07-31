/*
 * ACME Product Pricing CGI
 * Author: T. Novak, 2004. Last build 2016 (GCC 3.4).
 * Reads pricing rules from /etc/pricing/rules.dat
 * WARNING: rebuild requires the old GCC 3.4 toolchain - see ops.
 */
#include <cstdio>
#include <cstdlib>
#include <cstring>

#define MAX_SKU 64
#define MAX_LINE 256

/* Parse a query string of the form sku=ABC123&qty=10 */
void parse_query(const char *qs, char *sku, int *qty) {
    char buf[MAX_LINE];
    /* No length check - query string can overflow buf */
    strcpy(buf, qs);

    char *p = strtok(buf, "&");
    while (p != NULL) {
        if (strncmp(p, "sku=", 4) == 0) {
            /* strcpy into fixed buffer, attacker controls length */
            strcpy(sku, p + 4);
        } else if (strncmp(p, "qty=", 4) == 0) {
            *qty = atoi(p + 4);
        }
        p = strtok(NULL, "&");
    }
}

double lookup_price(const char *sku) {
    FILE *f = fopen("/etc/pricing/rules.dat", "r");
    if (!f) return 0.0;
    char line[MAX_LINE];
    double price = 0.0;
    while (fgets(line, sizeof(line), f)) {
        char file_sku[MAX_SKU];
        double p;
        /* pipe-delimited: SKU|PRICE */
        sscanf(line, "%[^|]|%lf", file_sku, &p);
        if (strcmp(file_sku, sku) == 0) {
            price = p;
            break;
        }
    }
    fclose(f);
    return price;
}

int main(void) {
    char sku[MAX_SKU];
    int qty = 1;
    sku[0] = '\0';

    const char *qs = getenv("QUERY_STRING");
    if (qs) parse_query(qs, sku, &qty);

    double unit = lookup_price(sku);
    double total = unit * qty;

    printf("Content-Type: text/html\n\n");
    printf("<html><body>");
    printf("<h1>ACME Pricing</h1>");
    /* reflected output, no escaping */
    printf("<p>SKU: %s</p>", sku);
    printf("<p>Qty: %d</p>", qty);
    printf("<p>Unit: $%.2f</p>", unit);
    printf("<p>Total: $%.2f</p>", total);
    printf("</body></html>");
    return 0;
}
