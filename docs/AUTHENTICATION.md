# Autenticacao - TrainTime

## Fluxo

```
Cadastro
   ↓
Login (email + senha)
   ↓
JWT Token
   ↓
Requisicoes autenticadas (Bearer token)
```

## Endpoints

| Metodo | Rota | Descricao | Auth |
|--------|------|-----------|------|
| POST | /api/auth/register | Cadastro generico | Nao |
| POST | /api/auth/register/athlete | Cadastro de atleta | Nao |
| POST | /api/auth/register/coach | Cadastro de treinador | Nao |
| POST | /api/auth/login | Login | Nao |
| GET | /api/auth/me | Dados do usuario | Sim |
| GET | /api/athletes/me | Perfil do atleta | Sim (athlete) |
| PUT | /api/athletes/me | Atualizar perfil atleta | Sim (athlete) |
| GET | /api/athletes/me/attributes | Atributos do atleta | Sim (athlete) |
| PUT | /api/athletes/me/attributes | Atualizar atributos | Sim (athlete) |
| GET | /api/coaches/me | Perfil do treinador | Sim (coach) |
| PUT | /api/coaches/me | Atualizar perfil treinador | Sim (coach) |

## Cadastro de Atleta

Requisicao:

```json
{
    "name": "Joao",
    "email": "joao@example.com",
    "password": "123456",
    "sport_id": 1,
    "position_id": 3
}
```

Validacoes:
- Esporte deve existir
- Posicao deve pertencer ao esporte
- Email deve ser unico
- Senha minimo 6 caracteres

## Cadastro de Treinador

Requisicao:

```json
{
    "name": "Maria",
    "email": "maria@example.com",
    "password": "123456",
    "sport_ids": [1, 2]
}
```

Validacoes:
- Todos os esportes devem existir
- Pelo menos um esporte selecionado

## Login

Requisicao:

```json
{
    "email": "joao@example.com",
    "password": "123456"
}
```

Resposta:

```json
{
    "access_token": "eyJ...",
    "token_type": "bearer"
}
```

## JWT

- Secret key via variavel de ambiente `SECRET_KEY`
- Algoritmo: HS256
- Expiracao: configuravel via `ACCESS_TOKEN_EXPIRE_MINUTES` (padrao 1440 = 24h)
- Payload: `{"sub": "<user_id>", "exp": <timestamp>}`

## Seguranca

- Senhas: bcrypt (nunca texto puro)
- JWT secret: variavel de ambiente (nunca no codigo)
- .env: nao commitado (.gitignore)
- Autorizacao: verificada no backend via dependencias
- Mensagens de erro: genericas (nao revelam se email existe)
