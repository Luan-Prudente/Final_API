from fastapi import FastAPI, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum
import datetime

app = FastAPI()

class AtendimentoTipo(str, Enum):
    normal = 'N'
    prioritario = 'P'

class Cliente(BaseModel):
    nome: str = Field(max_length=20)
    tipo_atendimento: AtendimentoTipo
    atendido: bool = False
    posicao: Optional[int] = None
    data_chegada: str = Field(default_factory=lambda: datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))

fila_clientes: List[Cliente] = []

def atualizar_posicoes():
    for idx, cliente in enumerate(fila_clientes):
        cliente.posicao = idx + 1

@app.get("/")
def bem_vindo():
    return {"message": "Bem-vindo! A fila. Aguarde sua vez!"}

@app.get("/fila", response_model=List[Cliente])
def listar_fila():
    nao_atendidos = [cliente for cliente in fila_clientes if not cliente.atendido]
    atualizar_posicoes()
    if not nao_atendidos:
        return []
    return nao_atendidos

@app.get("/fila/{id}", response_model=Cliente)
def obter_cliente(id: int):
    if id <= 0 or id > len(fila_clientes):
        raise HTTPException(status_code=404, detail="Cliente não encontrado na posição especificada.")
    return fila_clientes[id - 1]

@app.post("/fila", response_model=Cliente)
def adicionar_cliente(cliente: Cliente):
    if len(cliente.nome) > 20:
        raise HTTPException(status_code=400, detail="Nome excede o tamanho máximo permitido.")
    cliente.posicao = len(fila_clientes) + 1
    fila_clientes.append(cliente)
    return cliente

@app.put("/fila")
def atualizar_fila():
    nao_atendidos = [cliente for cliente in fila_clientes if not cliente.atendido]
    prioritarios = [cliente for cliente in nao_atendidos if cliente.tipo_atendimento == AtendimentoTipo.prioritario]
    normais = [cliente for cliente in nao_atendidos if cliente.tipo_atendimento == AtendimentoTipo.normal]

    nova_fila = []
    prioridades_contagem = 0

    while prioritarios or normais:
        if prioritarios and prioridades_contagem < 2:
            nova_fila.append(prioritarios.pop(0))
            prioridades_contagem += 1
        elif normais and prioridades_contagem == 2:
            nova_fila.append(normais.pop(0))
            prioridades_contagem = 0
        elif prioritarios:
            nova_fila.append(prioritarios.pop(0))
            prioridades_contagem += 1
        elif normais:
            nova_fila.append(normais.pop(0))


    for cliente in nova_fila:
        cliente.posicao -= 1
        if cliente.posicao == 0:
            cliente.atendido = True


    fila_clientes[:] = [cliente for cliente in nova_fila if not cliente.atendido]

    atualizar_posicoes()

    return fila_clientes


@app.delete("/fila/{id}", response_model=Cliente)
def remover_cliente(id: int):
    if id <= 0 or id > len(fila_clientes):
        raise HTTPException(status_code=404, detail="Cliente não encontrado na posição especificada.")
    cliente_removido = fila_clientes.pop(id - 1)
    atualizar_posicoes()
    return cliente_removido