from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from dotenv import find_dotenv, load_dotenv

# Read and print the sample summary file
with open('sample_summary.txt', 'r') as f:
    sample_text = f.read()

load_dotenv(find_dotenv())

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that summarizes text."),
    ("human", "{text}")
])

chat = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

chain = prompt | chat

response = chain.invoke({"text": sample_text})

print(response)


