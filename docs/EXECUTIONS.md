# Execucao de Treinos

Registro do que o atleta realmente fez em cada treino, exercicio a exercicio.

## Fluxo

1. O atleta abre um treino agendado em **Meus Treinos**.
2. Clica em **Iniciar treino**. O backend cria a execucao com status `in_progress`.
3. A tela de execucao lista os exercicios planejados com o que foi registrado.
4. O atleta salva cada exercicio como **feito** ou **pulado**.
5. Ao **Concluir treino**, a execucao recebe `finished_at` e o backend gera
   automaticamente os registros de desempenho com as metricas `volume` e `carga`.

## Endpoints

Prefixo: `/api/workouts/{workout_id}/executions`

| Metodo | Rota | Permissao | Descricao |
|--------|------|-----------|-----------|
| POST | `` | atleta | Inicia execucao. Recusa se ja houver uma `in_progress` do mesmo atleta no mesmo treino |
| GET | `` | atleta da equipe / treinador da equipe | Lista execucoes do treino |
| GET | `/summary` | dono / treinador da equipe | Historico com metricas, deltas e previsao (ver abaixo) |
| GET | `/{execution_id}` | dono / treinador da equipe | Detalhe, com `exercise_results` |
| PUT | `/{execution_id}` | dono | Atualiza `status`, `notes`, `finished_at` |
| POST | `/{execution_id}/exercises/{workout_exercise_id}` | dono | Salva o resultado do exercicio |

### Status da execucao

`in_progress` -> `completed` ou `cancelled`

Execucao `completed`/`cancelled` nao volta para `in_progress` (400).
Concluir duas vezes nao duplica as metricas: `_generate_performance` apaga as
metricas automaticas da execucao antes de regravá-las.

### Status do resultado do exercicio

`pending` -> `done` ou `skipped`

## Campos registrados

| Campo | Tipo | Origem |
|-------|------|--------|
| `status` | `pending` \| `done` \| `skipped` | escolhido pelo atleta |
| `actual_sets` | int | series executadas |
| `actual_repetitions` | int | repeticoes |
| `actual_duration_seconds` | int | tempo |
| `actual_distance_meters` | float | distancia |
| `actual_weight_kg` | float | carga |
| `notes` | str | observacoes |

## Metricas realizadas

Calculadas **sempre** a partir de `WorkoutExerciseExecution` (o que o atleta
registrou), nunca dos valores planejados de `WorkoutExercise`.

| Metrica | Formula | Quando |
|---------|---------|--------|
| `volume` | `actual_sets * actual_repetitions` | `status = done` e ambos informados |
| `volume` | `actual_duration_seconds` | exercicio de tempo, sem series/reps |
| `volume` | `actual_distance_meters` | exercicio de distancia, sem series/reps |
| `carga` | `volume * actual_weight_kg` | `done` com peso registrado |

Exercicio `skipped` ou `pending` zera as duas metricas. Sem `actual_weight_kg`
nao existe registro `carga`.

Adicionais em `GET /summary`, por execucao: `duracao_s`, `exercicios_planejados`,
`exercicios_feitos`, `exercicios_pulados` e `aderencia_pct`.

## Resumo, deltas e previsao

`GET /api/workouts/{workout_id}/executions/summary?limit=5`

```json
{
  "workout_id": 12,
  "executions": [
    {
      "id": 44,
      "status": "completed",
      "started_at": "2026-10-03T12:00:00",
      "finished_at": "2026-10-03T12:41:00",
      "volume": 3600.0,
      "carga": 28800.0,
      "duracao_s": 2460.0,
      "exercicios_planejados": 6,
      "exercicios_feitos": 6,
      "exercicios_pulados": 0,
      "aderencia_pct": 100.0,
      "delta": { "volume": 400.0, "carga": 3200.0, "duracao_s": 120.0 }
    }
  ],
  "forecast": {
    "volume": 3400.0,
    "carga": 27200.0,
    "duracao_s": 2380.0,
    "amostra": 3
  }
}
```

- `executions` vem da mais recente para a mais antiga (limite 1 a 20, padrao 5).
- `delta` compara com a execucao imediatamente anterior e so aparece quando
  as duas estao `completed`; a execucao mais antiga fica com `delta: null`.
- `forecast` e a media das **3 execucoes concluidas mais recentes** (`amostra`
  quantas entraram na media). Execucoes em andamento ou canceladas nao contam.

### Permissao

- Atleta: usa o proprio perfil, ignora `athlete_id`.
- Treinador: precisa enviar `athlete_id` (400 se faltar) e o atleta precisa
  pertencer a uma das suas equipes (403 caso contrario).
- Demais papeis: 403.

## Regras

- O `workout_id` da URL e conferido contra `execution.workout_id` em **todas** as
  rotas por `execution_id`. Combinacao inconsistente devolve 404, nao os dados de
  outro treino.
- O exercicio enviado precisa pertencer ao treino da execucao (validado no service).
- Salvar o mesmo exercicio novamente **atualiza** a linha existente em vez de criar
  outra. A chave logica e `(execution_id, workout_exercise_id)`.
- `completed_at` e preenchido quando o status vai para `done` e zerado caso volte
  para `pending`/`skipped`.
- `started_at` vem do SQLite sem fuso e `finished_at` e gravado em UTC;
  `_duration_seconds` normaliza os dois antes de calcular a duracao.

## Frontend

Pagina `page-execution` em `frontend/index.html`.

| Funcao | Responsabilidade |
|--------|------------------|
| `startExecution(workoutId, btn)` | Cria a execucao e abre a tela |
| `openExecution(executionId, workoutId)` | Carrega execucao + exercicios do treino, renderiza e dispara `loadExecutionSummary` |
| `saveExerciseResult(weId, status, btn)` | Envia o resultado de um exercicio |
| `setExecutionStatus(status)` | Conclui ou cancela, com trava contra duplo clique |
| `loadExecutionSummary(workoutId)` | Card "Previsao e comparacao": media prevista + historico com deltas |

A tela cruza `GET /workouts/{id}/exercises` (planejado) com
`GET .../executions/{id}` (realizado) por `workout_exercise_id`, porque a
resposta de detalhe traz apenas o id do exercicio do treino, sem nome nem meta.

O formulario de cada exercicio traz o planejado apenas como `placeholder`; o
`value` vem do resultado registrado, para o backend nunca herdar a meta como
medida.