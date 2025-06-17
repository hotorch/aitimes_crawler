import streamlit as st
import pandas as pd
import time
from aitimes_crawler import AITimesCrawler
import os

def main():
    st.set_page_config(
        page_title="AI타임스 뉴스 크롤러",
        page_icon="📰",
        layout="wide"
    )
    
    st.title("📰 AI타임스 뉴스 크롤러")
    st.markdown("AI타임스에서 최신 뉴스를 크롤링하고 AI로 요약하는 도구입니다.")
    
    # 사이드바 설정
    st.sidebar.header("⚙️ 설정")
    
    # OpenAI API 키 입력
    api_key = st.sidebar.text_input(
        "OpenAI API 키를 입력하세요:",
        type="password",
        help="https://platform.openai.com/api-keys 에서 API 키를 발급받을 수 있습니다."
    )
    
    # 크롤러 인스턴스 생성
    crawler = AITimesCrawler()
    
    # 메인 컨텐츠
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🔍 뉴스 크롤링")
        
        if st.button("AI타임스 뉴스 크롤링 시작", type="primary"):
            with st.spinner("뉴스 목록을 가져오는 중..."):
                news_list = crawler.crawl_news_list()
                
                if news_list:
                    st.success(f"✅ {len(news_list)}개의 뉴스를 발견했습니다!")
                    
                    # 뉴스 목록 표시
                    df_preview = pd.DataFrame(news_list)
                    st.dataframe(df_preview, use_container_width=True)
                    
                    # 세션 상태에 저장
                    st.session_state.news_list = news_list
                    st.session_state.df_preview = df_preview
                    
                else:
                    st.error("❌ 뉴스를 가져올 수 없습니다.")
    
    with col2:
        st.subheader("🤖 AI 요약 생성")
        
        if st.button("본문 크롤링 및 AI 요약", type="secondary"):
            if not api_key:
                st.error("❌ OpenAI API 키를 먼저 입력해주세요!")
                return
            
            if 'news_list' not in st.session_state:
                st.error("❌ 먼저 뉴스 크롤링을 실행해주세요!")
                return
            
            news_list = st.session_state.news_list
            
            # 진행 상황 표시
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            enhanced_news = []
            
            for i, news in enumerate(news_list):
                status_text.text(f"📄 {i+1}/{len(news_list)}: {news['title'][:50]}... 처리 중")
                
                # 본문 크롤링
                content = crawler.crawl_article_content(news['url'])
                
                if content:
                    # AI 요약
                    status_text.text(f"🤖 {i+1}/{len(news_list)}: AI 요약 생성 중...")
                    summary = crawler.summarize_with_gpt(news['title'], content, api_key)
                    
                    enhanced_news.append({
                        'rank': news['rank'],
                        'title': news['title'],
                        'url': news['url'],
                        'content': content,
                        'summary': summary,
                        'crawl_time': news['crawl_time']
                    })
                else:
                    enhanced_news.append({
                        'rank': news['rank'],
                        'title': news['title'],
                        'url': news['url'],
                        'content': "본문을 가져올 수 없습니다.",
                        'summary': "요약을 생성할 수 없습니다.",
                        'crawl_time': news['crawl_time']
                    })
                
                # 진행률 업데이트
                progress_bar.progress((i + 1) / len(news_list))
                
                # API 호출 제한을 위한 지연
                time.sleep(1)
            
            # CSV 저장
            csv_file = crawler.save_to_csv(enhanced_news)
            if csv_file:
                st.success(f"✅ 모든 처리가 완료되었습니다! 파일: {csv_file}")
                
                # 세션 상태에 저장
                st.session_state.enhanced_news = enhanced_news
                st.session_state.csv_file = csv_file
            
            status_text.text("✅ 완료!")
    
    # 결과 표시
    if 'enhanced_news' in st.session_state:
        st.markdown("---")
        st.subheader("📊 크롤링 결과 대시보드")
        
        enhanced_news = st.session_state.enhanced_news
        
        # 통계 정보
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("전체 뉴스", len(enhanced_news))
        with col2:
            successful_crawls = len([n for n in enhanced_news if n['content'] != "본문을 가져올 수 없습니다."])
            st.metric("본문 크롤링 성공", successful_crawls)
        with col3:
            successful_summaries = len([n for n in enhanced_news if not n['summary'].startswith("요약 실패")])
            st.metric("AI 요약 성공", successful_summaries)
        
        # 뉴스 선택 및 상세 보기
        st.subheader("📰 뉴스 상세 보기")
        
        # 뉴스 선택 드롭다운
        news_titles = [f"{news['rank']}. {news['title']}" for news in enhanced_news]
        selected_news_index = st.selectbox(
            "보고 싶은 뉴스를 선택하세요:",
            range(len(news_titles)),
            format_func=lambda x: news_titles[x]
        )
        
        selected_news = enhanced_news[selected_news_index]
        
        # 선택된 뉴스 표시
        st.markdown(f"### 📖 {selected_news['title']}")
        st.markdown(f"**순위:** {selected_news['rank']}")
        st.markdown(f"**URL:** {selected_news['url']}")
        
        # 탭으로 원문과 요약 분리
        tab1, tab2 = st.tabs(["🤖 AI 요약", "📄 원문"])
        
        with tab1:
            if selected_news['summary'] and not selected_news['summary'].startswith("요약 실패"):
                st.markdown(selected_news['summary'])
            else:
                st.error("AI 요약을 생성할 수 없었습니다.")
        
        with tab2:
            if selected_news['content'] and selected_news['content'] != "본문을 가져올 수 없습니다.":
                st.text_area("원문 내용", selected_news['content'], height=400)
            else:
                st.error("본문을 가져올 수 없었습니다.")
        
        # CSV 다운로드 및 PDF 리포트
        if 'csv_file' in st.session_state:
            st.markdown("---")
            st.subheader("💾 데이터 다운로드")
            
            col1, col2 = st.columns(2)
            
            with col1:
                try:
                    with open(st.session_state.csv_file, 'rb') as file:
                        st.download_button(
                            label="📥 CSV 파일 다운로드",
                            data=file.read(),
                            file_name=os.path.basename(st.session_state.csv_file),
                            mime='text/csv'
                        )
                except Exception as e:
                    st.error(f"파일 다운로드 중 오류: {str(e)}")
            
            with col2:
                if st.button("📄 PDF 리포트 생성", type="secondary"):
                    with st.spinner("PDF 리포트를 생성하는 중..."):
                        pdf_path = crawler.create_pdf_report(st.session_state.csv_file)
                        
                        if pdf_path and os.path.exists(pdf_path):
                            st.success("✅ PDF 리포트가 생성되었습니다!")
                            
                            try:
                                with open(pdf_path, 'rb') as pdf_file:
                                    st.download_button(
                                        label="📥 PDF 리포트 다운로드",
                                        data=pdf_file.read(),
                                        file_name=os.path.basename(pdf_path),
                                        mime='application/pdf'
                                    )
                            except Exception as e:
                                st.error(f"PDF 다운로드 중 오류: {str(e)}")
                        else:
                            st.error("❌ PDF 리포트 생성에 실패했습니다.")
    
    # 기존 CSV 파일로 PDF 생성
    st.markdown("---")
    st.subheader("📂 기존 데이터로 PDF 리포트 생성")
    
    csv_files = crawler.get_csv_files()
    if csv_files:
        selected_csv = st.selectbox(
            "PDF로 변환할 CSV 파일을 선택하세요:",
            csv_files,
            format_func=lambda x: os.path.basename(x)
        )
        
        if st.button("📄 선택한 파일로 PDF 생성"):
            with st.spinner("PDF 리포트를 생성하는 중..."):
                pdf_path = crawler.create_pdf_report(selected_csv)
                
                if pdf_path and os.path.exists(pdf_path):
                    st.success("✅ PDF 리포트가 생성되었습니다!")
                    
                    try:
                        with open(pdf_path, 'rb') as pdf_file:
                            st.download_button(
                                label="📥 PDF 리포트 다운로드",
                                data=pdf_file.read(),
                                file_name=os.path.basename(pdf_path),
                                mime='application/pdf',
                                key="existing_csv_pdf"
                            )
                    except Exception as e:
                        st.error(f"PDF 다운로드 중 오류: {str(e)}")
                else:
                    st.error("❌ PDF 리포트 생성에 실패했습니다.")
    else:
        st.info("📂 crawled_data 폴더에 CSV 파일이 없습니다.")

if __name__ == "__main__":
    main() 