import os
import time
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import fitz
import httpx
import pytest
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.services.extraction.boleto_extractor import extract_boleto_fields
from app.services.extraction.payslip_extractor import extract_payslip_fields
from app.services.extraction.text_utils import fold
from app.services.ocr.remote_provider import RemoteOCRProvider

pytestmark = pytest.mark.ocr

BOLETO_PT = [
    "Beneficiário: ACME SERVIÇOS LTDA",
    "CNPJ: 12.345.678/0001-90",
    "Pagador: JOÃO DA SILVA",
    "Data de Vencimento: 20/01/2026",
    "Valor do Documento: R$ 1.234,56",
    "Nosso Número: 12345678901",
    "Nº do Documento: 98765",
    "Código do Banco: 001",
    "Linha Digitável: 00190.00009 01234.567008 12345.678901 2 34560000123456",
]

BOLETO_ES = [
    "Beneficiario: SERVICIOS ANDINOS S.A.",
    "CNPJ: 12.345.678/0001-90",
    "Pagador: JUAN PEREZ",
    "Fecha de vencimiento: 20/01/2026",
    "Valor del documento: R$ 1.234,56",
    "Nuestro número: 12345678901",
    "Número del documento: 98765",
    "Código del banco: 001",
    "Línea digitable: 00190.00009 01234.567008 12345.678901 2 34560000123456",
]

BOLETO_EN = [
    "Beneficiary: ANDEAN SERVICES INC.",
    "CNPJ: 12.345.678/0001-90",
    "Payer: JOHN DOE",
    "Due Date: 20/01/2026",
    "Document Amount: 1,234.56",
    "Our Number: 12345678901",
    "Document Number: 98765",
    "Bank Code: 001",
    "Digitable Line: 00190.00009 01234.567008 12345.678901 2 34560000123456",
]

PAYSLIP_PT = [
    "Empregador: ACME S.A.",
    "CNPJ: 12.345.678/0001-90",
    "Funcionário: Maria Silva",
    "CPF: 123.456.789-09",
    "Cargo: Analista",
    "CBO: 411005",
    "Competência: 01/2026",
    "Admissão: 15/03/2020",
    "Salário Base: 3.000,00",
    "0010 INSS 11,00 330,00",
    "0020 IRRF 137,45",
    "0030 FGTS 240,00",
    "Total de Proventos: 5.000,00",
    "Total de Descontos: 707,45",
    "Líquido a Receber: 4.292,55",
    "Base de Cálculo INSS: 3.000,00",
    "Base IRRF: 2.670,00",
    "Base FGTS: 3.000,00",
    "Dependentes: 2",
]

PAYSLIP_ES = [
    "Empleador: ANDES S.A.",
    "CNPJ: 12.345.678/0001-90",
    "Trabajador: JUAN PEREZ",
    "CPF: 123.456.789-09",
    "Cargo: Analista",
    "CBO: 411005",
    "Período: 01/2026",
    "Fecha de ingreso: 15/03/2020",
    "Salario base: 3.000,00",
    "0010 INSS 11,00 330,00",
    "0020 IRRF 137,45",
    "0030 FGTS 240,00",
    "Total haberes: 5.000,00",
    "Total descuentos: 707,45",
    "Neto a pagar: 4.292,55",
    "Base de cálculo INSS: 3.000,00",
    "Base IRRF: 2.670,00",
    "Base FGTS: 3.000,00",
    "Dependientes: 2",
]

PAYSLIP_EN = [
    "Employer: ACME INC.",
    "CNPJ: 12.345.678/0001-90",
    "Employee: MARY SMITH",
    "CPF: 123.456.789-09",
    "Position: Analyst",
    "CBO: 411005",
    "Pay Period: 01/2026",
    "Hire Date: 15/03/2020",
    "Base Salary: 3,000.00",
    "0010 INSS 11.00 330.00",
    "0020 IRRF 137.45",
    "0030 FGTS 240.00",
    "Total Earnings: 5,000.00",
    "Total Deductions: 707.45",
    "Net Pay: 4,292.55",
    "INSS Base: 3,000.00",
    "IRRF Base: 2,670.00",
    "FGTS Base: 3,000.00",
    "Dependents: 2",
]

BOLETO_CASES = {
    "pt": (BOLETO_PT, "ACME SERVIÇOS LTDA"),
    "es": (BOLETO_ES, "SERVICIOS ANDINOS S.A."),
    "en": (BOLETO_EN, "ANDEAN SERVICES INC."),
}

PAYSLIP_CASES = {
    "pt": (PAYSLIP_PT, "Maria Silva"),
    "es": (PAYSLIP_ES, "JUAN PEREZ"),
    "en": (PAYSLIP_EN, "MARY SMITH"),
}


def _font() -> ImageFont.FreeTypeFont:
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\calibri.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), 32)
    pytest.skip("No TrueType font available")


def _render(lines: list[str]) -> Image.Image:
    font = _font()
    line_height = 52
    width = 2000
    height = 80 + line_height * len(lines)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    y = 30
    for line in lines:
        draw.text((50, y), line, fill="black", font=font)
        y += line_height
    return image


def _variant(image: Image.Image, name: str) -> Image.Image:
    if name == "clean":
        return image
    if name == "rotated":
        return image.rotate(2, expand=True, fillcolor="white")
    return image.filter(ImageFilter.GaussianBlur(1))


def _image_bytes(image: Image.Image, name: str) -> tuple[bytes, str]:
    buffer = BytesIO()
    if name == "blur":
        image.save(buffer, format="JPEG", quality=40)
        return buffer.getvalue(), ".jpg"
    image.save(buffer, format="PNG")
    return buffer.getvalue(), ".png"


def _pdf_bytes(image: Image.Image, name: str) -> bytes:
    image_data, _suffix = _image_bytes(image, name)
    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_image(
        fitz.Rect(20, 20, 575, 822),
        stream=image_data,
        keep_proportion=True,
    )
    data = document.tobytes()
    document.close()
    return data


def _digits(value) -> str:
    if value is None:
        return ""
    return "".join(char for char in str(value) if char.isdigit())


def _compare_boleto(fields, expected_beneficiary: str) -> dict[str, bool]:
    return {
        "linha_digitavel": _digits(
            getattr(fields.linha_digitavel, "value", "")
        )
        == "00190000090123456700812345678901234560000123456",
        "cnpj": _digits(getattr(fields.cnpj, "value", ""))
        == "12345678000190",
        "valor_nominal": getattr(fields.valor_nominal, "value", None)
        == Decimal("1234.56"),
        "data_vencimento": fields.data_vencimento is not None
        and str(fields.data_vencimento.value).startswith("2026-01-20"),
        "beneficiario": fold(
            str(getattr(fields.beneficiario, "value", ""))
        )
        == fold(expected_beneficiary),
        "codigo_banco": _digits(
            getattr(fields.codigo_banco, "value", "")
        )
        == "001",
    }


def _compare_payslip(fields, expected_name: str) -> dict[str, bool]:
    return {
        "cnpj": _digits(getattr(fields.cnpj, "value", ""))
        == "12345678000190",
        "cpf": _digits(getattr(fields.cpf, "value", "")) == "12345678909",
        "salario_bruto": getattr(fields.salario_bruto, "value", None)
        == Decimal("5000.00"),
        "total_descontos": getattr(fields.total_descontos, "value", None)
        == Decimal("707.45"),
        "salario_liquido": getattr(fields.salario_liquido, "value", None)
        == Decimal("4292.55"),
        "inss": getattr(fields.inss, "value", None) == Decimal("330.00"),
        "irrf": getattr(fields.irrf, "value", None) == Decimal("137.45"),
        "fgts": getattr(fields.fgts, "value", None) == Decimal("240.00"),
        "periodo": str(getattr(fields.periodo, "value", "")) == "01/2026",
        "nome_funcionario": fold(
            str(getattr(fields.nome_funcionario, "value", ""))
        )
        == fold(expected_name),
    }


def _ready(url: str) -> bool:
    try:
        response = httpx.get(f"{url}/ready", timeout=3.0)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


@pytest.mark.asyncio
async def test_real_ocr_extraction_accuracy(tmp_path):
    service_url = os.getenv("OCR_SERVICE_URL")
    if not service_url:
        pytest.skip("OCR_SERVICE_URL not set")
    if not _ready(service_url):
        pytest.skip(f"OCR service not ready at {service_url}")

    api_key = os.getenv("OCR_SERVICE_API_KEY")
    engines = ("paddle", "tesseract")
    variants = ("clean", "rotated", "blur")
    results: dict[tuple[str, str], dict[str, int]] = {}
    times: dict[tuple[str, str], list[float]] = {}
    errors: list[str] = []

    for engine in engines:
        provider = RemoteOCRProvider(
            url=service_url,
            timeout=300,
            api_key=api_key,
            engine=engine,
        )
        for variant in variants:
            results[(engine, variant)] = {
                "digits_hits": 0,
                "digits_total": 0,
                "text_hits": 0,
                "text_total": 0,
            }
            times[(engine, variant)] = []

            for language, (lines, expected_name) in BOLETO_CASES.items():
                image = _variant(_render(lines), variant)
                image_data, image_suffix = _image_bytes(image, variant)
                for kind, data, suffix in [
                    ("image", image_data, image_suffix),
                    ("pdf", _pdf_bytes(image, variant), ".pdf"),
                ]:
                    path = tmp_path / f"boleto_{language}_{variant}_{kind}{suffix}"
                    path.write_bytes(data)
                    started = time.perf_counter()
                    try:
                        result = await provider.extract_text(str(path))
                        fields = extract_boleto_fields(result.text)
                        checks = _compare_boleto(fields, expected_name)
                    except Exception as exc:
                        errors.append(
                            f"{engine}/{variant}/boleto/{language}/{kind}:"
                            f"{type(exc).__name__}"
                        )
                        checks = {}
                    times[(engine, variant)].append(time.perf_counter() - started)
                    for name, ok in checks.items():
                        category = "text" if name == "beneficiario" else "digits"
                        results[(engine, variant)][f"{category}_total"] += 1
                        if ok:
                            results[(engine, variant)][f"{category}_hits"] += 1

            for language, (lines, expected_name) in PAYSLIP_CASES.items():
                image = _variant(_render(lines), variant)
                image_data, image_suffix = _image_bytes(image, variant)
                for kind, data, suffix in [
                    ("image", image_data, image_suffix),
                    ("pdf", _pdf_bytes(image, variant), ".pdf"),
                ]:
                    path = tmp_path / f"payslip_{language}_{variant}_{kind}{suffix}"
                    path.write_bytes(data)
                    started = time.perf_counter()
                    try:
                        result = await provider.extract_text(str(path))
                        fields = extract_payslip_fields(result.text)
                        checks = _compare_payslip(fields, expected_name)
                    except Exception as exc:
                        errors.append(
                            f"{engine}/{variant}/payslip/{language}/{kind}:"
                            f"{type(exc).__name__}"
                        )
                        checks = {}
                    times[(engine, variant)].append(time.perf_counter() - started)
                    for name, ok in checks.items():
                        category = "text" if name == "nome_funcionario" else "digits"
                        results[(engine, variant)][f"{category}_total"] += 1
                        if ok:
                            results[(engine, variant)][f"{category}_hits"] += 1

    print("\nengine variant digits text avg_ocr_s")
    for key, counts in results.items():
        average = sum(times[key]) / len(times[key]) if times[key] else 0.0
        print(
            f"{key[0]:9s} {key[1]:7s} "
            f"{counts['digits_hits']}/{counts['digits_total']} "
            f"{counts['text_hits']}/{counts['text_total']} "
            f"{average:.3f}"
        )
    if errors:
        print("errors:")
        for error in errors:
            print(f"  {error}")
