# Desempenho (Performance)

Metricas de evolucao do atleta. Parte sao registradas a mao, parte e gerada
automaticamente ao concluir um treino.

## Origem dos dados

| Origem | Como |
|--------|------|
| Manual | O proprio atleta usa o formulario "Registrar desempenho" |
| Automatica | Concluir uma execucao gera registros com metrica `volume` |

## Endpoints

Prefixo: `/api/performance`

| Metodo | Rota | Permissao | Descricao |
|--------|------|-----------|-----------|
| POST | `` | atleta | Registra `{metric, value, execution_id?, notes?}` |
| GET | `/records` | atleta | Historico pessoal, em `PerformanceRecordResponse` |
| GET | `` | atleta ou treinador | Visao agregada, em `PerformanceAggregateResponse` |

O corpo do POST **ignora** qualquer `athlete_id` enviado: o registro sempre
pertence ao atleta autenticado.

## Diferenca entre as respostas

`GET /performance/records` nao tem `athlete_name`; `GET /performance` tem,
porque cada linha sao de um atleta e o treinador precisa saber de quem e.

Ambas ordenam por `recorded_at` decrescente.

## Quem ve o que

- **Atleta:** apenas os proprios registros.
- **Treinador:** apenas registros de atletas que pertencem a **alguma equipe
  sua**. O filtro usa `team_athletes` + `teams.coach_id`, independente de o
  registro vir de uma execucao ou ter sido digitado a mao.

O filtro por `athlete_id` do service so e aceito para treinador; para atleta
dispara `PermissionError` (403).

## Metricas automaticas `volume` e `carga`

Geradas por `_generate_performance` ao concluir uma execucao. Desde a Fase 10
usam **sempre** os valores realizados (`WorkoutExerciseExecution`), nunca o
planejado, e a gravacao e idempotente (as metricas automaticas da execucao sao
removidas antes de regravadas).

Por exercicio com `status = done`:

```
volume = actual_sets * actual_repetitions
         (ou actual_duration_seconds / actual_distance_meters, se nao houver series/reps)
carga  = volume * actual_weight_kg   -> so quando houver peso registrado
```

Exercicio `skipped`/`pending` nao gera registro. Metricas manuais
(`execution_id` nulo) nunca sao tocadas por esse processo.

`GET /performance` expoe `execution_id` em cada registro, o que permite ligar a
metrica a execucao de origem. Resumo por execucao, deltas e previsao ficam em
`GET /workouts/{workout_id}/executions/summary` (ver EXECUTIONS.md).

## Frontend

Pagina `page-performance` em `frontend/index.html`, acessada pelo card
"Performance" do dashboard ou pelo item "Desempenho" do menu.

| Funcao | Responsabilidade |
|--------|------------------|
| `openPerformancePage()` | Ajusta o texto conforme o papel e carrega |
| `loadPerformance()` | Busca os dados, aplica o filtro de metrica e renderiza |
| `renderMetricFilters(metrics)` | Monta os botoes de metrica a partir dos dados |
| `renderPerformanceCard(record)` | Card; mostra `athlete_name` so para treinador |
| `applyMetricFilter(metric)` | Filtra no cliente |
| `showCreatePerformance()` | Abre/fecha o formulario (so para atleta) |
| `handleCreatePerformance(e)` | Envia o registro e recarrega |

O filtro por metrica e feito no cliente, ja que o endpoint agregado nao expoe
query params.

## Bugs corrigidos na Fase 9

Encontrados por teste de integracao contra a API real, nao cobertos pela suite
anterior. As regressoes estao em `backend/tests/test_performance.py`.

1. **500 em `GET /performance` para atleta.** O service devolvia o objeto ORM
   cru no ramo de atleta, sem `athlete_name`, e o schema exigia o campo. Agora
   os dois ramos devolvem `PerformanceAggregateResponse`.
2. **Vazamento entre treinadores.** A query do treinador nao filtrava por equipe,
   entao qualquer treinador via todos os registros do sistema.
3. **Perda de registros manuais.** O `join` interno em `PerformanceRecord.execution`
   descartava todo registro com `execution_id` nulo, ou seja, os digitados a mao
   sumiam da visao do treinador.