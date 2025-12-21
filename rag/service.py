import json
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from .settings import DB_PATH, EMBEDDING_MODEL, LLM_MODEL

class RAGService:
    def __init__(self):
        # 1. 임베딩 & DB (동일)
        self.embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        self.vectorstore = Chroma(
            persist_directory=str(DB_PATH),
            embedding_function=self.embeddings
        )
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4} 
        )
        
        # 2. LLM 설정 (동일)
        self.llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            temperature=0.4
        )
        
        # 3. 프롬프트 수정: "source" 필드를 채우라고 지시
        self.prompt = ChatPromptTemplate.from_template("""
            당신은 LoL 전담 코치입니다. 선수에게 강렬한 피드백을 주되, 반드시 **근거(Wiki)**를 포함해야 합니다.
            
            [상황 정보]
            - 내 챔피언: {my_champion}
            - 상대: {enemy_champion}
            - 시간/상황: {game_time} / {current_status}
            - 질문: {user_question}
            
            [참고 문서 (출처 포함)]
            {context}

            ---
            [미션]
            위 문서를 참고하여 JSON 리스트를 작성하세요.
            각 카드마다 **어떤 문서(Source)를 참고했는지** 반드시 명시해야 합니다.

            [JSON 필드]
            - "type": "⚠️위험", "🔥킬각", "💡운영" 등
            - "title": 제목
            - "coach_saying": 코치 멘트 (구어체)
            - "wiki_evidence": 위키 내용 요약
            - "source": 참고한 문서의 제목 (예: "다리우스", "가렌" 등 [문서: ...]에 적힌 내용)
            - "solution": 행동 지침

            [예시]
            [
                {{
                    "type": "⚠️위험",
                    "title": "E 거리 주지 마!",
                    "coach_saying": "지금 끌려가면 죽어. 뒤로 빼.",
                    "wiki_evidence": "다리우스 E 사거리 535, 방관 효과 보유",
                    "source": "다리우스",
                    "solution": "🚫 거리 벌리기"
                }}
            ]
            ---
            [JSON 데이터만 출력]:
        """)

        self.chain = (
            {
                "context": RunnablePassthrough(), # 여기로 들어가는 텍스트를 아래 메서드에서 조작함
                "my_champion": RunnablePassthrough(),
                "enemy_champion": RunnablePassthrough(),
                "game_time": RunnablePassthrough(),
                "current_status": RunnablePassthrough(),
                "user_question": RunnablePassthrough(),
            }
            | self.prompt
            | self.llm
        )

    def provide_feedback(self, context_data):
        search_query = f"{context_data.my_champion} {context_data.enemy_champion} 상대법 {context_data.current_status}"
        if context_data.user_question:
            search_query += f" {context_data.user_question}"
            
        print(f"🔍 코치 검색: {search_query}")
        
        # 1. 문서 검색
        retrieved_docs = self.retriever.invoke(search_query)
        
        # 2. [핵심 수정] 문서 내용에 "출처 태그" 붙이기
        # 기존: 그냥 텍스트만 합침
        # 수정: "📄 [문서: 다리우스]\n내용..." 형식으로 만듦
        formatted_docs = []
        for doc in retrieved_docs:
            # 메타데이터에서 파일명(source) 가져오기 (없으면 '알수없음')
            source_name = doc.metadata.get("source", "알 수 없음")
            content = doc.page_content
            formatted_docs.append(f"📄 [문서: {source_name}]\n{content}")
            
        context_text = "\n\n".join(formatted_docs)
        
        # 3. LLM에게 전달
        response = self.chain.invoke({
            "context": context_text,
            "my_champion": context_data.my_champion,
            "enemy_champion": context_data.enemy_champion,
            "game_time": context_data.game_time,
            "current_status": context_data.current_status,
            "user_question": context_data.user_question or "상황 판단 부탁해"
        })
        
        return response.content

rag_service = RAGService()