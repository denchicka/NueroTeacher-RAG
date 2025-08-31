from neuroteacher.core.contracts import LLM
try:
    from langchain_openai import ChatOpenAI
except Exception:
    ChatOpenAI = None

class OpenAIChatLLM(LLM):
    def __init__(self, name: str = "gpt-4o-mini", temperature: float = 0.2):
        if ChatOpenAI is None: raise RuntimeError("Установите langchain-openai")
        self.name = name; self.temperature = temperature; self._llm = ChatOpenAI(model=name, temperature=temperature)
    def chat(self, messages: list[dict]) -> dict:
        res = self._llm.invoke(messages); usage = {}
        try: usage = res.response_metadata.get("token_usage", {})
        except Exception: pass
        return {"content": getattr(res, "content", str(res)), "usage": usage}
