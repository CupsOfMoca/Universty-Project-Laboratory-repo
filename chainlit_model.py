import pysolr
import ollama
import chainlit as cl
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi import FastAPI
from chainlit.server import app
from openai import OpenAI
client = OpenAI(api_key="")

# Connect to Solr
solr = pysolr.Solr('http://localhost:8983/solr/core1/', always_commit=True)
app = FastAPI()
def load_names_from_file(file_path):
    names = set()
    with open(file_path, 'r') as f:
        for line in f:
            names.add(line.strip())
    return names
names = load_names_from_file("unique_names.txt")
def remove_common_elements(user_input):
    
    common_elements = ["what", "who", "where", "when", "why", "how", "is", "in", "the", "a", "an", "quest", "quests","happens","happened","story", "meet", "do","does","did","he","she","it","her","him", "can", "I","me","my","event","archon","world","commission","summarize"]
    cleaned_input = ' '.join(word for word in user_input.content.split() if word.lower().strip("?!.,") not in common_elements)
    
    return cleaned_input.strip()

def construct_word_queries(user_input, question):
    # Split the user input into words
    words = user_input.split()
    word_queries = []
    
    # Construct Solr queries for each word
    for word in words:
        # Treat "AND" as an OR operator in the query
        
        word = word.strip("?!.,")
        word = word.strip("'s")
        
        if word.lower() == "and":
            word_queries.append(" OR ")
        elif(word.lower() in names ):
           word_queries.append(f'Name:*{word}*')
           
        else: word_queries.append(f'text:*{word}*')
    message = question.content.lower().strip("?!.,")
    if("story quest" in message): word_queries.append("Quest_Type:\"Story\"")
    if("event quest" in message): word_queries.append("Quest_Type:\"Event\"")
    if("archon quest" in message): word_queries.append("Quest_Type:\"Archon\"")
    if("commission" in message): word_queries.append("Quest_Type:\"Commission\"")
    if("world quest" in message): word_queries.append("Quest_Type:\"World\"")
    # Join the word queries with AND/OR operators as needed
    final_query = ' AND '.join(word_queries)
    print(final_query)
    
    
    return final_query


def query_solr(user_input):
    # Remove common question elements from the user input
    cleaned_input = remove_common_elements(user_input)
    
    # Construct Solr query to search for the cleaned input in the "text" column
    query = construct_word_queries(cleaned_input,user_input)
    print(query)
    # Send query to Solr
    query_params = {
        'q': query,
        'rows':30,  # Set the number of rows to retrieve
        "fl": "Summary, Name, Dialogue" 
    }
    results = solr.search(**query_params)
  
    #print("Solr server response:", results.raw_response)
    return results


def preprocess_message(question):
    # Preprocess user input question
    
    solr_messages = []
    solr_messages.append({"role": "system", "content": "You are a helpful assistant answering questions about java spring."})
    user_input =   {"role": "user", "content": question.content}
    solr_messages.append(user_input)
    '''
    # Preprocess Solr results
    repeat = []
    dialogues = ""
    for result in solr_results:
        # Extract relevant information from Solr results
        objective = result.get('Objective', [''])[0]
        name = result.get('Name', [''])[0]
        dialogue = result.get('Dialogue', [''])[0]
        summary = result.get('Summary', [''])[0]
        #print("Summary: "+summary)
        message =""
        # Create a message for each relevant piece of information
        #if objective:
            #message+=(" Current Objective: "+objective)
            #solr_messages.append({'role': 'system', 'content':  question+"Current Objective: "+objective})
        if name:
            message+=(f"{name}: ")
            
            #solr_messages.append({'role': 'system', 'content': question+"Currently Talking: "+name})
        if dialogue:
            message+=(f"{dialogue}\n")
            
            #solr_messages.append({'role': 'system', 'content': question+"What they've said: "+dialogue})
        #if(summary not in repeat and summary not in [None,""] and len(repeat)<40): 
            #solr_messages.append({"role": "assistant", "content": summary})
            #repeat.append(summary)
        #repeat.append(message)
        #solr_messages.append(message)
        dialogues+=message
        
    # Combine user input and Solr results into a single message list
    solr_messages.append({"role": "assistant", "content": dialogues})
    solr_messages.append({"role": "user", "content": "Please answer the question."})
    
    file_path = "tokencount.txt"
    with open(file_path, "w") as file:
            for message in solr_messages:
                file.write(f"{message}")
    with open("questions.txt", "a") as file:
        file.write(f"{question}\n")
    
    '''
    return solr_messages

def chatbot_response(question):
    # Query Solr based on the user input question
    #solr_results = query_solr(question)

    # Preprocess messages for Mistral
    messages = preprocess_message(question)
    
    print(f"\n{question}\n")
    # Launch Ollama and communicate with it
    print(messages)
   
    
    response = client.chat.completions.create(
        model="gpt-4o-2024-05-13",
        messages=messages
    )
    '''
    
    response = ollama.chat(
        model="llama2",
        messages=messages
    )
    '''
    
    
    
    # Print Mistral responses
    return response
    


# Create a ChatUI instance

@cl.on_message
async def main(message: cl.Message):
    
    await cl.Message(
        #content=chatbot_response(message)["message"]["content"]
        content=chatbot_response(message).choices[0].message.content,
    ).send()

'''
@app.post("/api")
async def api(request: Request):
    data = await request.json()
    message = cl.Message(content=data['message'])
    response = chatbot_response(message)["message"]["content"]
    
    return HTMLResponse(response)

@app.get("/discord")
def discord(request: Request):
    print(request.headers)
    
    response = chatbot_response("Who is Mona?")["message"]["content"]
    htmlcontent =  f"""
    <html>
        <head>
            <title>{response}</title>
        </head>
        <body>
            <h1>{response}</h1>
        </body>
    </html>
    """
    return HTMLResponse(content=htmlcontent,status_code=200)
'''