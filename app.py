import streamlit as st
import bisect

# --- 1. 계산 로직 ---
class ChildSupportCalculator:
    def __init__(self):
        # 2021년 서울가정법원 산정기준표 데이터 (표6 기반)
        self.income_bins = [2000000, 3000000, 4000000, 5000000, 6000000, 7000000, 8000000, 9000000, 10000000, 12000000]
        self.support_table = {
            "0-2": [621000, 752000, 945000, 1098000, 1245000, 1401000, 1582000, 1789000, 1997000, 2095000, 2207000],
            "3-5": [631000, 759000, 949000, 1113000, 1266000, 1422000, 1598000, 1807000, 2017000, 2116000, 2245000],
            "6-8": [648000, 767000, 959000, 1140000, 1292000, 1479000, 1614000, 1850000, 2065000, 2137000, 2312000],
            "9-11": [667000, 782000, 988000, 1163000, 1318000, 1494000, 1630000, 1887000, 2137000, 2180000, 2405000],
            "12-14": [679000, 790000, 998000, 1280000, 1423000, 1598000, 1711000, 1984000, 2159000, 2223000, 2476000],
            "15-18": [703000, 957000, 1227000, 1402000, 1604000, 1794000, 1964000, 2163000, 2246000, 2540000, 2883000]
        }

    def _get_age_group(self, age):
        if 0 <= age <= 2: return "0-2"
        elif 3 <= age <= 5: return "3-5"
        elif 6 <= age <= 8: return "6-8"
        elif 9 <= age <= 11: return "9-11"
        elif 12 <= age <= 14: return "12-14"
        elif 15 <= age <= 18: return "15-18"
        return None

    def calculate(self, custodial_income, non_custodial_income, children_ages, location, extra_expenses):
        # 입력된 만원 단위를 원 단위로 변환하여 계산
        custodial_income_won = custodial_income * 10000
        non_custodial_income_won = non_custodial_income * 10000
        extra_expenses_won = extra_expenses * 10000
        
        combined_income = custodial_income_won + non_custodial_income_won
        income_idx = bisect.bisect_right(self.income_bins, combined_income)
        
        base_total = 0
        details = []

        for age in children_ages:
            group = self._get_age_group(age)
            if group:
                val = self.support_table[group][income_idx]
                base_total += val
                # 결과 내역에는 쉼표(,) 포함하여 표시
                details.append(f"만 {age}세: {val:,}원")
            else:
                details.append(f"만 {age}세: 성인 (제외)")

        child_cnt = len([a for a in children_ages if 0 <= a <= 18])
        cnt_mul = 1.065 if child_cnt == 1 else (0.783 if child_cnt >= 3 else 1.0)
        loc_mul = 1.079 if location == "도시" else (0.835 if location == "농어촌" else 1.0)

        total = (base_total * cnt_mul * loc_mul) + extra_expenses_won
        ratio = (non_custodial_income_won / combined_income) if combined_income > 0 else 0
        final_pay = total * ratio

        return {
            "합산소득": combined_income,
            "표준총액": base_total,
            "자녀수": child_cnt,
            "내역": details,
            "총예상액": round(total, -1),
            "비율": round(ratio * 100, 1),
            "최종지급액": round(final_pay, -1)
        }

# --- 2. 화면 구성 (UI) ---
st.set_page_config(page_title="나자현 변호사의 양육비 계산기", page_icon="⚖️")

# [타이틀]
st.title("🧮 우리 아이 양육비, 1분 예상 계산기")
st.markdown("##### 창원·경남 **나자현 변호사**가 **우리 지역 부모님**들을 위해 직접 만들었습니다.")

st.info("💡 0을 세느라 헷갈리지 않게 **'만원 단위'**로 입력해 주세요. (예: 200 = 200만 원)")

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        # 입력값 포맷팅을 위해 help 메시지와 label 활용
        my_income = st.number_input("양육자 월 소득 (단위: 만원)", min_value=0, step=10, value=200, help="세전 소득 기준. 예: 250만원이면 250 입력")
        st.caption(f"👉 입력 확인: **{my_income * 10000:,}원**") # 입력 즉시 쉼표 금액 보여줌
        
    with col2:
        ex_income = st.number_input("비양육자 월 소득 (단위: 만원)", min_value=0, step=10, value=300, help="세전 소득 기준")
        st.caption(f"👉 입력 확인: **{ex_income * 10000:,}원**") # 입력 즉시 쉼표 금액 보여줌

    st.markdown("---")
    cnt = st.number_input("자녀 수", 1, 5, 1)
    
    st.markdown("##### 자녀 만 나이")
    ages = []
    cols = st.columns(cnt)
    for i in range(cnt):
        with cols[i]:
            ages.append(st.number_input(f"자녀{i+1}", 0, 25, 5))

    with st.expander("추가 설정 (거주지, 병원비 등)"):
        loc = st.radio("거주 지역", ["일반", "도시", "농어촌"], horizontal=True)
        # 추가 비용도 만원 단위로 통일
        extra = st.number_input("월 추가 비용 (단위: 만원 / 치료비·유학비 등)", min_value=0, step=5, value=0)
        if extra > 0:
            st.caption(f"👉 추가 비용: **{extra * 10000:,}원**")

    if st.button("양육비 계산하기", type="primary"):
        calc = ChildSupportCalculator()
        try:
            res = calc.calculate(my_income, ex_income, ages, loc, extra)
            
            st.divider()
            # 결과값에 쉼표(,) 적용하여 파란색으로 크게 강조
            st.markdown(f"### 💰 비양육자 예상 지급액: <span style='color:blue'>{res['최종지급액']:,}원</span>", unsafe_allow_html=True)
            
            st.write(f"**부모 합산 소득:** {res['합산소득']:,}원")
            st.write(f"**비양육자 분담 비율:** {res['비율']}%")
            
            st.markdown("---")
            st.caption("🔍 **상세 산출 내역**")
            st.caption(f"• 자녀별 표준값: {', '.join(res['내역'])}")
            st.caption(f"• 기본 합계: {res['표준총액']:,}원")
            
            # 조정 요소 설명
            adjustments = []
            if res['자녀수'] == 1: adjustments.append("1자녀 가산")
            if res['자녀수'] >= 3: adjustments.append("다자녀 감산")
            if loc != "일반": adjustments.append(f"거주지({loc})")
            if extra > 0: adjustments.append(f"추가비용({extra*10000:,}원)")
            
            if adjustments:
                st.caption(f"• 반영된 조정 요소: {', '.join(adjustments)}")
            else:
                st.caption("• 별도 가산/감산 요소 없음")
            
        except Exception as e:
            st.error("입력값을 확인해주세요.")

st.markdown("---")
st.markdown("**Created by Lawyer Najahyeon (Changwon/Gyeongnam)**")
st.caption("※ 본 결과는 2021년 산정기준표에 따른 예상치이며, 실제 판결은 재산 상황, 합의 등에 따라 달라질 수 있습니다.")
