from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from lumi_core.catalog.traits import TYPES
from lumi_core.catalog.zodiac import SIGNS
from lumi_core.catalog.tarot import BY_ID

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

class ReadingInput(StrictModel):
    mbti: str
    zodiac_id: str
    question: str = Field(min_length=2, max_length=1000)
    spread: Literal['three_card_reflection'] = 'three_card_reflection'

    @field_validator('question')
    @classmethod
    def trimmed_question(cls,value):
        value=value.strip()
        if len(value)<2: raise ValueError('Question is too short')
        return value

    @field_validator('mbti')
    @classmethod
    def known_type(cls,value):
        if value not in TYPES: raise ValueError('Unknown MBTI')
        return value

    @field_validator('zodiac_id')
    @classmethod
    def known_sign(cls,value):
        if value not in {sign[0] for sign in SIGNS}: raise ValueError('Unknown zodiac')
        return value

class Draw(StrictModel):
    card_id: str
    orientation: Literal['upright','reversed']
    position: Literal['past','present','future']
    ordinal: int = Field(ge=0,le=2)

    @field_validator('card_id')
    @classmethod
    def known_card(cls,value):
        if value not in BY_ID: raise ValueError('Unknown card')
        return value

class CardSection(StrictModel):
    card_id: str
    orientation: Literal['upright','reversed']
    position: Literal['past','present','future']
    body: str = Field(min_length=1,max_length=2500)
    citations: list[str] = Field(min_length=1,max_length=20)

class DraftReport(StrictModel):
    sections: list[CardSection] = Field(min_length=3,max_length=3)
    summary: str = Field(min_length=1,max_length=2000)
    small_action: str = Field(min_length=1,max_length=500)

class ReadingResponse(StrictModel):
    session_id: UUID
    session_token: str | None = None
    status: str
    draws: list[Draw]
    events_url: str

class ReadingView(StrictModel):
    session_id: UUID
    status: str
    draws: list[Draw]
    mbti: str
    zodiac_id: str
    question: str
    error_code: str | None = None
    report: dict | None = None
