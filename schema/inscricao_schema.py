"""Schemas Pydantic para entrada e saída de dados de Inscrições."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from .participante_schema import ParticipanteResponse


class InscricaoResponse(BaseModel):
    """Schema de confirmação após realizar uma inscrição."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Identificador único da inscrição")
    evento_id: int = Field(..., description="ID do evento")
    participante_id: int = Field(..., description="ID do participante")
    data_inscricao: datetime = Field(..., description="Data e horário da realização da inscrição")
    mensagem: str = Field(default="Inscrição realizada com sucesso!", description="Mensagem de confirmação")


class DetalhesInscricaoResponse(BaseModel):
    """Schema detalhado de uma inscrição contendo os dados do participante."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Identificador único da inscrição")
    evento_id: int = Field(..., description="ID do evento")
    data_inscricao: datetime = Field(..., description="Data e horário da inscrição")
    participante: ParticipanteResponse = Field(..., description="Dados completos do participante inscrito")

