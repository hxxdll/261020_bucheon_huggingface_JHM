"""
냉장고 털이 셰프 (간단 버전)

사진 한 장 → 재료 인식 → 요리 제안. 그게 전부.

    pip install gradio groq openai python-dotenv
    python fridge_simple.py

.env:
    GROQ_API_KEY=gsk_...
    HF_TOKEN=hf_...
"""

import base64
import mimetypes
import os

import gradio as gr
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI

import io
from PIL import Image

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
hf_client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN"),
)
print("TOKEN:", (os.getenv("HF_TOKEN") or "없음")[:10])
VISION_MODEL = "deepseek-ai/DeepSeek-V4.1-Flash-1017:novita"
GROQ_MODEL = "openai/gpt-oss-20b"

CHEF_PROMPT = """너는 30년 경력의 셰프다. 주어진 재료만으로 만들 수 있는 요리를 2~3개 제안한다.
각 요리마다 사용하는 재료, 조리 시간, 순서를 번호로 알려준다.
없는 재료를 사 오라고 하지 않는다. 기본 조미료는 집에 있다고 가정한다.
열정적이고 다정한 주방 말투로, 한국어로 답한다."""


def cook(image_path):
    if not image_path:
        yield "사진을 올려주세요."
        return


    img = Image.open(image_path).convert("RGB")
    img.thumbnail((1024, 1024))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    data_url = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

    yield "사진을 들여다보는 중..."
    try:
        res = hf_client.chat.completions.create(
            model=VISION_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text":
                        "이 사진에 보이는 식재료를 한국어로 나열해줘. "
                        "쉼표로 구분한 목록만 출력하고 설명은 붙이지 마."},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }],
            max_tokens=1500,
        )
        items = res.choices[0].message.content.strip()
        if not items:
            yield f"재료를 정리하지 못했습니다 (finish_reason: {res.choices[0].finish_reason})"
            return
    
    except Exception as exc:
        print("사진 안 읽힘")
        yield f"사진을 읽지 못했습니다 — {type(exc).__name__}: {exc}"
        return

    header = f"**찾은 재료**\n\n{items}\n\n---\n\n"
    yield header + "레시피를 궁리하는 중..."

    # 2단계 — 재료로 레시피 만들기
    try:
        stream = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": CHEF_PROMPT},
                {"role": "user", "content": f"재료: {items}"},
            ],
            temperature=0.7,
            max_completion_tokens=1200,
            stream=True,
        )
        answer = ""
        for chunk in stream:
            piece = chunk.choices[0].delta.content
            if piece:
                answer += piece
                yield header + answer
    except Exception as exc:
        yield header + f"주방에 문제가 생겼습니다 — {type(exc).__name__}: {exc}"


with gr.Blocks(title="냉장고 털이 셰프") as demo:
    gr.Markdown("# 냉장고 털이 셰프\n냉장고 사진을 올리면 만들 수 있는 요리를 알려드립니다.")

    with gr.Row():
        with gr.Column():
            image = gr.Image(type="filepath", label="냉장고 사진")
            btn = gr.Button("요리 찾기", variant="primary")
        output = gr.Markdown()

    btn.click(cook, inputs=image, outputs=output)


if __name__ == "__main__":
    demo.launch()