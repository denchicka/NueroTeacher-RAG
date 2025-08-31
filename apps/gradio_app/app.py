import os, sys, pathlib
import gradio as gr
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
load_dotenv()

from neuroteacher.services.indexing_service import IndexingService
from neuroteacher.services.rag_service import RAGService
from neuroteacher.utils.logger import get_logger, get_buffer_text
from neuroteacher.utils.config import load_models_config

logger = get_logger()
cfg = load_models_config()

def build_app(persist_path: str | None = None):
    idx = IndexingService(policy_path=os.getenv("SAFETY_POLICY_PATH"))
    rag = RAGService(persist_path=persist_path or os.getenv("CHROMA_DIR", "./data/chroma"))

    def refresh_logs():
        return get_buffer_text()

    def model_choices(vendor_value: str):
        try:
            return cfg["providers"][vendor_value]["models"]
        except Exception:
            return ["gigachat-2-lite"] if vendor_value == "gigachat" else ["gpt-4o-mini"]

    with gr.Blocks(title="NeuroTeacher RAG") as demo:
        gr.Markdown("# NeuroTeacher — RAG")

        with gr.Row():
            vendor = gr.Dropdown(choices=["openai", "gigachat"], value="gigachat", label="LLM")
            model = gr.Dropdown(choices=model_choices("gigachat"), value=model_choices("gigachat")[0], label="Модель")
            course = gr.Textbox(value="roblox", label="Курс")
            persist = gr.Textbox(value=rag.persist_path, label="Chroma")

        with gr.Tab("DOCX"):
            docx_file = gr.File(label="Файл .docx", file_types=[".docx"])
            btn_docx = gr.Button("Индексировать")
            log1 = gr.Markdown()

        with gr.Tab("Google Docs"):
            gdoc_url = gr.Textbox(label="URL Google Docs")
            btn_gdoc = gr.Button("Индексировать")
            log2 = gr.Markdown()

        query = gr.Textbox(label="Вопрос", lines=2)
        ask = gr.Button("Спросить", variant="primary")
        answer = gr.Markdown()
        logs_box = gr.Textbox(label="Логи", lines=10, interactive=False)

        def do_docx(file, course_key, persist_dir):
            try:
                if not file:
                    return "❗ Загрузите .docx файл."
                docs = idx.load_docx(file.name, course_key=course_key)
                rag.persist_path = persist_dir or rag.persist_path
                rag.index(docs)
                return f"✅ Загружено {len(docs)} чанков."
            except Exception as e:
                logger.exception("docx ingest failed: %s", e)
                return f"❗ Ошибка: {e}"

        def do_gdoc(url, course_key, persist_dir):
            try:
                if not url:
                    return "❗ Введите ссылку на Google Docs."
                docs = idx.load_gdocs(url, course_key=course_key)
                rag.persist_path = persist_dir or rag.persist_path
                rag.index(docs)
                return f"✅ Загружено {len(docs)} чанков (GDocs)."
            except Exception as e:
                logger.exception("gdoc ingest failed: %s", e)
                return f"❗ Ошибка: {e}"

        def do_ask(q, vndr, mdl, course_key):
            try:
                res = rag.answer(q, course=course_key, vendor=vndr, model=mdl)
                return f"**Ответ:**\n\n{res['answer']}\n\n— Источников: {len(res.get('sources', []))}"
            except Exception as e:
                logger.exception("ask failed: %s", e)
                return f"❗ Ошибка: {e}"

        btn_docx.click(do_docx, inputs=[docx_file, course, persist], outputs=[log1]).then(fn=refresh_logs, inputs=None, outputs=logs_box)
        btn_gdoc.click(do_gdoc, inputs=[gdoc_url, course, persist], outputs=[log2]).then(fn=refresh_logs, inputs=None, outputs=logs_box)
        ask.click(do_ask, inputs=[query, vendor, model, course], outputs=[answer]).then(fn=refresh_logs, inputs=None, outputs=logs_box)

        vendor.change(lambda v: gr.update(choices=model_choices(v), value=model_choices(v)[0]), inputs=vendor, outputs=model)

    return demo

if __name__ == "__main__":
    demo = build_app(persist_path=os.getenv("CHROMA_DIR", "./data/chroma"))
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
