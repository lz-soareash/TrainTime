# TrainTime

Plataforma esportiva para atletas e treinadores.

## Objetivo

Permitir que atletas acompanhem seus treinos pelo celular e que treinadores gerenciem atletas, equipes, treinos, avaliacoes, desempenho e escalacoes.

## Esportes

- Volei
- Basquete

Novos esportes poderao ser adicionados no futuro.

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, FastAPI |
| Banco | SQLite (migravel para PostgreSQL) |
| Auth | JWT + bcrypt |

## Como Executar

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

Crie o arquivo `backend/.env`:

```
SECRET_KEY=sua-chave-secreta
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM=HS256
DATABASE_URL=sqlite:///./train_time.db
```

```bash
uvicorn app.main:app --reload
```

A API estara disponivel em: `http://localhost:8000`
Documentacao automatica: `http://localhost:8000/docs`

### Frontend

O frontend e servido automaticamente pelo FastAPI na raiz: `http://localhost:8000`

### Testes

```bash
cd backend
pytest tests/ -v
```

## Estrutura

```
TrainTime/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── deps.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── routes/
│   │   └── database/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/
│   └── js/
├── docs/
├── README.md
└── .gitignore
```

## Fase Atual

**FASE 2** - Usuarios, autenticacao e perfis esportivos

### Implementado

- Estrutura do projeto
- Backend com FastAPI
- Banco de dados SQLite com SQLAlchemy
- Modelos: User, Sport, Position, SportAttribute, Athlete, Coach, Team, TeamAthlete, CoachSport, AthleteAttribute
- Autenticacao JWT com bcrypt
- Cadastro de atleta (com esporte e posicao)
- Cadastro de treinador (com esportes)
- Login e logout
- Perfil de atleta (GET/PUT)
- Perfil de treinador (GET/PUT)
- Atributos esportivos do atleta (0-100)
- Controle de roles e autorizacao
- Frontend responsivo mobile-first com login/cadastro/dashboard
- 35 testes automatizados
- Documentacao

### PLANEJADO (Fases futuras)

- Sistema de equipes
- Treinos e exercicios
- Acompanhamento de desempenho
- Avaliacoes de treinadores
- Escalacoes
- Integracao com IA (modulo opcional)
- Suporte a mais esportes
