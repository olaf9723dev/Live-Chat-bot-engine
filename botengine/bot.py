import os
import gradio as gr
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_openai import OpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
import warnings
from openai import OpenAI as open_AI
from dotenv import load_dotenv, find_dotenv
import mysql.connector

          
PERSIST_DIRECTORY = "botengine/db"
warnings.filterwarnings("ignore", category=DeprecationWarning)


class BotAnswer:
    def __init__(self, question):
        self.question = question
        connection = mysql.connector.connect(
                port=3306,
                user="dbadmin",  
                password="password",  
                database="livehelp_db",
                host="srv590123.hstgr.cloud"
            )
        cursor = connection.cursor(dictionary=True)
        select_query = "SELECT * FROM livehelp_settings WHERE name = %s"
        query_value = ("OpenAIKey",)
        cursor.execute(select_query, query_value)
        result = cursor.fetchone()

        openaikey  = result['value']

        self.CLIENT = open_AI(api_key= openaikey)
        os.environ['OPENAI_API_KEY'] = openaikey

    def start(self):
        question = self.question
        answer = self.get_answer(f" {question} ")

        return answer

    def get_pre_answer(self, question="Hi"):
        try:
            completion = self.CLIENT.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system", 
                            "content": (
                                            "You are a support assistant for Company. Greet clients warmly, "
                                            "using the provided custom data. If a question is outside the scope of the company's services, "
                                        )
                        },
                        {
                            "role": "user", 
                            "content": question
                        },
                    ],
                    stream= True
                )
            linetext = ''
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    linetext = linetext + chunk.choices[0].delta.content
            return linetext
        except:
            return "No"

    def get_answer(self, question = "Hi"):
        embeddings = OpenAIEmbeddings()

        db = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=embeddings,
        )
        memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=False,
        )

        qa = ConversationalRetrievalChain.from_llm(
            llm=OpenAI(temperature=0, max_tokens=-1),
            chain_type="stuff",
            retriever = db.as_retriever(),
            memory=memory,
            get_chat_history=lambda h: h,
            verbose=False,
        )

        res = qa.invoke(
            {
                "question": f"{question} : if you dont find correct answer, respond only with 'No' and do not make up an answer.",
                "chat_history":[],
            }
        )

        if res.get('answer', '').strip() != "No":
            return res.get('answer', '')
        else:
            pre_answer = self.get_pre_answer(question)
            return pre_answer