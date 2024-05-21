import pysolr
import ollama
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import List, Dict
import re
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
# Connect to Solr
#solr = pysolr.Solr('http://localhost:8983/solr/core1/', always_commit=True)
app = FastAPI()

llm = ChatOpenAI(model="gpt-4o-2024-05-13",api_key="")

#embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
# load it into Chroma
db = Chroma(persist_directory="embeddings2\\",embedding_function=OpenAIEmbeddings(model="text-embedding-3-small",api_key=""))
#db = Chroma(persist_directory="embeddings\\",embedding_function=embedding_function)
def extract_text_between_patterns(text, start_pattern, end_pattern):
    start_index = text.find(start_pattern)
    if start_index != -1:
        start_index += len(start_pattern)
        end_index = text.find(end_pattern, start_index)
        if end_index != -1:
            return text[start_index:end_index].strip()
    return ""
def answer_question(question):
    # Query Solr based on the user input question
    docs = db.similarity_search(question, 50)
    
    # Preprocess messages for Mistral
    messages = preprocess_message(question, docs)
    
    # Launch Ollama and communicate with it
    
    result= ollama.chat(
        model='mistral',
        messages=messages,
        
    )

    # Print Mistral responses
    return result

def preprocess_message(question, docs):
    # Preprocess user input question
    messages = []
    instruction = {'role': 'system', 'content': "You are a helpful assistant who will answer questions that the user asks based on the dialogue provided."}
    user_input = {'role': 'user', 'content': question}
    messages.append(instruction)
    messages.append(user_input)
    summaries = []
    dialogues = []
    #pattern = re.compile(r'Summary:(.*)')
    for result in docs:
       

        
        # Extract text between "Name:" and "Dialogue:"
        #match = pattern.search( result.page_content)
        summary = ""
        name = extract_text_between_patterns(result.page_content, '\nName: ', 'Dialogue:')
        dialogue = extract_text_between_patterns(result.page_content, '\nDialogue: ', 'Quest Type:')
        if(name!=None and name!="" and dialogue != None and dialogue != ""):dialogues.append(f"{name}: {dialogue}")
        '''
        if match:
            summary = match.group(1).strip()
        else :
            print("Substring 'Summary:' not found.")
        
        if(summary not in summaries and len(summaries)<30):summaries.append(summary)
        '''
    print(len(dialogues))
    print(dialogues)
    messages.append({'role': 'assistant', 'content': f"{dialogues}"})
    return messages
from langchain import hub
prompt = hub.pull("rlm/rag-prompt")
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)
retriever = db.as_retriever()
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)   
    

def chatbot_response(question):
    # Query Solr based on the user input question
    
    results = answer_question(question)

    # Preprocess messages for Mistral
    
    
    print(f"\n{question}\n")
    # Launch Ollama and communicate with it
    
    if(len(results)<3):
        return " Sorry, I didn't understand that!"
    else:
        response = ollama.chat(
        model="mistral",
        messages=results
        )   
        return response
    
    '''
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=messages
    )
    '''
    
    
    
   
    # Print Mistral responses
   
        
    


@app.post("/discord")
async def api(request: Request) -> JSONResponse:
    
    data = await request.json()
    question = data['message']
    
    
    botresponse = rag_chain.invoke(question)
    response=""
    '''
    if(botresponse == " Sorry, I didn't understand that!"):
        response = botresponse
    else:
        response = botresponse["message"]["content"]
    '''
    return JSONResponse(content=botresponse)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=5000)
