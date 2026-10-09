# Extrator de Fatura Equatorial

API HTTP em Python para extrair dados estruturados de faturas de energia da Equatorial Alagoas em PDF. O arquivo enviado é salvo temporariamente e apagado após o processamento.

## Requisitos

- Python 3.10 ou superior
- `pip`
- PDF com texto selecionável; PDFs digitalizados como imagem precisam de OCR, que esta API não oferece

## Instalação

Na pasta do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

No Windows, ative o ambiente com `.venv\Scripts\activate` e use `py` no lugar de `python3` para criá-lo.

## Execução

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Acesse `http://127.0.0.1:8000/docs` para testar pela interface interativa. Para enviar uma fatura pela linha de comando:

```bash
curl -X POST http://127.0.0.1:8000/extract -F "file=@/caminho/para/fatura.pdf"
```

`GET /` mostra uma breve descrição da API. `POST /extract` recebe o PDF no campo `file` e retorna um objeto JSON. Arquivos sem extensão `.pdf` recebem HTTP 400; arquivos sem texto extraível recebem HTTP 422. Os campos que não forem encontrados retornam `null`.

## Campos retornados

| Campo | Descrição |
| --- | --- |
| `reference_month` | Mês de referência, no formato `AAAA-MM-DD` |
| `previous_reading_date` | Data da leitura anterior |
| `current_reading_date` | Data da leitura atual |
| `reading_days` | Dias entre leituras |
| `next_reading_date` | Data da próxima leitura |
| `due_date` | Data de vencimento |
| `consumption_kwh` | Consumo em kWh |
| `total_amount` | Valor total, como texto decimal com ponto |
| `tariff_flag` | Bandeira tarifária |
| `consumer_unit` | Unidade consumidora |
| `customer_name` | Nome do titular |
| `customer_cpf` | CPF do titular |
| `address` | Endereço |
| `cep` | CEP |
| `neighborhood` | Bairro |
| `city` | Cidade |
| `state` | Estado |
| `invoice_number` | Número da nota fiscal |
| `issue_date` | Data de emissão |

As regras de extração foram feitas para o layout de faturas Equatorial Alagoas usado no desenvolvimento; outros layouts podem exigir ajustes em `main.py`. Faturas e resultados locais estão no `.gitignore` para evitar publicar dados pessoais por acidente.
