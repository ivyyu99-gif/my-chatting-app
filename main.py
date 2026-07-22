# -*- coding: utf-8 -*-
"""
Solar API(solar-open2)를 사용하는 스트림릿 AI 채팅앱
- openai 라이브러리로 Upstage Solar API를 호출합니다.
- API 키는 코드에 직접 쓰지 않고, 스트림릿의 secrets 금고에서 불러옵니다.
- 답변은 스트리밍으로 실시간 출력됩니다.
"""

import streamlit as st
from openai import OpenAI

# ------------------------------------------------------------
# 1. 페이지 기본 설정
# ------------------------------------------------------------
st.set_page_config(page_title="Solar AI 채팅", page_icon="💬")
st.title("💬 Solar AI 채팅")

# ------------------------------------------------------------
# 2. Solar API 클라이언트 만들기
#    - api_key는 절대 코드에 직접 쓰지 않고 secrets에서 가져옵니다.
#    - .streamlit/secrets.toml 또는 스트림릿 클라우드의 Secrets 설정에
#      아래처럼 넣어두면 됩니다.
#      SOLAR_API_KEY = "여기에_실제_키"
# ------------------------------------------------------------
try:
    api_key = st.secrets["SOLAR_API_KEY"]
except Exception:
    st.error("SOLAR_API_KEY가 설정되어 있지 않아요. 스트림릿 secrets에 키를 등록해 주세요.")
    st.stop()

client = OpenAI(
    api_key=api_key,
    base_url="https://api.upstage.ai/v1",  # Solar API 주소
)

# 시스템 프롬프트: AI의 성격을 정해줍니다.
SYSTEM_PROMPT = (
    "너는 따뜻하고 친절한 데이터 분석 선생님이야. 반드시 순수 한국어로만 답해"
)

# ------------------------------------------------------------
# 3. 세션(session_state)에 대화 기록 저장하기
#    - 새로고침 전까지는 대화가 계속 이어집니다.
#    - 화면에는 system 메시지는 보여주지 않고, user/assistant만 보여줍니다.
# ------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []  # [{"role": "user"/"assistant", "content": "..."}]

# 지금까지의 대화를 말풍선으로 화면에 그려주기
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------------------------------------------------
# 4. 채팅 입력창
# ------------------------------------------------------------
user_input = st.chat_input("메시지를 입력하세요...")

if user_input:
    # 4-1. 사용자 메시지를 기록하고 화면에 표시
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 4-2. Solar API에 보낼 메시지 목록 만들기 (시스템 프롬프트 + 전체 대화 기록)
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    api_messages.extend(st.session_state.messages)

    # 4-3. AI 답변을 스트리밍으로 받아서 실시간으로 보여주기
    with st.chat_message("assistant"):
        placeholder = st.empty()  # 실시간으로 글자를 채워 넣을 빈 공간
        full_answer = ""

        try:
            stream = client.chat.completions.create(
                model="solar-open2",  # 모델 이름은 그대로 사용
                messages=api_messages,
                stream=True,  # 스트리밍 켜기
                # reasoning_effort를 'none'으로 주면 추론(생각) 단계를 건너뛰고
                # 더 빠르게 답을 받을 수 있습니다. (temperature가 아닙니다!)
                reasoning_effort="none",
            )

            # 스트림에서 오는 조각(chunk)들을 하나씩 이어붙여서 보여주기
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    full_answer += delta.content
                    placeholder.markdown(full_answer + "▌")  # 커서 느낌 표시

            placeholder.markdown(full_answer)  # 마지막에 커서 제거하고 최종본 표시

        except Exception:
            # 에러가 나면 개발자용 에러 메시지 대신 친절한 안내 문구를 보여줍니다.
            full_answer = (
                "앗, 지금은 답변을 가져오는 데 문제가 생겼어요. 🙏\n\n"
                "잠시 후에 다시 시도해 주시겠어요? "
                "계속 문제가 있다면 API 키나 인터넷 연결 상태를 확인해 주세요."
            )
            placeholder.markdown(full_answer)

    # 4-4. AI 답변도 대화 기록에 저장 (다음 질문에 이어서 기억하도록)
    st.session_state.messages.append({"role": "assistant", "content": full_answer})
