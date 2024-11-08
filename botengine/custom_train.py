from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader

import os
import json
import sqlite3
import chromadb
from chromadb import Client
import mysql.connector
from chromadb.config import Settings
from dotenv import load_dotenv, find_dotenv

class CustomTrain:
    def __init__(self, custom_id):
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

        self.output_dir = "botengine/custom_output"
        self.custom_id = custom_id
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except Exception as e:
            print(e)

        for index, filename in enumerate(os.listdir(self.output_dir)):
            try:
                file_path = os.path.join(self.output_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(e)
                
    def start(self):
        try:
            self.read_custom_data()
            self.custom_train()
            return 'ok'
        except:
            return "error"

    def custom_train(self):
        try:
            custom_data_id = self.custom_id

            persist_directory = "botengine/db"

            embeddings = OpenAIEmbeddings()
            # Start >>> Delete Old Data
            vectordb = Chroma(
                collection_name="langchain",
                embedding_function=embeddings,
                persist_directory=persist_directory,
            )
            # Access the underlying ChromaDB collection
            collection = vectordb._collection
            # Retrieve all data from the collection
            db_data = collection.get()
            metadatas = db_data['metadatas']
            ids = db_data['ids']
            # Filter IDs based on custom_data_id in metadata
            ids_to_delete = [id for id, metadata in zip(ids, metadatas) if f'custom_{custom_data_id}' in metadata.get('source', '')]
            print(ids_to_delete)

            # Delete documents by their IDs
            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
            # >>> End
            
            # Start >>> Train Data
            loader = DirectoryLoader(
                "botengine/custom_output/",
                glob=f"**/custom_{custom_data_id}.txt",
                loader_cls=lambda path: TextLoader(path, encoding='utf-8'),
            )
            documents = loader.load()

            text_splitter = CharacterTextSplitter(
                chunk_size = 1024,
                chunk_overlap = 128,
            )
            texts = text_splitter.split_documents(documents)
                    
            for text_chunk in self.chunk_texts(texts, max_batch_size=5000):
                vectordb = Chroma.from_documents(
                    documents=text_chunk,
                    embedding=embeddings,
                    persist_directory=persist_directory,
                )
            # >>> End
        except Exception as e:
            print(e)

    def delete_collection(self, client, collection):
        collection_name = collection.name
        client.delete_collection(name=collection_name)
        print(f"Collection '{collection_name}' has been deleted.")

    def chunk_texts(self, texts, max_batch_size=5000):
        for i in range(0, len(texts), max_batch_size):
            yield texts[i:i + max_batch_size]

    def read_custom_data(self):
        try:
            connection = mysql.connector.connect(
                port=3306,
                user="dbadmin",  
                password="password",  
                database="livehelp_db",
                host="srv590123.hstgr.cloud"
            )
            cursor = connection.cursor(dictionary=True)
            select_query = "SELECT * FROM livehelp_settings WHERE name = %s"
            query_value = ("ChatBotData",)
            cursor.execute(select_query, query_value)
            result = cursor.fetchone()

            custom_data_string  = result['value']
            temp = []
            for index, row in enumerate(json.loads(custom_data_string)):
                with open (f"botengine/custom_output/custom_{row['id']}.txt", "w", encoding="utf-8") as file:
                    file.write(json.dumps(row))
        except Exception as e:
            print(e)