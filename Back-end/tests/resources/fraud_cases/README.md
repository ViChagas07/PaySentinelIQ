# Golden set sintÃ©tico â€” PaySentinelIQ

Documentos 100% fictÃ­cios, gerados por `app/synthetic`.
Cada item possui a variante `native`; itens legÃ­timos possuem tambÃ©m `scanned_clean` ou `scanned_rot`.

| ID | Tipo | Idioma | Layout | AdulteraÃ§Ã£o | Esperado | Banda |
|---|---|---|---|---|---|---|
| syn-2026-00000 | boleto | pt | A | nenhuma | nenhum | LOW |
| syn-2026-00001 | boleto | es | B | nenhuma | nenhum | LOW |
| syn-2026-00002 | boleto | en | C | nenhuma | nenhum | LOW |
| syn-2026-00003 | boleto | pt | A | nenhuma | nenhum | LOW |
| syn-2026-00004 | boleto | es | B | nenhuma | nenhum | LOW |
| syn-2026-00005 | boleto | en | C | nenhuma | nenhum | LOW |
| syn-2026-00006 | boleto | pt | A | nenhuma | nenhum | LOW |
| syn-2026-00007 | boleto | es | B | nenhuma | nenhum | LOW |
| syn-2026-00008 | boleto | en | C | nenhuma | nenhum | LOW |
| syn-2026-00009 | contracheque | pt | A | nenhuma | nenhum | LOW |
| syn-2026-00010 | contracheque | es | B | nenhuma | nenhum | LOW |
| syn-2026-00011 | contracheque | en | C | nenhuma | nenhum | LOW |
| syn-2026-00012 | contracheque | pt | A | nenhuma | nenhum | LOW |
| syn-2026-00013 | contracheque | es | B | nenhuma | nenhum | LOW |
| syn-2026-00014 | contracheque | en | C | nenhuma | nenhum | LOW |
| syn-2026-00015 | contracheque | pt | A | nenhuma | nenhum | LOW |
| syn-2026-00016 | contracheque | es | B | nenhuma | nenhum | LOW |
| syn-2026-00017 | contracheque | en | C | nenhuma | nenhum | LOW |
| syn-2026-00200 | boleto | pt | A | nenhuma | nenhum | LOW |
| syn-2026-00201 | boleto | es | B | nenhuma | nenhum | LOW |
| syn-2026-00202 | boleto | en | C | nenhuma | nenhum | LOW |
| syn-2026-00203 | boleto | pt | A | nenhuma | nenhum | LOW |
| syn-2026-00204 | boleto | pt | B | nenhuma | nenhum | LOW |
| syn-2026-00205 | boleto | es | C | nenhuma | nenhum | LOW |
| syn-2026-00100 | boleto | pt | A | B1 | BOLETO_AMOUNT_MISMATCH | HIGH |
| syn-2026-00101 | boleto | es | B | B2 | BOLETO_DUE_DATE_MISMATCH | HIGH |
| syn-2026-00102 | boleto | en | C | B3 | BANCO_INVALIDO, BOLETO_BANK_MISMATCH | HIGH |
| syn-2026-00103 | boleto | pt | A | B4 | BOLETO_GENERAL_DV_INVALID | HIGH |
| syn-2026-00104 | boleto | es | B | B5 | BOLETO_AMOUNT_MISMATCH, BOLETO_GENERAL_DV_INVALID | HIGH |
| syn-2026-00105 | boleto | en | C | B6 | nenhum | LOW |
| syn-2026-00106 | boleto | pt | A | B7 | nenhum | LOW |
| syn-2026-00107 | boleto | es | B | B8 | BOLETO_AMOUNT_MISMATCH | HIGH |
| syn-2026-00108 | contracheque | en | C | P1 | PAYSLIP_NET_MISMATCH | HIGH |
| syn-2026-00109 | contracheque | pt | A | P2 | PAYSLIP_INSS_MISMATCH | HIGH |
| syn-2026-00110 | contracheque | es | B | P3 | PAYSLIP_IRRF_MISMATCH | HIGH |
| syn-2026-00111 | contracheque | en | C | P4 | nenhum | LOW |
| syn-2026-00112 | contracheque | pt | A | P5 | PAYSLIP_CPF_INVALID | HIGH |
| syn-2026-00113 | contracheque | es | B | P6 | PAYSLIP_PERIOD_FUTURE | HIGH |
| syn-2026-00114 | contracheque | en | C | P7 | PAYSLIP_FGTS_MISMATCH | MEDIUM |
| syn-2026-00115 | contracheque | pt | A | P8 | PAYSLIP_DEDUCTIONS_INCONSISTENT | HIGH |
| syn-2026-00116 | contracheque | es | B | P9 | PAYSLIP_NET_MISMATCH | HIGH |
| syn-2026-00117 | boleto | en | C | B1, B2 | BOLETO_AMOUNT_MISMATCH, BOLETO_DUE_DATE_MISMATCH | HIGH |

Arquivos em `legitimate/` e `fraudulent/`; hashes em `manifest.json`.
