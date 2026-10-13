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

## Serviço Linux com systemd

Os arquivos de exemplo estão em [`deploy/equatorial-api.service`](deploy/equatorial-api.service) e [`deploy/equatorial-api.env.example`](deploy/equatorial-api.env.example). Os comandos abaixo partem da pasta deste projeto e exigem `sudo` e Python 3.10 ou superior. Instale `python3-venv` pelo gerenciador de pacotes da distribuição caso a criação do ambiente virtual falhe.

```bash
sudo useradd --system --home-dir /opt/equatorial-api --shell /usr/sbin/nologin equatorial-api
sudo install -d -m 0755 /opt/equatorial-api
sudo install -m 0644 main.py requirements.txt /opt/equatorial-api/
sudo python3 -m venv /opt/equatorial-api/.venv
sudo /opt/equatorial-api/.venv/bin/python -m pip install -r /opt/equatorial-api/requirements.txt
sudo install -m 0644 deploy/equatorial-api.env.example /etc/equatorial-api.env
sudo install -m 0644 deploy/equatorial-api.service /etc/systemd/system/equatorial-api.service
```

Edite `/etc/equatorial-api.env`. Para uso apenas no próprio servidor, mantenha `API_HOST=127.0.0.1`. Para atender outros computadores da rede interna, use **o IPv4 privado atribuído à interface interna do servidor**, por exemplo `API_HOST=192.168.1.10`. Consulte as interfaces com `ip -4 addr show`. Não use `0.0.0.0`: isso faria o serviço escutar em todas as interfaces IPv4.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now equatorial-api
sudo systemctl status equatorial-api
sudo journalctl -u equatorial-api -f
```

Ao alterar `/etc/equatorial-api.env`, reinicie com `sudo systemctl restart equatorial-api`. Para atualizar o código, copie `main.py` novamente para `/opt/equatorial-api/` e reinicie o serviço; se `requirements.txt` mudar, reinstale as dependências no ambiente virtual antes de reiniciar.

Confirme o endereço em que o processo escuta com `ss -ltnp | grep ':8000'`. Teste no servidor com `curl http://127.0.0.1:8000/` quando estiver configurado para loopback, ou com `curl http://192.168.1.10:8000/` após trocar pelo IP interno. Nesse último caso, teste também de outro computador da LAN.

**Restrição de rede:** escutar no IP privado limita a interface usada, mas não restringe quais redes roteadas conseguem chegar a ela. Configure o firewall do servidor para permitir a porta somente da sub-rede interna desejada e revise regras existentes que já abram essa porta. Por exemplo, com UFW, interface interna `eth0`, servidor `192.168.1.10` e LAN `192.168.1.0/24`:

```bash
sudo ufw allow in on eth0 from 192.168.1.0/24 to 192.168.1.10 port 8000 proto tcp
sudo ufw status numbered
```

Adapte interface, IP, sub-rede e porta ao servidor. Garanta também que a política de entrada ou uma regra específica negue a porta 8000 às demais origens; uma regra `allow` isolada não faz isso quando a política padrão permite conexões. Confira com `sudo ufw status verbose`. Se o UFW ainda não estiver ativo, confira primeiro as regras necessárias para SSH e outros serviços antes de habilitá-lo. A API usa HTTP sem autenticação; execute-a somente numa rede interna confiável ou coloque autenticação e TLS em um proxy interno.

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
