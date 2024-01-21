# from langchain.vectorstores import Chroma
# from langchain.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
# from langchain.embeddings import FastEmbedEmbeddings
# from langchain.schema.output_parser import StrOutputParser
# from langchain.document_loaders import PyPDFLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.schema.runnable import RunnablePassthrough
# from langchain.prompts import PromptTemplate
# from langchain.vectorstores.utils import filter_complex_metadata
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from pypdf import PdfReader
from PyPDF2 import PdfFileReader

from rag_builder.commons.utils import clear, load_prompt

import requests
from langchain_core.documents import Document
from langchain.prompts import ChatPromptTemplate
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from dotenv import load_dotenv

import logging

import fitz

load_dotenv()

class Assistant:
    
    def __init__(self) -> None:
        self.data = None
        self.prompt = self.initialize_prompt()
        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        self.memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
        self.initialized = False
        pass

    def initialize_knowledge(self, urls = list[str]):

        self.documents = self.read_urls(urls)
        self._chunk()
        self.embed_and_store()

        self.conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(),
            memory=self.memory
        )

        self.initialized = True
    def extract_information(self, pdf_path:str):
        doc = fitz.open(pdf_path)
        for page in doc: 
            text = page.get_text() 
            print(text)

            

            # txt = ""
            # reader = PdfReader(pdf_path)
            # print(len(reader.pages))
            # page = reader.pages[0]
            # txt = page.extract_text()

            # print(txt)
            # return txt
        
    def read_urls(self, list_of_urls = list[str]) -> list[Document]:
        url_texts = []
        for url in list_of_urls:
            url_texts.append(self.read_url(url))

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
        )
        return text_splitter.create_documents(url_texts)


    def read_url(self, url) -> str:

        res = requests.get(url)
        return res.text

            
    def _chunk(self):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        self.chunks = text_splitter.split_documents(self.documents)
        return self.chunks

    def embed_and_store(self):
        logging.debug("Loading documents into FAISS...")
        self.vectorstore = FAISS.from_documents(self.chunks, embedding=OpenAIEmbeddings())


    def initialize_prompt(self):
        template = load_prompt("rag")
        prompt = ChatPromptTemplate.from_template(template)

        return prompt
    
    def ask(self, query: str) -> str:
        """
        Asks the assistant a question, returns an answer related to the text.
        """

        if not self.initialized:
            raise RuntimeError("You have not run 'Assistant.initialize()' yet, so the vector store is empty.")
        logging.debug("Begun query")
        result = self.conversation_chain.invoke({"question": query})
        answer = result["answer"]
        print(answer)
        logging.debug("Ended query")

        return answer

    



       