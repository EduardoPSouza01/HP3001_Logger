# HP3001 Logger

Sistema de **monitoramento e registro de temperatura e umidade** para o termohigrômetro
**Impac HP3001** (conexão USB). Lê o equipamento automaticamente, grava cada leitura em banco de
dados, mostra tudo em um painel web e exporta para **Excel** para fins de **auditoria**.

Desenvolvido por **Eduardo Souza**.

---

## Instalação rápida (usuário final)

Para quem só quer **usar** o programa, sem mexer em código.

**Requisitos:** Windows 10 ou 11 (64 bits) e o termohigrômetro Impac HP3001 com cabo USB. Não é
preciso instalar Python nem nenhum outro programa.

### Passo a passo

1. **Baixe o instalador** `HP3001-Setup.exe` na página
   [**Releases**](../../releases) deste repositório (aba *Releases*, em *Assets*).
2. **Conecte o HP3001** ao computador pelo cabo USB.
3. **Execute o `HP3001-Setup.exe`.**
   - Se o Windows mostrar *"O Windows protegeu o computador"* (SmartScreen), clique em
     **Mais informações → Executar assim mesmo**. O aviso aparece porque o programa não tem
     assinatura digital paga; o código-fonte está todo neste repositório.
   - Não pede senha de administrador.
4. Siga o assistente (**Avançar**) e marque, se quiser:
   - **Criar atalho na Área de Trabalho**
   - **Iniciar a coleta automaticamente com o Windows (em segundo plano)**
5. Na última tela, deixe marcado **Abrir o HP3001 Logger agora** e clique em **Concluir**.

### Usando o programa

- Abre uma janela com o **Painel**. As leituras começam a ser gravadas sozinhas.
- Telas: **Painel** (gráficos), **Histórico** (consulta e **Exportar Excel**), **Configurações**
  (intervalo de coleta) e **Sobre**.
- **Fechar a janela não para a coleta.** O programa continua em segundo plano, com um ícone na
  **bandeja do Windows** (seta `^` ao lado do relógio).
- Clique com o botão direito nesse ícone para **Abrir painel**, ligar/desligar **Iniciar com o
  Windows** ou **Sair (para a coleta)**.
- Para abrir de novo depois, use o atalho da Área de Trabalho ou o Menu Iniciar → *HP3001 Logger*.

### Onde ficam os dados

Na pasta de instalação (por padrão `C:\Users\<seu usuário>\AppData\Local\Programs\HP3001`):

| Arquivo | O que é |
|---|---|
| `hp3001.db` | Banco com todas as leituras (para auditoria) |
| `config.ini` | Configuração (nome do equipamento, canais, banco) |
| `settings.json` | Intervalo de coleta escolhido na tela *Configurações* |
| `hp3001.log` | Registro de eventos e erros |

Faça cópia de segurança do `hp3001.db` periodicamente.

### Atualizar para uma versão nova

Feche o programa (bandeja → **Sair**) e execute o novo `HP3001-Setup.exe`. Os dados e a
configuração **não são apagados**. Observação: o `config.ini` existente é mantido, então novidades
do `config.ini` padrão (como novos canais) precisam ser editadas à mão.

### Desinstalar

*Configurações do Windows → Aplicativos → HP3001 Logger → Desinstalar.* O banco e as configurações
são **mantidos** na pasta de instalação (são dados de auditoria); apague a pasta manualmente se
quiser remover tudo.

### Ajustes comuns

- **Nomear canais** (ex.: `2 = Estoque`): edite o `[channels]` do `config.ini`, na pasta de
  instalação, e reinicie o programa (bandeja → **Sair** e abra de novo).
- **Trocar o intervalo de coleta:** tela *Configurações*, sem reiniciar.
- **Não aparece leitura / "Erro de leitura":** confira o cabo USB e se não há outro programa
  usando o equipamento. Mais dicas na seção [Solução de problemas](#16-solução-de-problemas).

### Para quem publica o projeto: como disponibilizar o instalador

O `HP3001-Setup.exe` **não vai no código** (a pasta `installer_out/` está no `.gitignore`). Gere
com `.\build_installer.bat` e publique como arquivo de release:

1. No GitHub: **Releases → Draft a new release**.
2. Crie uma tag (ex.: `v1.0.0`) e um título.
3. Arraste `installer_out\HP3001-Setup.exe` para a área de *Assets* e clique em **Publish release**.

---

## Sumário

0. [Instalação rápida (usuário final)](#instalação-rápida-usuário-final)
1. [O que o sistema faz](#1-o-que-o-sistema-faz)
2. [Como o equipamento se comunica (protocolo USB)](#2-como-o-equipamento-se-comunica-protocolo-usb)
3. [Arquitetura (MVC)](#3-arquitetura-mvc)
4. [Estrutura de pastas](#4-estrutura-de-pastas)
5. [Requisitos](#5-requisitos)
6. [Instalação para desenvolvimento](#6-instalação-para-desenvolvimento)
7. [Como executar](#7-como-executar)
8. [Telas do painel](#8-telas-do-painel)
9. [Configuração](#9-configuração)
10. [Banco de dados](#10-banco-de-dados)
11. [API HTTP](#11-api-http)
12. [Linha de comando](#12-linha-de-comando)
13. [Gerar o executável e o instalador](#13-gerar-o-executável-e-o-instalador)
14. [Implantação no computador do cliente](#14-implantação-no-computador-do-cliente)
15. [Testes](#15-testes)
16. [Solução de problemas](#16-solução-de-problemas)
17. [Decisões de projeto e limitações](#17-decisões-de-projeto-e-limitações)
18. [Créditos](#18-créditos)

---

## 1. O que o sistema faz

- **Lê** a temperatura e a umidade de cada canal do HP3001 pela porta USB.
- **Grava** cada leitura (data/hora, equipamento, canal, temperatura, umidade) em banco de dados
  (SQLite por padrão; SQL Server ou outro banco via SQLAlchemy).
- **Painel web** com cartões da última leitura por canal, gráficos de temperatura e umidade e
  indicador do estado da coleta.
- **Histórico** com filtros por período e canal, paginação e **atualização automática** a cada
  leitura nova.
- **Exporta para Excel (.xlsx)** respeitando os filtros aplicados, pronto para auditoria.
- **Configuração de intervalo** pela própria tela (de 1 segundo até 1 vez por dia ou mais), com
  efeito imediato, sem reiniciar.
- **Coleta em segundo plano**: o `HP3001.exe` roda na bandeja do Windows, sem janela aberta, e pode
  iniciar junto com o Windows.
- **Instalador** (`HP3001-Setup.exe`) para levar o sistema a computadores sem nada instalado.

Canais com sensor ausente são ignorados automaticamente. Apenas os canais conectados são gravados.

---

## 2. Como o equipamento se comunica (protocolo USB)

O HP3001 é um dispositivo **USB HID** com **VID `0x0483` / PID `0x5750`**. O protocolo foi obtido
a partir do trabalho público de engenharia reversa (veja [Créditos](#18-créditos)).

| Item | Valor |
|---|---|
| Requisição | `7B 03 40 7D` + zeros, completando 64 bytes |
| Resposta | `7B`, depois 8 canais × 3 bytes, e `40 7D` no final |
| Cada canal | `temp_hi`, `temp_lo`, `umidade` |
| Temperatura | inteiro de 16 bits, big-endian, **com sinal**, dividido por 10 (°C) |
| Canal ausente | `7F FF / FF` |
| Pacote com corpo todo zero | pacote de calibração, **ignorado** |

A decodificação está em [`hp3001/services/protocol.py`](hp3001/services/protocol.py) e é coberta
por testes.

**Importante:** o equipamento só aceita **um leitor por vez**. Não execute o `HP3001.exe`, o
`python app.py` e o `python logger.py collect` ao mesmo tempo.

---

## 3. Arquitetura (MVC)

```
                +-----------------------------+
   Navegador -> |  View (templates + JS/CSS)  |
                +--------------+--------------+
                               |
                +--------------v--------------+
                |  Controller (Flask routes)  |
                +------+---------------+------+
                       |               |
          +------------v---+     +-----v------------------+
          |  Model         |     |  Services              |
          |  tabela +      |<----|  collector (thread),   |
          |  repositorio   |     |  device (USB), protocol,|
          +--------+-------+     |  exporter (xlsx)       |
                   |             +-----------+------------+
              Banco de dados                 |
              (SQLite / SQL Server)     HP3001 (USB)
```

| Camada | Pasta | Responsabilidade |
|---|---|---|
| **Model** | `hp3001/models/` | Tabela `readings` (SQLAlchemy Core) e `ReadingRepository` (inserir, consultar, filtrar, paginar, séries) |
| **View** | `hp3001/views/` | Templates Jinja2 (`templates/`) e arquivos estáticos (`static/`: CSS, JS, Chart.js local) |
| **Controller** | `hp3001/controllers/` | Rotas Flask: páginas, API JSON e exportação |
| **Services** | `hp3001/services/` | Regras de negócio e integrações: protocolo, acesso USB, coletor em thread, gerador de Excel |
| **Config** | `hp3001/config.py` | Carrega `config.ini` + `settings.json`, valida o intervalo |

Pontos de projeto:

- **Fábrica de aplicação** (`create_app`) em `hp3001/__init__.py`: monta repositório, coletor e
  controller. Facilita os testes (injeta configuração e backend simulado).
- **Backends de dispositivo** intercambiáveis: `hid` (padrão no Windows), `usb` (PyUSB, exige
  driver WinUSB) e `fake` (simulado, só para testes).
- **Coletor** (`services/collector.py`): thread de segundo plano que lê o equipamento a cada
  intervalo. O intervalo pode ser alterado em tempo real (um evento acorda a thread), e o estado
  (`running`, `last_ok`, `last_error`, `last_count`, `interval_seconds`, `backend`) é exposto em
  `/api/status`.
- **Atualização em tempo real da interface**: `status.js` consulta `/api/status` a cada 1 s e
  avisa as páginas quando `last_ok` muda; o histórico e o painel então recarregam os dados. Assim a
  tela acompanha o intervalo configurado, seja ele de 1 segundo ou de 1 hora.

---

## 4. Estrutura de pastas

```
hp3001-logger/
├── app.py                  # Servidor web de desenvolvimento (python app.py)
├── desktop.py              # Ponto de entrada do .exe: servidor + coletor + bandeja + janela
├── logger.py               # Linha de comando: collect / list / export
├── config.ini              # Configuração padrão
├── requirements.txt        # Dependências Python
├── build.bat               # Gera dist\HP3001\HP3001.exe (PyInstaller)
├── build_installer.bat     # Gera installer_out\HP3001-Setup.exe (Inno Setup)
├── installer.iss           # Script do instalador
├── hp3001/
│   ├── __init__.py         # create_app()
│   ├── config.py           # Config, load_config, validate_interval, save_interval
│   ├── models/
│   │   ├── reading.py      # Tabela readings, get_engine
│   │   └── repository.py   # ReadingRepository
│   ├── services/
│   │   ├── protocol.py     # Montagem/decodificação do pacote
│   │   ├── device.py       # Backends HID, USB e fake
│   │   ├── collector.py    # Thread de coleta
│   │   └── exporter.py     # build_xlsx
│   ├── controllers/
│   │   └── dashboard.py    # Rotas (páginas + API + export)
│   └── views/
│       ├── templates/      # base, dashboard, history, settings, about
│       └── static/         # style.css, dashboard.js, settings.js, status.js, chart.umd.min.js
└── tests/                  # Testes automatizados (pytest)
```

---

## 5. Requisitos

**Para usar o instalador / executável:** Windows 10 ou 11 (64 bits). Nada mais precisa ser
instalado (veja [seção 14](#14-implantação-no-computador-do-cliente)).

**Para desenvolver:**

- Windows 10/11 (a leitura USB foi validada no Windows)
- Python 3.11 ou superior
- Dependências em `requirements.txt`: `flask`, `hidapi`, `pyusb`, `sqlalchemy>=2.0`, `pyodbc`,
  `openpyxl`, `pytest`
- Para gerar o exe: `pyinstaller`, `pywebview`, `pystray`, `pillow` (o `build.bat` instala)
- Para gerar o instalador: [Inno Setup 6](https://jrsoftware.org/isdl.php)

---

## 6. Instalação para desenvolvimento

```powershell
git clone <url-do-repositorio>
cd hp3001-logger
pip install -r requirements.txt
```

Opcional, mas recomendado, usar ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 7. Como executar

### 7.1 Modo desenvolvimento (painel web)

```powershell
python app.py
```

Abra <http://127.0.0.1:5000>. A coleta inicia junto (`autostart = true` no `config.ini`).

Opções:

```powershell
python app.py --backend fake   # dados simulados, para testar sem o equipamento
python app.py --no-collect     # só visualizar, sem ler o equipamento
```

> Não misture dados simulados com o banco real. Para testar com `fake`, use outro
> `database.url` ou outra pasta.

### 7.2 Modo aplicativo (executável)

Abra `HP3001.exe`:

- Abre a janela do painel **e** inicia a coleta.
- Um ícone aparece na **bandeja do Windows** (a seta `^` ao lado do relógio).
- **Fechar a janela não para a coleta.** Ela continua em segundo plano.

Menu do ícone da bandeja (botão direito):

| Item | Ação |
|---|---|
| Abrir painel | Abre a janela do painel |
| Iniciar com o Windows | Liga/desliga o início automático em segundo plano |
| Sair (para a coleta) | Encerra o aplicativo **e a coleta** |

Parâmetros do executável:

| Parâmetro | Efeito |
|---|---|
| *(nenhum)* | Coleta e abre a janela |
| `--background` | Coleta sem abrir janela (usado pelo início automático) |
| `--window` | Só abre a janela (sem coletar) |

Se o aplicativo já estiver rodando, abrir o `HP3001.exe` de novo apenas mostra o painel.

---

## 8. Telas do painel

| Tela | Rota | O que mostra |
|---|---|---|
| **Painel** | `/` | Cartões com a última leitura de cada canal e gráficos de temperatura e umidade (período selecionável) |
| **Histórico** | `/history` | Tabela com todos os registros, filtros (De, Até, Canal), paginação e botão **Exportar Excel** |
| **Configurações** | `/settings` | Escolha do intervalo de coleta |
| **Sobre** | `/about` | Descrição do software e do desenvolvedor |

O indicador no topo mostra o estado: *Coletando*, *Erro de leitura* (com o motivo ao passar o
mouse), *Coleta parada* ou *Servidor offline*.

A tela se atualiza sozinha a cada leitura nova; não é preciso trocar de página.

---

## 9. Configuração

### 9.1 `config.ini`

```ini
[logger]
interval_seconds = 60        # intervalo padrão entre leituras (segundos)
device_name = HP3001-01      # gravado em cada registro (útil na auditoria)
backend = hid                # hid | usb | fake
autostart = true             # inicia a coleta ao abrir o painel (python app.py)

[web]
host = 127.0.0.1
port = 5000

[channels]                   # nomes amigáveis (opcional)
1 = Canal 1
5 = Canal 5

[database]
url = sqlite:///hp3001.db
```

### 9.2 Intervalo de coleta (tela Configurações)

Escolha uma opção pronta (1 s, 5 s, 10 s, 15 s, 30 s, 60 s, 5/10/15/30 min, 1 h, 2 h, 6 h, 12 h,
1 vez por dia) ou **Personalizado** (valor + unidade: segundos, minutos, horas ou dias).

- Valor aceito: de **1 segundo a 7 dias**.
- O valor é salvo em `settings.json` (ao lado do executável/projeto) e **tem prioridade** sobre
  `interval_seconds` do `config.ini`.
- A mudança vale **imediatamente**, sem reiniciar.
- Intervalos muito curtos mostram um aviso sobre o crescimento do banco (por exemplo, 3 s gera
  cerca de 28.800 leituras por canal por dia).

### 9.3 Onde ficam os arquivos no executável/instalado

Tudo fica **na pasta do `HP3001.exe`**: `config.ini`, `hp3001.db`, `settings.json` e
`hp3001.log`.

---

## 10. Banco de dados

Tabela `readings` (criada automaticamente):

| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | inteiro, chave primária | Identificador |
| `recorded_at` | data e hora | Momento da leitura (índice `ix_readings_time`) |
| `device_name` | texto (100) | Nome do equipamento |
| `channel` | inteiro | Número do canal |
| `temperature_c` | decimal | Temperatura em °C |
| `humidity` | inteiro | Umidade relativa em % |

### SQLite (padrão)

Não exige instalação:

```ini
[database]
url = sqlite:///hp3001.db
```

### SQL Server (opcional)

1. Instale o **ODBC Driver 17 ou 18 for SQL Server** no computador.
2. Crie o banco vazio no servidor.
3. Ajuste o `config.ini`:

```ini
[database]
# Usuário e senha
url = mssql+pyodbc://USUARIO:SENHA@SERVIDOR/BANCO?driver=ODBC+Driver+17+for+SQL+Server
# Ou autenticação do Windows
url = mssql+pyodbc://@SERVIDOR/BANCO?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes
```

A tabela é criada na primeira execução. Qualquer banco suportado pelo SQLAlchemy funciona de forma
semelhante (PostgreSQL, MySQL etc.), bastando instalar o driver correspondente.

> O suporte a SQL Server está implementado, mas **não foi validado em um servidor real**. O instalador
> não inclui o driver ODBC.

---

## 11. API HTTP

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/latest` | Última leitura de cada canal |
| GET | `/api/series?hours=N` | Séries de temperatura/umidade por canal nas últimas N horas |
| GET | `/api/status` | Estado da coleta (`running`, `last_ok`, `last_error`, `last_count`, `interval_seconds`, `backend`) |
| GET | `/api/settings` | Intervalo atual e opções |
| POST | `/api/settings` | Altera o intervalo (JSON) e aplica na hora |
| GET | `/export.xlsx` | Baixa o Excel; aceita `start`, `end` (AAAA-MM-DD) e `channel` |

O servidor escuta apenas em `127.0.0.1` por padrão. **Não há autenticação**; não exponha a porta na
rede sem proteção.

---

## 12. Linha de comando

Alternativa ao painel (não rode junto com o painel/executável):

```powershell
python logger.py collect                 # coleta continuamente
python logger.py collect --once          # uma única leitura
python logger.py collect --backend fake  # simulado
python logger.py list --start 2026-01-01 --end 2026-01-31 --channel 1
python logger.py export auditoria.xlsx --start 2026-01-01 --end 2026-01-31
```

---

## 13. Gerar o executável e o instalador

**Antes de qualquer build, feche o aplicativo** (ícone da bandeja → **Sair**); arquivos em uso não
podem ser substituídos.

### 13.1 Executável

```powershell
.\build.bat
```

Gera `dist\HP3001\HP3001.exe` (com a pasta `_internal`). O script usa PyInstaller e **preserva**
`config.ini`, `hp3001.db`, `settings.json` e `hp3001.log` já existentes em `dist\HP3001`.

### 13.2 Instalador

```powershell
.\build_installer.bat
```

Roda o `build.bat` e depois o Inno Setup, gerando `installer_out\HP3001-Setup.exe`.

O instalador:

- instala por usuário, **sem pedir administrador**, em `%LOCALAPPDATA%\Programs\HP3001`;
- cria atalho no Menu Iniciar e (opcional) na Área de Trabalho;
- oferece iniciar a coleta com o Windows;
- **nunca inclui** o banco ou configurações do desenvolvedor;
- ao **atualizar**, não sobrescreve `config.ini`, `hp3001.db` nem `settings.json`;
- ao **desinstalar**, encerra o aplicativo e **mantém** banco e configuração (dados de auditoria).
  Apague a pasta manualmente se quiser remover tudo.

---

## 14. Implantação no computador do cliente

O pacote já leva o Python e todas as bibliotecas. Em um Windows 10/11 64 bits limpo:

| Item | Precisa instalar? |
|---|---|
| Python e bibliotecas | Não |
| Driver USB do HP3001 | Não (usa o driver HID do próprio Windows) |
| Banco SQLite | Não |
| WebView2 (janela do painel) | Normalmente não; se faltar, o painel abre no navegador padrão |
| SQL Server | Só se for usar SQL Server: instalar o ODBC Driver 17/18 |

Passo a passo: execute `HP3001-Setup.exe`, conecte o HP3001 por USB e abra o aplicativo.

Observações:

- O executável **não é assinado digitalmente**: o SmartScreen ou o antivírus podem alertar (é
  comum em programas empacotados com PyInstaller).
- Se a pasta for copiada manualmente em vez de usar o instalador, copie `dist\HP3001` **inteira**
  (não só o `.exe`) e não inclua o seu `hp3001.db`.

---

## 15. Testes

```powershell
python -m pytest -q
```

Cobertura atual (29 testes):

- `tests/test_protocol.py`: decodificação do pacote (sinal, canais ausentes, calibração)
- `tests/test_repository.py`: gravação, filtros, paginação e séries
- `tests/test_settings.py`: validação e persistência do intervalo, API de configurações
- `tests/test_web.py`: páginas, API e exportação Excel

Os testes usam banco temporário e o backend `fake`; não precisam do equipamento.

---

## 16. Solução de problemas

| Sintoma | Causa provável e solução |
|---|---|
| "Erro de leitura" no topo | Equipamento desconectado, ou outro programa o está usando. Veja o motivo ao passar o mouse e confira `hp3001.log` |
| Nenhuma leitura é gravada | Verifique o cabo USB, o `backend = hid` e se não há outra instância lendo o equipamento |
| `python app.py` abre mas o exe não coleta (ou vice-versa) | A porta 5000 e o USB só aceitam um dono. Feche o outro (Ctrl+C no terminal ou **Sair** na bandeja) |
| Backend `usb` falha | Exige driver **WinUSB** (por exemplo via Zadig). Prefira `hid` |
| Botão **Exportar Excel** não baixa no `.exe` | Gere o exe novamente (`build.bat`); o download na janela precisa estar habilitado. Alternativa: abra o painel no navegador |
| `build.bat` falha ao copiar | O aplicativo ainda está aberto. Use **Sair** na bandeja |
| Não acho o ícone da bandeja | Clique na seta `^` ao lado do relógio. Alternativa: Gerenciador de Tarefas → finalizar `HP3001` |
| Histórico não atualiza | Atualize para a versão atual (a tela agora segue cada nova leitura). Verifique se o indicador mostra *Coletando* |
| Dados falsos no banco | Foram gerados com `--backend fake`. Apague as linhas com `DELETE FROM readings WHERE ...` |

Logs: `hp3001.log`, na pasta do executável.

---

## 17. Decisões de projeto e limitações

- **SQLite por padrão** para funcionar sem instalação; troca de banco só pela URL.
- **Um leitor USB por vez**, limitação do próprio equipamento.
- **Sem autenticação** no painel (uso local). Para acesso em rede, coloque um proxy com autenticação.
- Validado com o equipamento real nos **canais 1 e 5**.
- Fora do escopo atual e pendente de validação: SQL Server em servidor real, alertas de
  temperatura/umidade, múltiplos equipamentos, assinatura digital do executável.

---

## 18. Créditos

- **Eduardo Souza**: idealização e desenvolvimento deste projeto.
- Protocolo USB do HP3000/HP3001 baseado no trabalho público de engenharia reversa:
  - [partoneoftwo/hp3000-weather-station-data](https://github.com/partoneoftwo/hp3000-weather-station-data)
  - [weewx-hp3000](https://github.com/matthewwall/weewx-hp3000), de Matthew Wall
- Bibliotecas: Flask, SQLAlchemy, hidapi, PyUSB, openpyxl, Chart.js, pywebview, pystray, Pillow,
  PyInstaller e Inno Setup.
