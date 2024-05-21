import pysolr
import ollama
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import List, Dict

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
    
    common_elements = ["what", "who", "where", "when", "why", "how", "is", "in", "the", "a", "an", "quest", "quests","happens","happened","story", "meet", "do","does","did","he","she","it","her","him", "can", "I","me","my","event","archon","world","commission","summarize","buzzy","Bashi","bushy","arona","aruna","arana"]
    cleaned_input = ' '.join(word for word in user_input.split() if word.lower().strip("?!.:,") not in common_elements).replace("answer this","")
    
    return cleaned_input.strip()

def construct_word_queries(user_input, question):
    # Split the user input into words
    words = user_input.split()
    word_queries = []
    
    # Construct Solr queries for each word
    for word in words:
        # Treat "AND" as an OR operator in the query
        if word == "purina": word = "furina"
        if word.lower() in { "arcon","arkon"}: word = "archon"
        word = word.strip("?!.:,")
        word = word.strip(str("'s"))
        
        if word.lower() == "and":
            word_queries.append(" OR ")
        elif(word.lower() in names ):
           word_queries.append(f'Name:*{word}*')
           
        else: word_queries.append(f'text:*{word}*')
    message = question.lower().strip("?!.:,").replace("answer this","")
    if("story quest" in message): word_queries.append("Quest_Type:\"Story\"")
    if("event quest" in message): word_queries.append("Quest_Type:\"Event\"")
    if("archon quest" in message): word_queries.append("Quest_Type:\"Archon\"")
    if("commission" in message): word_queries.append("Quest_Type:\"Commission\"")
    if("world quest" in message): word_queries.append("Quest_Type:\"World\"")
    # Join the word queries with AND/OR operators as needed
    #final_query = ' AND '.join(word_queries)
    final_query = f"text:\"{user_input}\"~10"
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
        'rows':1000,  # Set the number of rows to retrieve
        "fl": "Summary, Name, Dialogue" 
    }
    results = solr.search(**query_params)
  
    #print("Solr server response:", results.raw_response)
    return results


def preprocess_message(question, solr_results):
    # Preprocess user input question
    
    solr_messages = []
    solr_messages.append({"role": "system", "content": "You are a helpful assistant answering questions related to Genshin Impact given by the user."})
    wakewords = {"arona", "aruna","arana"}
    cleaned_question = ""
    for word in wakewords:
         if(word in question) :cleaned_question = question.replace(word,"")
    
    
    print(cleaned_question.replace("answer this","").strip("?!.:,"))
    
    user_input =   {"role": "user", "content": f"{cleaned_question}?"}
    solr_messages.append(user_input)
    # Preprocess Solr results
    repeat = []
    
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
        if(summary not in repeat and summary not in [None,""] and len(repeat)<20): 
            #solr_messages.append({"role": "assistant", "content": summary})
            repeat.append(summary)
        
        #solr_messages.append(message)
    # Combine user input and Solr results into a single message list
    summ = ""
    for summary in repeat:
        summ+=f"{summary}\n"
    if(summ != ""):solr_messages.append({"role": "assistant", "content": summ})
    print(summ)
    solr_messages.append({"role": "user", "content": "Please answer the question."})
    
    file_path = "tokencount.txt"
    with open(file_path, "w") as file:
            for message in solr_messages:
                file.write(f"{message}")
    with open("questions.txt", "a") as file:
        file.write(f"{question}\n")
    
    return solr_messages

def chatbot_response(question):
    # Query Solr based on the user input question
    solr_results = query_solr(question)

    # Preprocess messages for Mistral
    messages = preprocess_message(question, solr_results)
    
    print(f"\n{question}\n")
    # Launch Ollama and communicate with it
    print(messages)
    if(len(messages)<4):
        return " Sorry, I didn't understand that!"
    else:
        response = ollama.chat(
        model="mistral",
        messages=messages
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
    print(question)
    botresponse = chatbot_response(question)
    response=""
    print(botresponse)
    if(botresponse == " Sorry, I didn't understand that!"):
        response = botresponse
    else:
        response = botresponse["message"]["content"]
    return JSONResponse(content=response)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=5000)
