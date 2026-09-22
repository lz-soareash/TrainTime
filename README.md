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

**FASE 3** - Sistema de Equipes

### Implementado

- Autenticacao JWT + bcrypt
- Cadastro e login (atleta/treinador)
- Perfil de atleta e treinador
- Atributos esportivos (0-100)
- **Sistema de equipes:**
  - Criar equipe (treinador)
  - Listar equipes (treinador)
  - Visualizar equipe (treinador/atleta)
  - Editar nome da equipe (treinador)
  - Excluir equipe (treinador)
  - Adicionar atleta a equipe (treinador)
  - Remover atleta da equipe (treinador)
  - Visualizar minhas equipes (atleta)
  - Validacao de esporte compativel
  - Controle de duplicidade
  - Autorizacao por proprietario
- 62 testes automatizados
- Frontend mobile-first com gerenciamento de equipes

### PLANEJADO (Fases futuras)

- Treinos e exercicios
- Acompanhamento de desempenho
- Avaliacoes de treinadores
- Escalacoes
- Integracao com IA (modulo opcional)
- Suporte a mais esportes
