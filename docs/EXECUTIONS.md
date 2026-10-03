# Execucao de Treinos

Registro do que o atleta realmente fez em cada treino, exercicio a exercicio.

## Fluxo

1. O atleta abre um treino agendado em **Meus Treinos**.
2. Clica em **Iniciar treino**. O backend cria a execucao com status `in_progress`.
3. A tela de execucao lista os exercicios planejados com o que foi registrado.
4. O atleta salva cada exercicio como **feito** ou **pulado**.
5. Ao **Concluir treino**, a execucao recebe `finished_at` e o backend gera
   automaticamente registros de desempenho com a metrica `volume`.

## Endpoints

Prefixo: `/api/workouts/{workout_id}/executions`

| Metodo | Rota | Permissao | Descricao |
|--------|------|-----------|-----------|
| POST | `` | atleta | Inicia execucao. Recusa se ja houver uma `in_progress` do mesmo atleta no mesmo treino |
| GET | `` | atleta da equipe / treinador da equipe | Lista execucoes do treino |
| GET | `/{execution_id}` | dono / treinador da equipe | Detalhe, com `exercise_results` |
| PUT | `/{execution_id}` | dono | Atualiza `status`, `notes`, `finished_at` |
| POST | `/{execution_id}/exercises/{workout_exercise_id}` | dono | Salva o resultado do exercicio |

### Status da execucao

`in_progress` -> `completed` ou `cancelled`

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

## Regras

- O exercicio enviado precisa pertencer ao treino da execucao (validado no service).
- Salvar o mesmo exercicio novamente **atualiza** a linha existente em vez de criar
  outra. A chave logica e `(execution_id, workout_exercise_id)`.
- `completed_at` e preenchido quando o status vai para `done` e zerado caso volte
  para `pending`/`skipped`.
- Somar exercicios com status `done` e o que alimenta a geracao automatica de performance.

## Frontend

Pagina `page-execution` em `frontend/index.html`.

| Funcao | Responsabilidade |
|--------|------------------|
| `startExecution(workoutId, btn)` | Cria a execucao e abre a tela |
| `openExecution(executionId, workoutId)` | Carrega execucao + exercicios do treino e renderiza |
| `saveExerciseResult(weId, status, btn)` | Envia o resultado de um exercicio |
| `setExecutionStatus(status)` | Conclui ou cancela, com trava contra duplo clique |

A tela cruza `GET /workouts/{id}/exercises` (planejado) com
`GET .../executions/{id}` (realizado) por `workout_exercise_id`, porque a
resposta de detalhe traz apenas o id do exercicio do treino, sem nome nem meta.

## Limitacoes conhecidas

- A metrica automatica `volume` usa os valores **planejados** do treino
  (`sets * repetitions`), nao os valores **realizados** no resultado.
  Ver `_generate_performance` em `app/services/workout_execution_service.py`.
- O `workout_id` da URL nao e conferido contra `execution.workout_id`; a validacao
  existente compara o exercicio com `execution.workout_id`, o que cobre o caso
  pratico, mas nao rejeita a combinacao de ids inconsistente.
- Concluir a mesma execucao duas vezes gera registros `volume` duplicados, pois
  `_generate_performance` nao e idempotente.