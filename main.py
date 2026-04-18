from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import date
from datetime import datetime # <- NOVA
import requests # <- NOVA

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

@app.get("/robo/cobrar-hoje")
def disparar_robo_cobranca():
    # 1. Descobre a data de hoje no formato do banco de dados (YYYY-MM-DD)
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    # 2. Pede para o Supabase as contas pendentes que vencem hoje
    resposta = supabase.table("contas_pagar").select("*").eq("pago", False).eq("vencimento", hoje).execute()
    contas_hoje = resposta.data
    
    # 3. Se não tiver nenhuma conta hoje, o robô volta a dormir
    if not contas_hoje:
        return {"mensagem": "Tudo tranquilo! Nenhuma conta vencendo hoje."}
    
    # 4. Se tiver contas, o robô monta a mensagem de aviso
    texto_mensagem = "🚨 *Aviso de Vencimento Hoje!* 🚨\n\n"
    
    for conta in contas_hoje:
        # Formata o valor para ficar bonito (ex: 150.00 -> 150,00)
        valor_formatado = f"{conta['valor']:.2f}".replace(".", ",")
        texto_mensagem += f"📄 *{conta['descricao']}*\n💰 Valor: R$ {valor_formatado}\n\n"
        
    texto_mensagem += "Não esqueça de dar baixa no sistema após o pagamento!"
    
    # 5. Envia a carta para os correios do Telegram
    TOKEN = "8696328198:AAGY7QJZZLeS9DS81BNsc_RfMOR4uM1_GUc"
    CHAT_ID = "8092934430"
    url_telegram = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    dados = {
        "chat_id": CHAT_ID,
        "text": texto_mensagem,
        "parse_mode": "Markdown" # Permite usar negrito com o asterisco (*)
    }
    
    requests.post(url_telegram, json=dados)
    
    return {"mensagem": f"Robô disparado! {len(contas_hoje)} cobrança(s) enviada(s)."}