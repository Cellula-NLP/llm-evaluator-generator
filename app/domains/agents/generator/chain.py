from langchain_core.output_parsers import StrOutputParser

from app.domains.agents.generator.prompts import build_generator_prompt
from app.infrastructure.llm.base import ILLMProvider


def build_generator_chain(llm_provider: ILLMProvider):
    return build_generator_prompt() | llm_provider.generator | StrOutputParser()