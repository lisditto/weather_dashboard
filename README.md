# 평균-분산 포트폴리오 분석 대시보드

Markowitz Modern Portfolio Theory(MPT) 기반의 인터랙티브 투자 분석 대시보드.
미국 주식을 티커 기반(SPY · TLT · GLD · VNQ 등)으로 수익률·변동성·상관관계를 분석하고,
포트폴리오 비중을 직접 조정하면서 리스크에 따른 최적의 분배 비율을 확인할 수 있습니다.

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

기본 포트는 `http://localhost:8501`. 네트워크가 없을 경우 사이드바에서
**오프라인(샘플) 데이터**를 켜면 합성 데이터로 동작합니다.

## 구성

```
app.py                         # Streamlit 엔트리포인트
portfolio_dashboard/
├── config.py                  # 자산·색상·상수
├── data.py                    # yfinance + 합성 데이터 폴백
├── analysis.py                # 수익률, 변동성, 샤프, MDD, 상관
├── portfolio.py               # 포트폴리오 통계 + EF 시뮬레이션 + 최적화
└── charts.py                  # Plotly 차트 빌더 (다크 테마)
.streamlit/config.toml         # 다크 테마 설정
```

## 주요 기능

1. **자산 현황** — 자산별 수익률·변동성·샤프지수·MDD 카드
2. **상관관계 히트맵** — RdBu_r 팔레트, -1~1 고정
3. **포트폴리오 분석** — 비중 슬라이더 + 도넛 차트 + 실시간 지표
   - 「최대 샤프」 / 「최소 변동성」 / 「균등」 프리셋 버튼
4. **Efficient Frontier** — 몬테카를로 시뮬레이션 + 최적해 마커

## 가정

- 무위험금리 0%
- 연 환산: 252영업일
- yfinance 실패 시 GBM 기반 합성 데이터(`seed=42`)로 폴백
