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

**FASE 4** - Sistema de Treinos

### Implementado

- Autenticacao JWT + bcrypt
- Cadastro e login (atleta/treinador)
- Perfil de atleta e treinador
- Atributos esportivos (0-100)
- Sistema de equipes
- **Sistema de treinos:**
  - Criar treino (treinador)
  - Listar treinos (treinador por equipe, atleta por equipes)
  - Visualizar treino (proprietario)
  - Editar treino (treinador proprietario)
  - Excluir treino (treinador proprietario)
  - Filtros por team_id e status
  - Status: scheduled, completed, cancelled
  - Ordenacao por scheduled_at ASC
  - Autorizacao por propriedade da equipe
- 86 testes automatizados
- Frontend mobile-first com gerenciamento de treinos

### PLANEJADO (Fases futuras)

- Exercicios dentro dos treinos
- Execucao de treinos
- Acompanhamento de desempenho
- Avaliacoes de treinadores
- Integracao com IA (modulo opcional)
- Suporte a mais esportes
