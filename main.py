from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
import re
from datetime import datetime
import pymupdf

app = FastAPI(title="Extrator de Fatura Equatorial", version="1.0")


def extrair_texto_pdf(caminho_pdf: str) -> str:
    """Extrai todo o texto de um PDF usando PyMuPDF"""
    doc = pymupdf.open(caminho_pdf)
    texto = ""
    for pagina in doc:
        texto += pagina.get_text() + "\n"
    doc.close()
    return texto


def parse_equatorial_bill(texto: str) -> dict:
    def extrair(padrao, texto, grupo=1, default=None):
        match = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)
        if not match:
            return default
        try:
            valor = match.group(grupo)
            return valor.strip() if valor else default
        except IndexError:
            return match.group(0).strip() if match.group(0) else default

    def para_data(data_str):
        if not data_str:
            return None
        data_str = data_str.replace(".", "/")
        try:
            return datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        except:
            return None

    # Nome do cliente
    customer_name = extrair(r"([A-ZÁÉÍÓÚÃÕÂÊÎÔÛÇ ]{8,60})\s*\n\s*CPF:", texto)

    # CPF
    customer_cpf = extrair(r"(\d{3}\.\d{3}\.\d{3}-\d{2})", texto)
    if not customer_cpf:
        customer_cpf = extrair(r"CPF:\s*([\d\.\*\-]+)", texto)

    # Endereço
    address = extrair(r"(R\.\s*[^\n]+)", texto)

    # CEP + Localização
    cep = extrair(r"CEP:\s*(\d{5}-\d{3})", texto)
    neighborhood = city = state = None
    partes = re.findall(
        r"CEP:\s*\d{5}-\d{3}\s*-\s*([^-]+)\s*-\s*([^-]+)\s*-\s*([A-Z]{2})",
        texto
    )
    if partes:
        neighborhood, city, state = [p.strip() for p in partes[0]]

    # Datas de leitura
    previous_reading_date = extrair(
        r"(\d{2}/\d{2}/\d{4})\s*\n\s*\d{2}/\d{2}/\d{4}\s*\n\s*\d+", texto
    )
    current_reading_date = extrair(
        r"\d{2}/\d{2}/\d{4}\s*\n\s*(\d{2}/\d{2}/\d{4})\s*\n\s*\d+", texto
    )
    next_reading_date = extrair(
        r"\d{2}/\d{2}/\d{4}\s*\n\s*\d{2}/\d{2}/\d{4}\s*\n\s*\d+\s*\n\s*(\d{2}/\d{2}/\d{4})",
        texto
    )

    reading_days = extrair(
        r"\d{2}/\d{2}/\d{4}\s*\n\s*\d{2}/\d{2}/\d{4}\s*\n\s*(\d+)", texto
    )

    consumption_kwh = extrair(r"(\d+)\s*kWh", texto)
    tariff_flag = extrair(r"Band\.?\s*Tarif\.?:\s*(\w+)", texto)

    total_amount = extrair(r"R\$\s*([\d\.,]+)", texto)
    if total_amount:
        total_amount = total_amount.replace(".", "").replace(",", ".")

    due_date = extrair(r"(\d{2}\.\d{2}\.\d{4})", texto) or extrair(
        r"VENCIMENTO.*?(\d{2}[./]\d{2}[./]\d{4})", texto
    )

    consumer_unit = extrair(r"(\d{1,2}\.\d{3}\.\d{3}\.\d{3}-\d{2})", texto)

    reference = extrair(r"(\d{2}/\d{4})", texto)
    reference_month = None
    if reference:
        mes, ano = reference.split("/")
        reference_month = f"{ano}-{mes}-01"

    invoice_number = extrair(r"NOTA FISCAL Nº\s*(\d+)", texto)
    issue_date = extrair(r"DATA DE EMISSÃO:\s*(\d{2}/\d{2}/\d{4})", texto)

    return {
        "reference_month": reference_month,
        "previous_reading_date": para_data(previous_reading_date),
        "current_reading_date": para_data(current_reading_date),
        "reading_days": int(reading_days) if reading_days and reading_days.isdigit() else None,
        "next_reading_date": para_data(next_reading_date),
        "due_date": para_data(due_date),
        "consumption_kwh": consumption_kwh,
        "total_amount": total_amount,
        "tariff_flag": tariff_flag,
        "consumer_unit": consumer_unit,
        "customer_name": customer_name,
        "customer_cpf": customer_cpf,
        "address": address,
        "cep": cep,
        "neighborhood": neighborhood,
        "city": city,
        "state": state,
        "invoice_number": invoice_number,
        "issue_date": para_data(issue_date),
    }


@app.post("/extract")
async def extract_bill(file: UploadFile = File(...)):
    # Valida se é PDF
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="O arquivo deve ser um PDF")

    temp_path = None
    try:
        # Cria arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            temp_path = tmp.name

        # Extrai texto do PDF
        texto = extrair_texto_pdf(temp_path)

        if not texto.strip():
            raise HTTPException(status_code=422, detail="Não foi possível extrair texto do PDF")

        # Faz o parsing
        dados = parse_equatorial_bill(texto)

        return JSONResponse(content=dados)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar o arquivo: {str(e)}")

    finally:
        # Sempre apaga o arquivo temporário
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/")
def root():
    return {
        "message": "API de Extração de Fatura Equatorial",
        "endpoint": "POST /extract",
        "exemplo": "Envie um arquivo PDF no campo 'file'"
    }
