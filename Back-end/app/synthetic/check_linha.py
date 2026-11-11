from __future__ import annotations

import sys

from app.services.validation.febraban import decode_linha_digitavel


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: python -m app.synthetic.check_linha <linha_digitavel>")
        raise SystemExit(2)
    linha = sys.argv[1]
    decoded = decode_linha_digitavel(linha)
    print(f"status: {decoded.get('status')}")
    print(f"banco: {decoded.get('banco', '')}")
    print(f"moeda: {decoded.get('moeda', '')}")
    dvs = decoded.get("campo_dvs_validos")
    if isinstance(dvs, dict):
        print(f"dv_campo1: {'ok' if dvs.get('campo1') else 'invalido'}")
        print(f"dv_campo2: {'ok' if dvs.get('campo2') else 'invalido'}")
        print(f"dv_campo3: {'ok' if dvs.get('campo3') else 'invalido'}")
    print(f"dv_geral: {decoded.get('dv_geral', '')}")
    print(
        "dv_geral_valido: "
        f"{'sim' if decoded.get('dv_geral_valido') else 'nao'}"
    )
    print(f"fator: {decoded.get('fator', '')}")
    print(f"vencimento: {decoded.get('vencimento') or 'sem vencimento'}")
    print(f"valor: {decoded.get('valor', '')}")
    print(f"codigo_barras: {decoded.get('codigo_barras', '')}")


if __name__ == "__main__":
    main()
