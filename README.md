# 냉장고 털이 셰프

냉장고 사진을 올리면 그 안의 재료만으로 만들 수 있는 요리를 알려줍니다.

사진에서 재료를 읽는 일과 레시피를 생각하는 일을 서로 다른 모델이 나눠서 맡습니다.

```
냉장고 사진
   ↓  Hugging Face (멀티모달)   "고구마, 감자, 오이, 토마토"
재료 목록
   ↓  Groq (셰프 페르소나)       "오! 그걸로 감자고구마전 어때요?"
레시피
```

## 기능

- 사진 한 장으로 재료 자동 인식
- 인식된 재료만으로 구성한 요리 2~3가지 제안
- 조리 시간과 순서까지 단계별 안내
- 응답이 생성되는 대로 화면에 바로 표시 (스트리밍)
- 없는 재료를 사 오라고 하지 않음

## 설치

```bash
git clone https://github.com/hxxdll/저장소명.git
cd 저장소명
pip install -r requirements.txt
```

## API 키 설정

키가 두 개 필요합니다.

- Groq — [console.groq.com/keys](https://console.groq.com/keys)
- Hugging Face — [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

`.env.example`을 `.env`로 복사한 뒤 두 값을 채웁니다.

```bash
cp .env.example .env
```

```
GROQ_API_KEY=gsk_...
HF_TOKEN=hf_...
```

`.env`는 `.gitignore`에 등록되어 있어 저장소에 올라가지 않습니다.

## 실행

```bash
python 261020_bucheon_hugging_jhm.py
```

터미널에 뜨는 `http://127.0.0.1:7860` 주소를 브라우저로 엽니다.
사진을 올리고 버튼을 누르면 됩니다.

## 사용 모델

| 역할 | 모델 | 제공 |
|------|------|------|
| 사진에서 재료 읽기 | `deepseek-ai/DeepSeek-V4.1-Flash-1017` | Hugging Face Router |
| 레시피 생성 | `openai/gpt-oss-20b` | Groq |

두 API 모두 OpenAI 호환 형식이라 호출 코드가 거의 같습니다.
`base_url`과 모델명만 다릅니다.

## 구조

```
261020_bucheon_hugging_jhm.py
├── cook(image_path)      # 전체 흐름. yield로 진행 상황을 순서대로 내보냄
│   ├── 이미지 리사이즈    # 1024px로 줄여 base64 data URL 생성
│   ├── 1단계: HF 호출     # 사진 → 재료 목록
│   └── 2단계: Groq 호출   # 재료 → 레시피 (스트리밍)
└── gr.Blocks             # 사진 입력, 버튼, 결과 출력
```

## 만들면서 걸렸던 것들

**이미지 용량** — 원본 사진을 그대로 base64로 바꾸면 1.7MB가 넘어 요청이 거부됩니다.
PIL로 1024px까지 줄여서 보냅니다.

**추론 토큰** — 비전 모델이 추론형이라 생각 과정에도 토큰을 씁니다.
`max_tokens`가 부족하면 분석은 끝내놓고 답을 쓰지 못한 채 잘립니다.
이때 `content`는 빈 문자열, `finish_reason`은 `length`로 돌아옵니다.
응답이 비어 있을 땐 `finish_reason`을 먼저 확인하면 원인이 빠르게 갈립니다.

**화면 갱신** — Gradio는 `yield`한 값으로 출력 영역을 통째로 교체합니다.
재료 목록을 계속 보이게 하려면 매번 앞에 붙여서 내보내야 합니다.

## 환경

- Python 3.11
- gradio
- groq
- openai
- python-dotenv
- pillow

## 앞으로 해볼 것

- 인식된 재료를 사용자가 직접 수정할 수 있는 입력칸
- 인원수, 조리 시간, 식단 제한(채식 등) 옵션
- 마음에 든 레시피 저장
