from langchain.vectorstores.chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter

from langchain.document_loaders import DirectoryLoader, TextLoader

import os
import subprocess
import mysql.connector
from dotenv import load_dotenv, find_dotenv

class SiteTrain:
    def __init__(self):
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
        os.environ['OPENAI_API_KEY'] = openaikey

    def start(self):
        try:
            self.crawl_site()
            loader = DirectoryLoader(
                "botengine/airmaxcmcrawl/output/",
                glob="**/*.txt",
                loader_cls=lambda path: TextLoader(path, encoding='utf-8'),
            )
            documents = loader.load()

            text_splitter = CharacterTextSplitter(
                chunk_size = 1024,
                chunk_overlap = 128,
            )
            texts = text_splitter.split_documents(documents)

            persist_directory = "botengine/db"

            embeddings = OpenAIEmbeddings()

            for text_chunk in self.chunk_texts(texts, max_batch_size=5000):
                vectordb = Chroma.from_documents(
                    documents=text_chunk,
                    embedding=embeddings,
                    persist_directory=persist_directory,
                )
                vectordb.persist()
            return 'ok'
        except:
            return 'error'

    def chunk_texts(self, texts, max_batch_size=5000):
        for i in range(0, len(texts), max_batch_size):
            yield texts[i:i + max_batch_size]

    def crawl_site(self):
        commands = "cd /home/ubuntu/chatbot_api/botengine/airmaxcmcrawl; scrapy crawl airmaxcm"
        result = subprocess.run(commands, shell=True, capture_output=True, text=True)