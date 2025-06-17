# AI타임스 뉴스 크롤러

AI타임스(aitimes.com)에서 최신 뉴스를 크롤링하고 OpenAI GPT를 활용하여 자동으로 요약하는 Streamlit 웹 애플리케이션입니다.

## 기능

1. **뉴스 크롤링**: AI타임스 메인 페이지에서 상위 10개 뉴스의 제목과 URL을 수집
2. **본문 추출**: 각 뉴스 기사의 전체 본문을 크롤링
3. **AI 요약**: OpenAI GPT-4o-mini를 사용하여 구조화된 형태로 뉴스 요약
4. **데이터 저장**: 크롤링 시간이 포함된 CSV 파일을 `crawled_data/` 폴더에 타임스탬프와 함께 저장
5. **PDF 리포트**: 마크다운 형식의 AI 요약을 PDF 리포트로 변환
6. **대시보드**: Streamlit을 통한 직관적인 웹 인터페이스 제공

## 설치 및 실행

### 1. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. OpenAI API 키 준비
- [OpenAI Platform](https://platform.openai.com/api-keys)에서 API 키를 발급받으세요.

### 3. 애플리케이션 실행
```bash
streamlit run app.py
```

## 사용법

1. **API 키 입력**: 사이드바에서 OpenAI API 키를 입력합니다.
2. **뉴스 크롤링**: "AI타임스 뉴스 크롤링 시작" 버튼을 클릭합니다.
3. **AI 요약**: "본문 크롤링 및 AI 요약" 버튼을 클릭하여 전체 프로세스를 실행합니다.
4. **결과 확인**: 대시보드에서 뉴스별 요약 결과를 확인합니다.
5. **파일 다운로드**: 
   - CSV 파일을 다운로드하거나
   - PDF 리포트를 생성하여 다운로드할 수 있습니다.
6. **기존 데이터 활용**: 이전에 저장된 CSV 파일을 선택하여 PDF 리포트로 변환할 수 있습니다.

## 요약 형식

각 뉴스는 다음 구조로 요약됩니다:

- 🚀 **제목**
- 💡 **핵심 비유**: 내용을 쉽게 이해할 수 있는 비유
- ✨ **핵심 요약**: 가장 중요한 3가지 포인트
- 📚 **상세 내용**: 구체적인 설명과 배경
- 🤔 **비판적 관점**: 주의할 점과 생각해볼 질문
- 📊 **숫자**: 중요한 통계 정보 (선택사항)
- 👟 **쉬운 첫걸음**: 즉시 실행 가능한 행동 제안
- 🧩 **핵심 개념 & 용어**: 중요한 용어의 쉬운 설명
- 📖 **참고: 선행 지식**: 이해에 필요한 사전 지식

## 주요 파일

- `app.py`: Streamlit 메인 애플리케이션
- `aitimes_crawler.py`: 크롤링 및 AI 요약 로직
- `requirements.txt`: 필요한 Python 패키지 목록
- `crawled_data/`: 크롤링 결과 저장 폴더 (실행 후 자동 생성)
  - `aitimes_YYYY_MM_DD_HHMMSS.csv`: 크롤링 결과 CSV 파일
  - `aitimes_YYYY_MM_DD_HHMMSS_report.pdf`: PDF 리포트 파일

## 주의사항

- OpenAI API 사용에 따른 비용이 발생할 수 있습니다.
- 웹 크롤링 시 해당 사이트의 robots.txt와 이용약관을 준수해주세요.
- API 호출 제한을 고려하여 요청 간 지연시간을 두었습니다.

## 기술 스택

- **Python**: 메인 프로그래밍 언어
- **Streamlit**: 웹 애플리케이션 프레임워크
- **BeautifulSoup**: HTML 파싱 및 크롤링
- **Pandas**: 데이터 처리 및 CSV 저장
- **OpenAI**: GPT를 활용한 텍스트 요약
- **Requests**: HTTP 요청 처리
- **ReportLab**: PDF 리포트 생성
- **Markdown**: 마크다운 텍스트 처리 