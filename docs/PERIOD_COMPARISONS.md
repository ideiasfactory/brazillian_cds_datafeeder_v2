# Period Comparisons Feature - Statistics Endpoint

## Overview

O endpoint `/api/cds/statistics` agora inclui comparações de variação temporal para os períodos:
- **1 mês** (~30 dias)
- **3 meses** (~90 dias)  
- **6 meses** (~180 dias)
- **52 semanas** (~364 dias)

## Exemplo de Resposta

```json
{
  "status": "success",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "total_records": 5234,
    "earliest_date": "2010-01-04",
    "latest_date": "2025-11-20",
    "sources": ["investing.com"],
    "period_comparisons": [
      {
        "period": "1 month",
        "days": 30,
        "start_date": "2025-10-21",
        "end_date": "2025-11-20",
        "start_value": 0.0234,
        "end_value": 0.0245,
        "absolute_change": 0.0011,
        "percentage_change": 4.70,
        "available": true
      },
      {
        "period": "3 months",
        "days": 90,
        "start_date": "2025-08-22",
        "end_date": "2025-11-20",
        "start_value": 0.0220,
        "end_value": 0.0245,
        "absolute_change": 0.0025,
        "percentage_change": 11.36,
        "available": true
      },
      {
        "period": "6 months",
        "days": 180,
        "start_date": "2025-05-24",
        "end_date": "2025-11-20",
        "start_value": 0.0210,
        "end_value": 0.0245,
        "absolute_change": 0.0035,
        "percentage_change": 16.67,
        "available": true
      },
      {
        "period": "52 weeks",
        "days": 364,
        "start_date": "2024-11-22",
        "end_date": "2025-11-20",
        "start_value": 0.0198,
        "end_value": 0.0245,
        "absolute_change": 0.0047,
        "percentage_change": 23.74,
        "available": true
      }
    ]
  },
  "error_message": null,
  "timestamp": "2025-11-20T04:30:00.000000"
}
```

## Campos da Comparação de Períodos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `period` | string | Nome do período (ex: "1 month", "3 months") |
| `days` | integer | Número de dias no período |
| `start_date` | date \| null | Data inicial da comparação (registro mais próximo encontrado) |
| `end_date` | date | Data final (data mais recente no banco de dados) |
| `start_value` | float \| null | Valor do CDS na data inicial (em basis points) |
| `end_value` | float | Valor do CDS na data final (em basis points) |
| `absolute_change` | float \| null | Variação absoluta em basis points (end_value - start_value) |
| `percentage_change` | float \| null | Variação percentual ((absolute_change / start_value) * 100) |
| `available` | boolean | Indica se há dados disponíveis para este período |

## Comportamento

### Dados Disponíveis
Quando há dados históricos suficientes para o período:
- `available` = `true`
- Todos os campos numéricos são preenchidos
- `start_date` é o registro mais próximo (ou anterior) à data calculada

### Dados Indisponíveis
Quando não há dados históricos para o período:
- `available` = `false`
- Campos `start_date`, `start_value`, `absolute_change`, `percentage_change` = `null`
- Apenas `end_date` e `end_value` são preenchidos

### Exemplo de Período Sem Dados

```json
{
  "period": "52 weeks",
  "days": 364,
  "start_date": null,
  "end_date": "2025-11-20",
  "start_value": null,
  "end_value": 0.0245,
  "absolute_change": null,
  "percentage_change": null,
  "available": false
}
```

## Implementação Técnica

### Novo Modelo: `PeriodComparison`
```python
class PeriodComparison(BaseModel):
    period: str
    days: int
    start_date: Optional[date]
    end_date: Optional[date]
    start_value: Optional[float]
    end_value: Optional[float]
    absolute_change: Optional[float]
    percentage_change: Optional[float]
    available: bool
```

### Repositório: `CDSRepository.get_period_comparisons()`
```python
async def get_period_comparisons(
    self, latest_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """
    Calcula comparações período-a-período para vários intervalos de tempo.
    
    Compara o valor atual do CDS com valores de:
    - 1 mês atrás (~30 dias)
    - 3 meses atrás (~90 dias)
    - 6 meses atrás (~180 dias)
    - 52 semanas atrás (~364 dias)
    """
```

### Endpoint: `GET /api/cds/statistics`
- **Autenticação**: Requer API Key (header `X-API-Key`)
- **Método HTTP**: GET
- **Response**: `StandardResponse` com `CDSStatisticsData`

## Uso

### cURL
```bash
curl -X GET "https://api.example.com/api/cds/statistics" \
  -H "X-API-Key: your-api-key-here"
```

### Python
```python
import requests

response = requests.get(
    "https://api.example.com/api/cds/statistics",
    headers={"X-API-Key": "your-api-key-here"}
)

data = response.json()
comparisons = data["data"]["period_comparisons"]

for comp in comparisons:
    if comp["available"]:
        print(f"{comp['period']}: {comp['percentage_change']:.2f}% change")
```

### JavaScript
```javascript
const response = await fetch('https://api.example.com/api/cds/statistics', {
  headers: {
    'X-API-Key': 'your-api-key-here'
  }
});

const data = await response.json();
const comparisons = data.data.period_comparisons;

comparisons.forEach(comp => {
  if (comp.available) {
    console.log(`${comp.period}: ${comp.percentage_change}% change`);
  }
});
```

## Notas

1. **Arredondamento**: 
   - `absolute_change`: 4 casas decimais
   - `percentage_change`: 2 casas decimais

2. **Data de Referência**: 
   - Se não especificada, usa a data mais recente no banco de dados
   - Busca o registro mais próximo (ou anterior) à data calculada

3. **Tratamento de Erros**:
   - Se falhar ao calcular comparações, o campo `period_comparisons` será `null`
   - A resposta principal não é afetada (statistics básicas ainda são retornadas)

4. **Performance**:
   - Cada comparação faz 1 query adicional ao banco
   - Total: 5 queries (1 para latest + 4 para períodos)
   - Tempo estimado: < 100ms para banco otimizado
