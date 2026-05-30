from dotenv import load_dotenv
from langchain.messages import HumanMessage, AIMessage
from langchain_core.messages import BaseMessage
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from transcript import get_transcript

load_dotenv()

# Shared across all users — keyed by video_id only
vectorstore_cache: dict[str, FAISS] = {}


# Memory store — keyed by session_id:video_id
# lives outside the chain, fully in our control
message_store: dict[str, list[BaseMessage]] = {}


def get_chat_history(video_id: str, session_id: str) -> list[BaseMessage]:
    key = f"{session_id}:{video_id}"
    if key not in message_store:
        message_store[key] = []
    return message_store[key]


def append_chat_history(
    video_id: str, session_id: str, history: list[BaseMessage]
) -> None:
    key = f"{session_id}:{video_id}"
    if key not in message_store:
        message_store[key] = []
    message_store[key].extend(history)


def get_vectorstore(video_id: str) -> FAISS:
    if video_id in vectorstore_cache:
        return vectorstore_cache[video_id]

    # 1. get transcript
    trascript = get_transcript(video_id)

    # 2. Split trascript into chunks(docs)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=60)
    docs = text_splitter.create_documents([trascript])

    # 3. Embed chunks docs into vectorstore
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore_cache[video_id] = vectorstore
    return vectorstore


def get_question_answer(video_id: str, session_id: str, question: str) -> str:
    try:
        # get vectorstore for the video_id
        vectorstore = get_vectorstore(video_id)

        # get retriever from vectorstore
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        # get llm with low temperature for deterministic responses
        llm = ChatOpenAI(temperature=0.2)

        # get chat history for the session_id and video_id
        chat_history = get_chat_history(video_id, session_id)

        # parser
        parser = StrOutputParser()
        # chain - 1: get history aware retriever
        # this rewrite user question using chat history so FAISS get a proper standalone question
        question_rewrite_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """given the conversation history and the follow up question, rewrite the follow up question to be a standalone question. if the follow up question is already standalone, then return the follow up question as it is.""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
            ]
        )

        if chat_history:
            chain = question_rewrite_prompt | llm | parser
            question = chain.invoke(
                {"question": question, "chat_history": chat_history}
            )

        retrieved_docs = retriever.invoke(question)
        retrieved_context = "\n\n".join([doc.page_content for doc in retrieved_docs])

        # answer prompt
        answer_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Answer the question based on the following context. 
                    And if you don't have any answer then say you don't know.\n\n
                    Context:
                    {context}\n\n""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
            ]
        )
        answer_chain = answer_prompt | llm | parser

        result = answer_chain.invoke(
            {
                "question": question,
                "context": retrieved_context,
                "chat_history": chat_history,
            }
        )
        append_chat_history(
            video_id,
            session_id,
            [
                HumanMessage(content=question),
                AIMessage(content=result),
            ],
        )
        return result

        # chain = get_qa_chain(video_id, session_id)
        # return chain.invoke(question)
    except Exception as e:
        print(e)
        return "Unable to get answer for the question. Please try again later."

    # "faiss-cpu>=1.14.2",
    # "fastapi>=0.136.3",
    # "langchain>=1.3.2",
    # "langchain-community>=0.4.2",
    # "langchain-core>=1.4.0",
    # "langchain-faiss>=0.1.1",
    # "langchain-openai>=1.2.2",
    # "langchain-text-splitters>=1.1.2",
    # "uvicorn>=0.48.0",
    # "youtube-transcript-api>=1.2.4",
