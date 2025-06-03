# --- agents/translate_agent.py ---
from langchain_community.llms import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain


def translate_response(text: str, target_lang: str) -> str:
    if target_lang.lower() == "en":
        return text

    prompt = PromptTemplate.from_template("Translate this to {lang}: {text}")
    chain = LLMChain(llm=OpenAI(), prompt=prompt)

    try:
        return chain.run(lang=target_lang, text=text)
    except Exception as e:
        return f"⚠️ Translation failed: {str(e)}"
