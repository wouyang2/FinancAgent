from pydantic import BaseModel
from typing import List, Optional
import datetime as dt
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage, RemoveMessage
from langchain_openai import ChatOpenAI

from state import FinanceSystemState

class Entity(BaseModel):
    name: str
    note: str

class ExtractContent(BaseModel):
    year: Optional[int]
    month: Optional[str]
    category: Optional[str]
    last_question_type: Optional[str]
    new_entity: List[Entity]