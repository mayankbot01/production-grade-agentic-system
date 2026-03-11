import os
from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models import BaseChatModel


class LLMService:
    """Service for interacting with LLM providers via LangChain."""

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._llm: Optional[BaseChatModel] = None

    def get_llm(self) -> BaseChatModel:
        """Initialize and return the LLM instance."""
        if self._llm is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            self._llm = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=api_key,
            )
        return self._llm

    async def ainvoke(self, messages: List[BaseMessage]) -> AIMessage:
        """Asynchronously invoke the LLM with a list of messages."""
        llm = self.get_llm()
        response = await llm.ainvoke(messages)
        return response

    def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        """Synchronously invoke the LLM with a list of messages."""
        llm = self.get_llm()
        return llm.invoke(messages)

    async def astream(self, messages: List[BaseMessage]):
        """Asynchronously stream tokens from the LLM."""
        llm = self.get_llm()
        async for chunk in llm.astream(messages):
            yield chunk

    def build_messages(
        self,
        system_prompt: str,
        history: List[BaseMessage],
        user_message: str,
    ) -> List[BaseMessage]:
        """Build a complete message list with system prompt, history, and new user message."""
        messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]
        messages.extend(history)
        messages.append(HumanMessage(content=user_message))
        return messages
