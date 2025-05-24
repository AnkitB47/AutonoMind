# --- agents/translate_agent.py ---
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

def translate_response(text, target_lang):
    if target_lang == "en":
        return text
    prompt = PromptTemplate.from_template("Translate this to {lang}: {text}")
    chain = LLMChain(llm=OpenAI(), prompt=prompt)
    return chain.run(lang=target_lang, text=text)