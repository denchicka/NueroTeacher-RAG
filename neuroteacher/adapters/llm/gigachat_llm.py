from __future__ import annotations
import os, base64
from neuroteacher.core.contracts import LLM

try:
    from langchain_gigachat import GigaChat  # LangChain wrapper over gigachat SDK
except Exception:
    GigaChat = None


class GigaChatLLM(LLM):
    """Адаптер GigaChat c явной передачей credentials/scope + гибким SSL.

    Читает переменные окружения (или задавайте их программно до импорта адаптера):
      - GIGACHAT_AUTHORIZATION   - base64("CLIENT_ID:CLIENT_SECRET")
        (либо задайте GIGACHAT_CLIENT_ID/GIGACHAT_CLIENT_SECRET)
      - GIGACHAT_SCOPE           - "GIGACHAT_API_PERS" (личный) или "GIGACHAT_API_CORP" (корп.)
      - GIGACHAT_VERIFY_SSL      - "false" для отключения строгой проверки (по умолчанию false)
      - GIGACHAT_CA_BUNDLE       - путь к PEM (если нужен свой корневой сертификат)

    Примечание: 401 Unauthorized почти всегда означает
    *непереданные credentials* или *неверный scope*.
    """

    def __init__(self, name: str = "gigachat", temperature: float = 0.2):
        if GigaChat is None:
            raise RuntimeError("Установите langchain-gigachat")
        self.name = name
        self.temperature = temperature

        # --- Credentials ---
        credentials = os.getenv("GIGACHAT_AUTHORIZATION")
        if not credentials:
            cid = os.getenv("GIGACHAT_CLIENT_ID")
            csec = os.getenv("GIGACHAT_CLIENT_SECRET")
            if cid and csec:
                credentials = base64.b64encode(f"{cid}:{csec}".encode()).decode()
        if not credentials:
            raise RuntimeError(
                "GigaChat: не заданы credentials. Установите GIGACHAT_AUTHORIZATION (base64) \n"
                "или GIGACHAT_CLIENT_ID/GIGACHAT_CLIENT_SECRET."
            )

        scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")

        # --- SSL toggles ---
        verify_env = os.getenv("GIGACHAT_VERIFY_SSL", "false").strip().lower()
        verify_ssl = verify_env not in ("0", "false", "no")
        ca_bundle = os.getenv("GIGACHAT_CA_BUNDLE")
        if ca_bundle:
            os.environ.setdefault("SSL_CERT_FILE", ca_bundle)
        if not verify_ssl:
            os.environ.setdefault("PYTHONHTTPSVERIFY", "0")

        # Инициализируем клиента, учитывая различия версий
        client = None
        last_err = None
        for kw in (
            dict(temperature=temperature, credentials=credentials, scope=scope, verify_ssl_certs=verify_ssl, model=name),
            dict(temperature=temperature, credentials=credentials, scope=scope, verify_ssl=verify_ssl, model=name),
            dict(temperature=temperature, credentials=credentials, scope=scope, verify=verify_ssl, model=name),
            dict(temperature=temperature, credentials=credentials, scope=scope, model=name),
        ):
            try:
                client = GigaChat(**kw)
                break
            except TypeError as e:
                last_err = e
                continue
        if client is None:
            raise RuntimeError(f"GigaChat: несовместимые параметры конструктора: {last_err}")
        self._llm = client

    def chat(self, messages: list[dict]) -> dict:
        # В gigachat чаще всего достаточно plain-text
        joined = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        try:
            if hasattr(self._llm, "invoke"):
                out = self._llm.invoke(joined)
                content = getattr(out, "content", str(out))
            else:
                out = self._llm([{ "role": "user", "content": joined }])  # type: ignore
                content = getattr(out, "content", str(out))
            return {"content": content, "usage": {}}
        except Exception as e:
            msg = str(e)
            hint = ""
            if "401" in msg or "Unauthorized" in msg:
                hint = (
                    "\n\nПодсказка: проверьте GIGACHAT_AUTHORIZATION (или CLIENT_ID/CLIENT_SECRET) и GIGACHAT_SCOPE\n"
                    "Обычно scope = GIGACHAT_API_PERS для личного доступа, либо GIGACHAT_API_CORP."
                )
            elif "CERTIFICATE_VERIFY_FAILED" in msg or "self-signed" in msg:
                hint = (
                    "\n\nПодсказка: для окружений с MITM: установите GIGACHAT_VERIFY_SSL=false или укажите GIGACHAT_CA_BUNDLE."
                )
            raise RuntimeError(f"GigaChat ошибка: {e}{hint}") from e
