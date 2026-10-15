from pydantic import BaseModel


class OrcamentoCreate(BaseModel):
    nome: str
    categoria: str
    valor: float
    validade_meses: int
    cpf: str

    class Config:
        orm_mode = True
