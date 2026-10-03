# TrainTime

Plataforma esportiva para atletas e treinadores.

## Objetivo

Permitir que atletas acompanhem seus treinos pelo celular e que treinadores gerenciem atletas, equipes, treinos, avaliacoes, desempenho e escalacoes.

## Esportes

- Volei
- Basquete

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, FastAPI |
| Banco | SQLite (migravel para PostgreSQL) |
| Auth | JWT + bcrypt |

## Como Executar

```bash
cd backend
pip install -r requirements.txt
```

Crie `backend/.env`:

```
SECRET_KEY=sua-chave-secreta
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM=HS256
DATABASE_URL=sqlite:///./train_time.db
```

```bash
uvicorn app.main:app --reload
```

- API: `http://localhost:8000/docs`
- Frontend: `http://localhost:8000`

## Testes

```bash
cd backend
pytest tests/ -v
```

## Fase Atual

**FASE 9** - Execucao de Treinos e Acompanhamento de Desempenho (frontend)

### Implementado

- Autenticacao JWT + bcrypt
- Cadastro e login (atleta/treinador)
- **Perfis:**
  - Visualizacao e edicao de perfil (atleta e treinador) pelo frontend
  - Troca de esporte do atleta limpa posicao/atributos e remove de times de esporte incompativel
  - Posicao validada contra o esporte do atleta; posicao pode ser desmarcada
  - Treinador seleciona os esportes que treina (checkboxes)
- **Atributos esportivos (0-100):**
  - Leitura e atualizacao tipada no backend (duplicatas rejeitadas, lista vazia inadmitida)
  - Nova tela "Meus atributos" com sliders no frontend
- **Invariante treinador x esporte:**
  - Treinador so pode criar time ou exercicio em esporte do proprio perfil
- **Sistema de equipes:**
  - Exclusao de time remove treinos e relacoes vinculadas (cascata)
  - Guarda de perfil do treinador em rotas de time (evita 500)
- **Sistema de treinos**
- **Sistema de exercicios:**
  - Criar exercicio (treinador)
  - Listar exercicios (todos autenticados)
  - Visualizar exercicio (todos autenticados)
  - Editar exercicio (proprietario)
  - Excluir exercicio (proprietario, bloqueado se em uso)
  - Filtros por sport_id e exercise_type
  - Tipos: repetitions, duration, distance, mixed
  - **Biblioteca de exercicios no frontend** (criar/editar/excluir, filtro por esporte, sinalizacao de exercicios de outros treinadores)
- **Exercicios em treinos:**
  - Adicionar exercicio ao treino (treinador proprietario)
  - Listar exercicios do treino (proprietario ou atleta da equipe)
  - Editar exercicio do treino (treinador proprietario)
  - Remover exercicio do treino (treinador proprietario, validando o treino da URL)
  - Validacao de esporte compativel
  - Mesmo exercicio pode aparecer varias vezes
  - Configuracao: order, sets, repetitions, duration, distance, rest, notes
- **Metas (Goals):**
  - Criar metas por atleta (treinador) ou para si mesmo (atleta)
  - Listar metas (atleta: as proprias; treinador: dos atletas das suas equipes)
  - Filtros por status (todas/ativas/concluidas/canceladas)
  - Atualizar progresso; conclusao automatica quando current >= target
  - Cancelar meta
  - `progress_percentage` e `athlete_name` calculados na resposta
  - Pagina de metas no frontend (cards, barra de progresso, formulario de criacao com selecao de atleta para treinador)
- **Execucao de treinos (atleta):**
  - Iniciar execucao de um treino agendado (uma por vez, bloqueia duplicidade)
  - Registrar resultado por exercicio (series, reps, peso, duracao, distancia)
  - Marcar exercicio como feito ou pulado
  - Concluir ou cancelar a execucao
  - Pagina de execucao no frontend com planejado x realizado por exercicio
- **Desempenho (Performance):**
  - Atleta registra metricas manualmente (peso, altura, circunferencia, etc.)
  - Historico pessoal em `GET /performance/records`
  - Visao agregada em `GET /performance` (atleta: proprios dados; treinador: apenas atletas das suas equipes)
  - Registro automatico de metricas `volume` ao concluir uma execucao
  - Pagina de desempenho no frontend com filtros por metrica
  - Card "Performance" e item de menu "Desempenho" liberados
- **Correcoes de bugs criticos encontrados em testes de integracao da Fase 9:**
  - `GET /performance` retornava **500** para atleta (faltava `athlete_name` no schema)
  - **Vazamento de dados:** treinador via desempenho de atletas de outros treinadores (ausencia de filtro por equipe)
  - **Perda de dados:** registros manuais (`execution_id` nulo) sumiam da visao do treinador (inner join)
  - **Duplicacao:** salvar o mesmo exercicio varias vezes criava varias linhas (agora faz upsert por `(execution_id, workout_exercise_id)`)
- 177 testes automatizados (13 de performance, 14 de execucoes, 10 de regressao dos bugs acima)
- Frontend mobile-first com gerenciamento de perfis, atributos, exercicios, treinos, execucoes, metas e desempenho

### PLANEJADO (Fases futuras)

- Execucao de treinos: calculo de volume usando valores **realizados** (hoje usa os planejados)
- Execucao de treinos: validar `workout_id` da URL contra a execucao
- Execucao de treinos: previsao de carga e comparacao entre execucoes
- Avaliacoes de treinadores
- Integracao com IA (modulo opcional)
- Suporte a mais esportes
