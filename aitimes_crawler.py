import requests
from bs4 import BeautifulSoup
import pandas as pd
import openai
import streamlit as st
import time
import re
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import markdown
from io import BytesIO

class AITimesCrawler:
    def __init__(self):
        self.base_url = "https://www.aitimes.com"
        self.main_url = "https://www.aitimes.com/"
        
    def crawl_news_list(self):
        """메인 페이지에서 상위 10개 뉴스의 제목과 URL을 크롤링"""
        try:
            crawl_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.main_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 뉴스 링크들을 찾기
            news_links = soup.find_all('a', class_='auto-valign')
            
            news_data = []
            
            for i, link in enumerate(news_links[:10], 1):
                try:
                    # 순위 번호 추출
                    number_elem = link.find('em', class_='number')
                    if number_elem:
                        rank = number_elem.get_text(strip=True)
                    else:
                        rank = str(i)
                    
                    # 제목 추출
                    title_elem = link.find('span', class_='auto-titles')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    else:
                        continue
                    
                    # URL 추출
                    href = link.get('href')
                    if href:
                        if href.startswith('/'):
                            full_url = self.base_url + href
                        else:
                            full_url = href
                    else:
                        continue
                    
                    news_data.append({
                        'rank': rank,
                        'title': title,
                        'url': full_url,
                        'crawl_time': crawl_time
                    })
                    
                except Exception as e:
                    st.warning(f"뉴스 {i}번 처리 중 오류: {str(e)}")
                    continue
            
            return news_data
            
        except Exception as e:
            st.error(f"뉴스 목록 크롤링 중 오류 발생: {str(e)}")
            return []
    
    def crawl_article_content(self, url):
        """개별 뉴스 기사의 본문을 크롤링"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 기사 본문 추출 (여러 가능한 선택자 시도)
            content_selectors = [
                'div.news-content',
                'div.article-content',
                'div.view-content',
                'div#article-content',
                'div.content'
            ]
            
            content = ""
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    # p 태그들의 텍스트 추출
                    paragraphs = content_div.find_all('p')
                    content = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    break
            
            # 위 방법으로 찾지 못한 경우, 모든 p 태그 시도
            if not content:
                paragraphs = soup.find_all('p')
                content = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            return content.strip()
            
        except Exception as e:
            st.warning(f"기사 본문 크롤링 중 오류: {str(e)}")
            return ""
    
    def summarize_with_gpt(self, title, content, api_key):
        """OpenAI GPT를 사용하여 기사를 요약"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            prompt = f"""
다음 뉴스 기사를 아래 형식에 맞춰 한국어로 요약해주세요:

기사 제목: {title}
기사 내용: {content}

---
## 🚀 {title}

### 💡 핵심 비유 (Analogy)
- 내용을 한눈에 파악할 수 있는 강력하고 기억하기 쉬운 비유 또는 캐치프레이즈

### ✨ 핵심 요약 (Key Points)
- 가장 중요한 내용 3가지 요약
    - Point 1
    - Point 2
    - Point 3

### 📚 상세 내용 (Details)
- 핵심 요약에서 제시된 내용에 대한 구체적인 설명, 배경 또는 주요 특징 기술

### 🤔 비판적 관점 (Critical Points)
- 해당 내용에 대해 주의 깊게 생각하거나 경계해야 할 지점, 또는 더 깊이 생각해 볼 만한 질문 제시
    - Point 1
    - Point 2

### 📊 숫자 (Numbers)
*(선택 사항: 관련 데이터가 중요할 경우)*
- 핵심 통계 1:
- 핵심 통계 2:

### 👟 쉬운 첫걸음 (Easy Next Step)
- 핵심 교훈을 바탕으로, 가장 마찰이 적고 즉시 실행 가능한 구체적인 행동 1가지 제안

---

### 🧩 핵심 개념 & 용어
- 기술적으로 중요하거나 어려운 핵심 용어 3개를 비유를 통해 한 줄로 설명하여 소화 및 기억을 돕습니다.
    - **용어 1**:
    - **용어 2**:
    - **용어 3**:

### 📖 참고: 선행 지식 (Prerequisites)
- 이 정보를 완전히 이해하기 위해 필요한 사전 지식이나 조건
"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # gpt-4.1-mini가 아직 없으므로 gpt-4o-mini 사용
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            st.error(f"AI 요약 중 오류 발생: {str(e)}")
            return f"요약 실패: {str(e)}"
    
    def save_to_csv(self, news_data):
        """뉴스 데이터를 CSV 파일로 저장"""
        try:
            # crawled_data 디렉토리 생성
            os.makedirs("crawled_data", exist_ok=True)
            
            # 파일명 생성 (aitimes_yyyy_mm_dd_hhmmss.csv)
            timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
            filename = f"crawled_data/aitimes_{timestamp}.csv"
            
            df = pd.DataFrame(news_data)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            return filename
        except Exception as e:
            st.error(f"CSV 저장 중 오류: {str(e)}")
            return None
    
    def create_pdf_report(self, csv_file_path):
        """CSV 파일을 읽어서 PDF 리포트 생성"""
        try:
            # CSV 파일 읽기
            df = pd.read_csv(csv_file_path)
            
            # PDF 파일명 생성
            csv_filename = os.path.basename(csv_file_path)
            pdf_filename = csv_filename.replace('.csv', '_report.pdf')
            pdf_path = os.path.join(os.path.dirname(csv_file_path), pdf_filename)
            
            # 한글 폰트 등록 (CID 폰트 사용)
            try:
                from reportlab.pdfbase.cidfonts import UnicodeCIDFont
                
                # 한글 지원 CID 폰트 등록 시도
                korean_fonts = ['HYSMyeongJoStd-Medium', 'HYGothic-Medium', 'AppleGothic']
                korean_font_registered = False
                
                for font_name in korean_fonts:
                    try:
                        pdfmetrics.registerFont(UnicodeCIDFont(font_name))
                        korean_font_registered = True
                        st.info(f"✅ 한글 CID 폰트 로드 성공: {font_name}")
                        break
                    except:
                        continue
                
                if not korean_font_registered:
                    st.info("ℹ️ CID 폰트를 사용할 수 없습니다. 기본 폰트를 사용합니다.")
                    
            except Exception as font_error:
                st.info(f"ℹ️ CID 폰트 등록 중 오류: {str(font_error)}. 기본 폰트를 사용합니다.")
            
            # PDF 문서 생성
            doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                  rightMargin=inch, leftMargin=inch,
                                  topMargin=inch, bottomMargin=inch)
            
            # 스타일 설정
            styles = getSampleStyleSheet()
            
            # 사용할 폰트 결정 (CID 폰트 우선, 없으면 기본 폰트)
            korean_fonts = ['HYSMyeongJoStd-Medium', 'HYGothic-Medium', 'AppleGothic']
            available_korean_font = None
            
            for font_name in korean_fonts:
                try:
                    # 폰트가 등록되어 있는지 확인
                    from reportlab.pdfbase.pdfmetrics import getFont
                    getFont(font_name)
                    available_korean_font = font_name
                    break
                except:
                    continue
            
            regular_font = available_korean_font if available_korean_font else 'Helvetica'
            bold_font = available_korean_font if available_korean_font else 'Helvetica-Bold'
            
            # 제목 스타일
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=1,  # 중앙 정렬
                textColor='#2E86AB',
                fontName=bold_font
            )
            
            # 헤딩 스타일
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                spaceBefore=20,
                textColor='#A23B72',
                fontName=bold_font
            )
            
            # 본문 스타일
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=12,
                leading=14,
                fontName=regular_font
            )
            
            # 소제목 스타일
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=13,
                spaceAfter=8,
                spaceBefore=12,
                textColor='#F18F01',
                fontName=bold_font
            )
            
            # 리포트 내용 구성
            story = []
            
            # 제목
            crawl_time = df['crawl_time'].iloc[0] if 'crawl_time' in df.columns else "Unknown"
            story.append(Paragraph(f"AI타임스 뉴스 리포트", title_style))
            story.append(Paragraph(f"크롤링 시간: {crawl_time}", body_style))
            story.append(Spacer(1, 20))
            
            # 요약 통계
            story.append(Paragraph("📊 크롤링 요약", heading_style))
            story.append(Paragraph(f"• 총 뉴스 개수: {len(df)}개", body_style))
            
            successful_summaries = len(df[~df['summary'].str.startswith('요약 실패', na=False)]) if 'summary' in df.columns else 0
            story.append(Paragraph(f"• AI 요약 성공: {successful_summaries}개", body_style))
            story.append(Spacer(1, 20))
            
            # 각 뉴스별 상세 리포트
            for idx, row in df.iterrows():
                # 페이지 나누기 (첫 번째 뉴스 제외)
                if idx > 0:
                    story.append(PageBreak())
                
                # 뉴스 제목
                story.append(Paragraph(f"📰 뉴스 #{row.get('rank', idx+1)}: {row['title']}", heading_style))
                story.append(Paragraph(f"URL: {row['url']}", body_style))
                story.append(Spacer(1, 12))
                
                # AI 요약이 있는 경우
                if 'summary' in row and pd.notna(row['summary']) and not str(row['summary']).startswith('요약 실패'):
                    summary_text = str(row['summary'])
                    
                    # 마크다운을 HTML로 변환 후 단순화
                    try:
                        # 마크다운 특수 문자들을 단순화
                        summary_text = summary_text.replace('### ', '')
                        summary_text = summary_text.replace('## ', '')
                        summary_text = summary_text.replace('# ', '')
                        summary_text = summary_text.replace('**', '')
                        summary_text = summary_text.replace('*', '•')
                        summary_text = summary_text.replace('- ', '• ')
                        
                        # 이모지와 제목들을 적절히 처리
                        lines = summary_text.split('\n')
                        processed_lines = []
                        
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                                
                            # 이모지가 포함된 섹션 제목들
                            if any(emoji in line for emoji in ['🚀', '💡', '✨', '📚', '🤔', '📊', '👟', '🧩', '📖']):
                                processed_lines.append(f"<b>{line}</b>")
                            else:
                                processed_lines.append(line)
                        
                        summary_text = '<br/>'.join(processed_lines)
                        story.append(Paragraph(summary_text, body_style))
                        
                    except Exception as e:
                        # 마크다운 처리 실패 시 원본 텍스트 사용
                        clean_text = summary_text.replace('<', '&lt;').replace('>', '&gt;')
                        story.append(Paragraph(clean_text, body_style))
                        
                else:
                    story.append(Paragraph("AI 요약을 생성할 수 없었습니다.", body_style))
                
                story.append(Spacer(1, 20))
            
            # PDF 생성
            doc.build(story)
            return pdf_path
            
        except Exception as e:
            st.error(f"PDF 리포트 생성 중 오류: {str(e)}")
            return None
    
    def get_csv_files(self):
        """crawled_data 디렉토리의 CSV 파일 목록 반환"""
        try:
            if not os.path.exists("crawled_data"):
                return []
            
            csv_files = []
            for file in os.listdir("crawled_data"):
                if file.endswith('.csv') and file.startswith('aitimes_'):
                    csv_files.append(os.path.join("crawled_data", file))
            
            # 최신순으로 정렬
            csv_files.sort(key=os.path.getmtime, reverse=True)
            return csv_files
            
        except Exception as e:
            st.error(f"CSV 파일 목록 조회 중 오류: {str(e)}")
            return [] 