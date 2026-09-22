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

**FASE 5** - Sistema de Exercicios

### Implementado

- Autenticacao JWT + bcrypt
- Cadastro e login (atleta/treinador)
- Perfil de atleta e treinador
- Atributos esportivos (0-100)
- Sistema de equipes
- Sistema de treinos
- **Sistema de exercicios:**
  - Criar exercicio (treinador)
  - Listar exercicios (todos autenticados)
  - Visualizar exercicio (todos autenticados)
  - Editar exercicio (proprietario)
  - Excluir exercicio (proprietario, bloqueado se em uso)
  - Filtros por sport_id e exercise_type
  - Tipos: repetitions, duration, distance, mixed
- **Exercicios em treinos:**
  - Adicionar exercicio ao treino (treinador proprietario)
  - Listar exercicios do treino (proprietario ou atleta da equipe)
  - Editar exercicio do treino (treinador proprietario)
  - Remover exercicio do treino (treinador proprietario)
  - Validacao de esporte compativel
  - Mesmo exercicio pode aparecer varias vezes
  - Configuracao: order, sets, repetitions, duration_seconds, distance_meters, rest_seconds, notes
- 125 testes automatizados
- Frontend mobile-first com gerenciamento de exercicios e treinos

### PLANEJADO (Fases futuras)

- Execucao de treinos
- Acompanhamento de desempenho
- Avaliacoes de treinadores
- Integracao com IA (modulo opcional)
- Suporte a mais esportes
