from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os

load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")

# Set up Groq LLM (LLaMA3-8B)
llm = ChatGroq(
    groq_api_key=groq_key,  
    model_name="llama3-8b-8192" ,
    temperature = 0.3 # lower for more factual answers
)

# Example prompt template for summarizing themes
prompt = PromptTemplate(
    input_variables=["extracted_answers"],
    template="""
You are an AI assistant helping analyze a collection of document responses.
Given the extracted answers from multiple documents:

{extracted_answers}

Identify and summarize common themes. Label each theme (e.g., "Theme 1 – ..."), and cite relevant document IDs wherever applicable.
Be concise and structured. Format:

Theme 1 – [Theme Name]:
DOC001, DOC003: Explanation

Theme 2 – [Theme Name]:
DOC002: Explanation
"""
)

# LangChain chain
theme_summarizer_chain = LLMChain(llm=llm, prompt=prompt)


def summarize_themes(doc_answers):
    formatted_input = "\n".join([f"{d['doc_id']}: {d['answer']}" for d in doc_answers])
    themes = theme_summarizer_chain.run({"extracted_answers": formatted_input})
    return themes




# # Format into one string
# formatted_input = "\n".join([f"{d['doc_id']}: {d['answer']}" for d in doc_answers])

# # Run synthesis
# themes = theme_summarizer_chain.run({"extracted_answers": formatted_input})
# print("🎯 Synthesized Themes:\n", themes)
