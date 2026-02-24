#!/usr/bin/env python3
"""
심층 분석 보고서 생성 스크립트
OpenAI API를 사용하여 주요 금융 이슈를 자동으로 추출하고 심층 분석합니다.
"""

import os
import requests
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# API 키 로드
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

def call_openai(question, context="", max_tokens=1000, system_prompt=None):
    """OpenAI API 호출"""
    api_url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    if system_prompt is None:
        system_prompt = '당신은 금융 시장 분석 전문가입니다. 사실 기반으로 구체적이고 상세한 분석을 제공합니다.'
    
    user_message = f"{context}\n\n{question}" if context else question
    
    payload = {
        'model': 'gpt-4o',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message}
        ],
        'max_tokens': max_tokens,
        'temperature': 0.3
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"API 오류 (코드 {response.status_code}): {response.text}"
    except Exception as e:
        return f"예외 발생: {str(e)}"

def load_news_data(filepath):
    """뉴스 로그 파일 읽기"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"뉴스 파일 로드 실패: {e}")
        return None

def extract_key_issues(news_content):
    """수집된 뉴스에서 주요 이슈와 분석 질문을 자동 생성 (글로벌/한국, 매크로/기업 분류)"""
    print("\n[1단계] 뉴스 데이터에서 주요 이슈 추출 중...")
    print("  - 글로벌 이슈: 매크로 5개 + 기업 15개 = 20개")
    print("  - 한국 이슈: 매크로 5개 + 기업 15개 = 20개")
    print("  - 총 40개 이슈 추출 예정\n")
    
    # 뉴스 전체 사용 (충분한 샘플)
    news_sample = news_content[:30000] if len(news_content) > 30000 else news_content
    
    prompt = """다음은 최근 24시간 동안 수집된 금융 뉴스입니다.

이 뉴스들을 분석하여 총 40개의 주요 이슈를 다음 체계로 추출하세요:

【글로벌 뉴스 - 총 20개】
1. 매크로 이슈 (5개): 금리, 환율, 통화정책, 경제지표, 지정학적 리스크 등
2. 기업 이슈 (15개): 글로벌 기업의 실적, 산업 트렌드, 기술 혁신, M&A 등
   - 많이 언급된 주요 기업 위주로 선정하되
   - 덜 언급되지만 중요한 기업 이슈도 포함

【한국 뉴스 - 총 20개】
1. 매크로 이슈 (5개): 한국 금리정책, 환율, 정부정책, 경제지표 등
2. 기업 이슈 (15개): 한국 기업의 실적, 산업 트렌드, 기술 혁신, M&A 등
   - 많이 언급된 주요 기업 위주로 선정하되
   - 덜 언급되지만 중요한 기업 이슈도 포함

각 이슈에 대해 '왜(Why)'와 '어떻게(How)'를 깊이 있게 조사할 수 있는 심층 분석 질문을 생성하세요.

응답 형식은 반드시 JSON으로 작성하고, 다음 구조를 따르세요:
{
  "global_macro": [
    {"title": "이슈 제목", "question": "심층 분석 질문"}
  ],
  "global_corporate": [
    {"title": "이슈 제목", "question": "심층 분석 질문"}
  ],
  "korea_macro": [
    {"title": "이슈 제목", "question": "심층 분석 질문"}
  ],
  "korea_corporate": [
    {"title": "이슈 제목", "question": "심층 분석 질문"}
  ]
}

중요: 
- 실제로 뉴스에 등장한 이슈만 선정할 것
- 질문은 구체적이고 분석 가능해야 함
- 반드시 유효한 JSON 형식으로만 응답할 것
- 각 카테고리의 개수를 정확히 지킬 것 (매크로 5개, 기업 15개)"""
    
    response = call_openai(
        prompt,
        context=news_sample,
        max_tokens=4000,
        system_prompt='당신은 글로벌 및 한국 금융시장 분석 전문가입니다. 매크로와 기업 이슈를 체계적으로 분류하고 분석합니다.'
    )
    
    try:
        # JSON 파싱
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0].strip()
        elif '```' in response:
            response = response.split('```')[1].split('```')[0].strip()
        
        issues_data = json.loads(response)
        
        # 카테고리별로 이슈 수집
        all_issues = []
        
        # 글로벌 매크로
        global_macro = issues_data.get('global_macro', [])
        for issue in global_macro:
            issue['category'] = '글로벌 매크로'
            all_issues.append(issue)
        
        # 글로벌 기업
        global_corporate = issues_data.get('global_corporate', [])
        for issue in global_corporate:
            issue['category'] = '글로벌 기업'
            all_issues.append(issue)
        
        # 한국 매크로
        korea_macro = issues_data.get('korea_macro', [])
        for issue in korea_macro:
            issue['category'] = '한국 매크로'
            all_issues.append(issue)
        
        # 한국 기업
        korea_corporate = issues_data.get('korea_corporate', [])
        for issue in korea_corporate:
            issue['category'] = '한국 기업'
            all_issues.append(issue)
        
        print(f"  ✓ 글로벌 매크로: {len(global_macro)}개")
        print(f"  ✓ 글로벌 기업: {len(global_corporate)}개")
        print(f"  ✓ 한국 매크로: {len(korea_macro)}개")
        print(f"  ✓ 한국 기업: {len(korea_corporate)}개")
        print(f"  ✓ 총 {len(all_issues)}개 이슈 추출 완료\n")
        
        return all_issues
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        print(f"응답 내용: {response[:500]}...")
        return None

def main():
    """메인 실행 함수"""
    print("="*80)
    print("심층 분석 보고서 자동 생성 시작")
    print("="*80)
    
    # 뉴스 파일 찾기 (가장 최근 파일)
    import glob
    news_files = glob.glob('output/news_log_*.txt')
    if not news_files:
        print("❌ 뉴스 로그 파일을 찾을 수 없습니다.")
        return
    
    latest_news_file = sorted(news_files)[-1]
    print(f"\n📂 뉴스 파일: {latest_news_file}")
    
    # 뉴스 데이터 로드
    news_content = load_news_data(latest_news_file)
    if not news_content:
        print("❌ 뉴스 데이터 로드 실패")
        return
    
    # 주요 이슈 자동 추출
    analysis_topics = extract_key_issues(news_content)
    if not analysis_topics:
        print("❌ 주요 이슈 추출 실패")
        return
    
    # 카테고리별 이슈 개수 표시
    categories = {}
    for topic in analysis_topics:
        cat = topic.get('category', '기타')
        categories[cat] = categories.get(cat, 0) + 1
    
    print("카테고리별 이슈:")
    for cat, count in categories.items():
        print(f"  - {cat}: {count}개")
    
    # 보고서 생성
    print(f"\n[2단계] 총 {len(analysis_topics)}개 이슈에 대한 심층 분석 수행 중...")
    print("="*80)
    
    report_lines = []
    report_lines.append("=" * 100)
    report_lines.append("\n📊 금융 뉴스 심층 분석 보고서 (체계적 분류)")
    report_lines.append("In-Depth Financial News Analysis Report (Systematic Classification)\n")
    report_lines.append(f"보고서 작성일: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}")
    report_lines.append(f"데이터 소스: {latest_news_file}")
    report_lines.append("분석 방법: OpenAI GPT-4o 기반 자동 이슈 추출 및 심층 분석")
    report_lines.append("분류 체계: 글로벌/한국 × 매크로/기업\n")
    report_lines.append("=" * 100)
    report_lines.append("\n\n【 보고서 개요 】\n")
    report_lines.append("본 보고서는 최근 24시간 동안 수집된 금융 뉴스를 AI가 자동으로 분석하여,")
    report_lines.append("주요 시장 이슈를 체계적으로 분류하고 심층 분석한 결과입니다.\n")
    report_lines.append("분류 기준:")
    report_lines.append("  - 글로벌/한국: 지역별 구분")
    report_lines.append("  - 매크로/기업: 이슈 유형별 구분")
    report_lines.append("    * 매크로: 금리, 환율, 정책, 경제지표 등")
    report_lines.append("    * 기업: 기업 실적, 산업 트렌드, M&A, 기술 혁신 등\n")
    report_lines.append(f"총 {len(analysis_topics)}개 이슈 분석 완료\n\n")

    # 카테고리별로 그룹화하여 출력
    current_category = None
    for i, topic in enumerate(analysis_topics, 1):
        category = topic.get('category', '기타')
        
        # 카테고리가 바뀔 때마다 섹션 헤더 추가
        if category != current_category:
            report_lines.append("\n" + "=" * 100)
            report_lines.append(f"\n【 {category} 】\n")
            report_lines.append("=" * 100 + "\n")
            current_category = category
        
        print(f"\n[{i}/{len(analysis_topics)}] [{category}] {topic['title']} 분석 중...")
        
        report_lines.append("━" * 100)
        report_lines.append(f"\n■ {topic['title']}\n")
        
        analysis_result = call_openai(topic['question'])
        report_lines.append(analysis_result)
        report_lines.append("\n\n")
        
        print(f"  ✓ 완료 ({len(analysis_result)} 글자)")
        
        # Rate limit 방지 (40개 이슈니까 조금 더 여유있게)
        if i < len(analysis_topics):
            time.sleep(2)

    # 종합 시사점
    report_lines.append("\n" + "=" * 100)
    report_lines.append("\n【 종합 시사점 】\n")
    report_lines.append("=" * 100 + "\n")
    report_lines.append("본 보고서를 통해 현재 금융시장의 주요 동향을 다음과 같이 정리할 수 있습니다:\n")
    report_lines.append("1. 글로벌 매크로: 주요국 통화정책, 경제지표, 지정학적 리스크 동향")
    report_lines.append("2. 글로벌 기업: 주요 글로벌 기업의 실적, 산업 트렌드, 기술 혁신")
    report_lines.append("3. 한국 매크로: 국내 금리정책, 환율, 정부 정책 방향")
    report_lines.append("4. 한국 기업: 국내 기업 실적, 산업 동향, M&A 활동\n")
    report_lines.append("각 이슈는 독립적으로 발생한 것이 아니라, 글로벌 경제 환경, 기술 발전,")
    report_lines.append("지정학적 요인 등이 복합적으로 작용한 결과입니다.\n")
    report_lines.append("투자자는 이러한 이슈들의 상호 연관성을 이해하고, 장기적 관점에서")
    report_lines.append("시장 변화를 주시할 필요가 있습니다.\n\n")

    # 푸터
    report_lines.append("=" * 100)
    report_lines.append("\n⚠️ 면책 조항")
    report_lines.append("본 보고서는 AI 기반 분석을 포함하고 있으며, 투자 조언이나 종목 추천이 아닌")
    report_lines.append("시장 이해를 돕기 위한 정보 제공 목적으로 작성되었습니다.\n")
    report_lines.append("분석 엔진: OpenAI GPT-4o")
    report_lines.append(f"생성 일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}")
    report_lines.append(f"분석 이슈 수: {len(analysis_topics)}개\n")
    report_lines.append("=" * 100)

    # 파일 저장
    output_file = 'output/INDEPTH_ANALYSIS_REPORT.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print(f"\n{'='*80}")
    print(f"✅ 심층 분석 보고서 생성 완료!")
    print(f"📄 저장 위치: {output_file}")
    print(f"📊 분석된 이슈: {len(analysis_topics)}개")
    for cat, count in categories.items():
        print(f"   - {cat}: {count}개")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()
