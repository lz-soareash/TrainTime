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

**FASE 5** - Consolidacao: Perfis, Atributos e Sistema de Exercicios

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
  - Configuracao: order, sets, repetitions, duration_seconds, distance_meters, rest_seconds, notes
- 137 testes automatizados
- Frontend mobile-first com gerenciamento de perfis, atributos, exercicios e treinos

### PLANEJADO (Fases futuras)

- Execucao de treinos
- Acompanhamento de desempenho
- Avaliacoes de treinadores
- Integracao com IA (modulo opcional)
- Suporte a mais esportes
