from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import date

# 1. Inicializando o FastAPI
app = FastAPI(title="API de Boletos - Embalagens")

from fastapi.middleware.cors import CORSMiddleware

# ... (seu app = FastAPI() já está aqui)

# Liberando o CORS para o React conseguir acessar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Na vida real, colocaríamos a URL exata do React aqui
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Configurando a conexão com o Supabase
# Substitua com as chaves que você copiou na etapa anterior
SUPABASE_URL = "https://edqhoekcdcvqfpwavzzm.supabase.co"
SUPABASE_KEY = "sb_publishable_4mljtSYrwhbH2BLqb-5nHg_MuZEsz3O"


# Cria o "cliente" que vai fazer a comunicação com o banco
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class ContaNova(BaseModel):
    descricao: str
    valor: float
    vencimento: date

# ROTA 1: Teste para saber se a API está viva
@app.get("/")
def raiz():
    return {"status": "API online e operante!"}

# ROTA 2: Cadastrar um novo boleto (C - Create)
@app.post("/contas/")
def cadastrar_conta(conta: ContaNova):
    # Transforma os dados em um dicionário e insere na tabela 'contas_pagar'
    resposta = supabase.table("contas_pagar").insert(conta.model_dump(mode='json')).execute()
    
    # Se der certo, retorna os dados cadastrados
    return {"mensagem": "Boleto salvo com sucesso", "dados": resposta.data}

# ROTA 3: Listar apenas os boletos pendentes (R - Read)
@app.get("/contas/pendentes")
def listar_boletos_pendentes():
    # Vai no banco, seleciona TUDO (*), mas apenas ONDE (eq) pago for Falso
    resposta = supabase.table("contas_pagar").select("*").eq("pago", False).execute()
    return resposta.data

# ROTA 4: Dar baixa em um boleto (U - Update)
@app.post("/contas/{conta_id}/pagar")
def dar_baixa_boleto(conta_id: str):
    # Procura a conta pelo ID e atualiza o campo 'pago' para Verdadeiro
    resposta = supabase.table("contas_pagar").update({"pago": True}).eq("id", conta_id).execute()
    return {"mensagem": "Boleto pago!", "dados": resposta.data}