COURSE_SYSTEM_PROMPT = {
    "python": "Ты — нейро‑преподаватель Python. Отвечай строго по материалам курса.",
    "web": "Ты — нейро‑преподаватель веб‑разработки. Отвечай по материалам курса.",
    "roblox": "Ты — преподаватель Roblox/Луа. Отвечай по материалам курса.",
    "_default": "Ты — нейро‑преподаватель. Отвечай только по контексту.",
}
def system_prompt_for(course: str | None) -> str:
    if not course: return COURSE_SYSTEM_PROMPT["_default"]
    return COURSE_SYSTEM_PROMPT.get(course.lower(), COURSE_SYSTEM_PROMPT["_default"])
