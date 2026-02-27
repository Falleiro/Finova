# Pluggy API — Referência de Integração

Documentação dos detalhes críticos da API Pluggy para o projeto FINOVA.
Atualizar sempre que descobrir novos comportamentos da API.

---

## Autenticação

### Obter API Key (backend)

```
POST https://api.pluggy.ai/auth
Content-Type: application/json

Body:
{
  "clientId": "<OPEN_FINANCE_CLIENT_ID>",
  "clientSecret": "<OPEN_FINANCE_CLIENT_SECRET>"
}

Resposta:
{
  "apiKey": "eyJhbGci..."
}
```

- A `apiKey` **expira em 2 horas**
- Deve ser obtida dinamicamente a cada sessão — **não armazenar como valor estático no .env**
- Usar no header de todas as requisições: `X-API-KEY: <apiKey>`

### Connect Token (frontend — não usado no backend)

```
POST https://api.pluggy.ai/connect_token
X-API-KEY: <apiKey>

Retorna accessToken válido por 30 minutos — usado só no widget PluggyConnect
```

---

## Headers de Autenticação

```
X-API-KEY: <apiKey>         ← backend (este projeto)
Authorization: Bearer ...   ← NÃO é o padrão da Pluggy
x-consent-token: ...        ← NÃO existe na Pluggy
```

---

## Endpoints de Dados

### Contas — GET /accounts

```
GET /accounts?itemId=<PLUGGY_ITEM_ID>
X-API-KEY: <apiKey>
```

**itemId é obrigatório.** Sem ele → 400 Bad Request.

Resposta:
```json
{
  "total": 2,
  "totalPages": 1,
  "results": [
    {
      "id": "uuid-da-conta",
      "itemId": "uuid-do-item",
      "type": "BANK",
      "subtype": "CHECKING_ACCOUNT",
      "name": "Conta Corrente",
      "balance": 1234.56,
      "currencyCode": "BRL",
      "institution": {
        "name": "Nubank",
        "primaryColor": "#8A05BE"
      }
    }
  ]
}
```

Mapeamento de campos (API → interno):
| API | Interno |
|-----|---------|
| `id` | `account_id` |
| `institution.name` ou `name` | `institution` |
| `subtype` | `type` |
| `balance` (float) | `balance_cents` (× 100) |
| `currencyCode` | `currency` |
| `results` | `data` |

---

### Transações — GET /transactions

```
GET /transactions?accountId=<account_id>&from=YYYY-MM-DD&to=YYYY-MM-DD
X-API-KEY: <apiKey>
```

**Importante:**
- Usa `accountId` (não `itemId`) — precisa buscar contas primeiro
- Data filtrada por `from`/`to` (não `days`)
- Adicionar `pageSize=500` para evitar paginação em contas com muitas transações

Resposta:
```json
{
  "total": 10,
  "totalPages": 1,
  "results": [
    {
      "id": "uuid-da-transacao",
      "accountId": "uuid-da-conta",
      "description": "iFood *pedido",
      "amount": 45.90,
      "currencyCode": "BRL",
      "date": "2026-02-27T00:00:00.000Z",
      "type": "DEBIT",
      "category": "Food",
      "merchant": null
    }
  ]
}
```

Mapeamento de campos (API → interno):
| API | Interno |
|-----|---------|
| `id` | `transaction_id` |
| `accountId` | `account_id` |
| `amount` (float) | `amount_cents` (× 100) |
| `description` | `description` |
| `merchant` | `merchant` |
| `date` | `timestamp` |
| `results` | `data` |

---

### Investimentos — GET /investments

```
GET /investments?itemId=<PLUGGY_ITEM_ID>
X-API-KEY: <apiKey>
```

**itemId é obrigatório.** Sem ele → 400 Bad Request.

Resposta (campos variam por tipo):
```json
{
  "total": 3,
  "totalPages": 1,
  "results": [
    {
      "id": "uuid",
      "itemId": "uuid",
      "type": "FIXED_INCOME",
      "subtype": "CDB",
      "name": "CDB Banco X",
      "code": "CDB_X",
      "quantity": 1.0,
      "value": 5000.00,
      "amount": 4800.00,
      "annualRate": 12.5,
      "lastMonthRate": 1.02,
      "date": "2026-02-27"
    }
  ]
}
```

Mapeamento de campos (API → interno):
| API | Interno |
|-----|---------|
| `id` | `asset_id` |
| `code` ou `name` | `ticker` |
| `name` | `name` |
| `quantity` | `quantity` |
| `value` (valor atual total) | `total_value_cents` (× 100) |
| `amount` (valor aplicado) | — |
| `results` | `data` |

**Nota sobre daily_change_pct**: A Pluggy não retorna `openPrice`/`currentPrice` separados.
Calcular variação com `annualRate` ou `lastMonthRate` quando disponíveis, senão usar 0.0.

---

## Conceitos Importantes

### Item vs Account

| Conceito | O que é | Usado em |
|---|---|---|
| `itemId` | Conexão bancária (ex: "minha conta Nubank") | `/accounts`, `/investments` |
| `accountId` | Conta específica dentro do item (corrente, poupança) | `/transactions` |

Um `itemId` pode ter múltiplos `accountId`s.

### PLUGGY_ITEM_ID_MEU_PLUGGY

O valor do `PLUGGY_ITEM_ID_MEU_PLUGGY` no `.env` é o `itemId` da conexão bancária.
Não confundir com `OPEN_FINANCE_CONSENT_TOKEN` (que no projeto não é usado).

---

## Variáveis de Ambiente Relevantes

```env
OPEN_FINANCE_CLIENT_ID=...          # clientId para autenticação
OPEN_FINANCE_CLIENT_SECRET=...      # clientSecret para autenticação
OPEN_FINANCE_BASE_URL=https://api.pluggy.ai
PLUGGY_ITEM_ID_MEU_PLUGGY=...       # itemId da conexão bancária
```

`OPEN_FINANCE_CONSENT_TOKEN` existe no .env mas não é utilizado pelo backend.
