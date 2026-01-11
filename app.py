import streamlit as st
import bisect

# --- 1. 계산 로직 (기존 코드와 동일) ---
class ChildSupportCalculator:
    def __init__(self):
        # 소득 구간 (200만원 ~ 1200만원)
        self.income_bins = [
            2000000, 3000000, 4000000, 5000000, 6000000, 
            7000000, 8000000, 9000000, 10000000, 12000000
        ]
        # 양육비 산정기준표 데이터 (표 6 참조)
        self.support_table = {
            "0-2":   [621000, 752000, 945000, 1098000, 1245000, 1401000, 1582000, 1789000, 1997000, 2095000, 2207000],
            "3-5":   [631000, 759000, 949000, 1113000, 1266000, 1422000, 1598000, 1807000, 2017000, 2116000, 2245000],
            "6-8":   [648000, 767000, 959000, 1140000, 1292000, 1479000, 1614000, 1850000, 2065000, 2137000, 2312000],
            "9-11":  [667000, 782000, 988000, 1163000, 1318000, 1494000, 1630000, 1887000, 2137000, 2180000, 2405000],
            "12-14": [679000, 790000, 998000, 1280000, 1423000, 1598000, 1711000, 1984000, 2159000, 2223000, 2476000],
            "15-18": [703000, 957000, 1227000, 1402000, 1604000, 1794000, 1964000, 2163000, 2246000, 2540000, 2883000]
        }

    def _get_age_group(self, age: int) -> str:
        if 0 <= age <= 2: return "0-2"
        elif 3 <= age <= 5: return "3-5"
        elif 6 <= age <= 8: return "6-8"
        elif 9 <= age <= 11: return "9-11"
        elif 12 <= age <= 14: return "12-14"
        elif 15 <= age <= 18: return "15-18"
        else: return None

    def _get_income_index(self, combined_income: int) -> int:
        return bisect.bisect_right(self.income_bins, combined_income)

    def calculate(self, custodial_income, non_custodial_income, children_ages, location, extra_expenses):
        combined_income = custodial_income + non_custodial_income
        income_idx = self._get_income_index(combined_income)
        
        base_support_total = 0
        details = []

        for age in children_ages:
            age_group = self._get_age_group(age)
            if age_group:
                base = self.support_table[age_group][income_idx]
                base_support_total += base
                details.append(f"만 {age}세: {base:,}원 ({age_group} 구간)")
            else:
                details.append(f"만 {age}세: 산정 제외 (성인)")

        child_count = len([a for a in children_ages if 0 <= a <= 18])
        
        # 가산요소: 자녀 수
        count_multiplier = 1.0
        if child_count == 1: count_multiplier = 1.065
        elif child_count >= 3: count_multiplier = 0.783
        
        # 가산요소: 거주지역
        location_multiplier = 1.0
        if location == "도시": location_multiplier = 1.079
        elif location == "농어촌": location_multiplier = 0.835

        adjusted_support = base_support_total * count_multiplier * location_multiplier
        final_total = adjusted_support + extra_expenses
        
        share_ratio = 0
        if combined_income > 0:
            share_ratio = non_custodial_income / combined_income
            
        final_payment = final_total * share_ratio
        
        return {
            "합산소득": combined_income,
            "기본양육비총액": base_support_total,
            "자녀수": child_count,
            "상세내역": details,
            "총예상양육비": round(final_total),
            "분담비율": round(share_ratio * 100, 1),
            "비양육자지급액": round(final_payment, -1)
        }

# --- 2. 화면 구성 (UI) ---
st.set_page_config(page_title="창원.경남 나자현 변호사의 자녀양육비 계산기", page_icon="⚖️")

st.title("⚖️ 서울가정법원 공표 2021년 양육비 산정기준표 계산기")
st.markdown("서울가정법원 공표 2021년 양육비 산정기준표 해설서에 기반한 자동 계산기입니다.")

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        custodial_income = st.number_input("양육자 월 세전 소득 (원)", min_value=0, step=100000, value=2000000)
    with col2:
        non_custodial_income = st.number_input("비양육자 월 세전 소득 (원)", min_value=0, step=100000, value=3000000)

    num_children = st.number_input("자녀 수", min_value=1, max_value=5, value=1)
    
    children_ages = []
    st.markdown("##### 자녀 만 나이 입력")
    cols = st.columns(num_children)
    for i in range(num_children):
        with cols[i]:
            age = st.number_input(f"자녀 {i+1} 나이", min_value=0, max_value=25, value=5, key=f"child_{i}")
            children_ages.append(age)

    with st.expander("추가 설정 (거주지, 추가 치료비 등)"):
        location = st.radio("거주 지역", ["일반", "도시", "농어촌"], index=0, horizontal=True)
        extra_expenses = st.number_input("월 추가 비용 (고액 치료비/교육비 등)", min_value=0, step=50000)

    if st.button("양육비 계산하기", type="primary"):
        calc = ChildSupportCalculator()
        try:
            res = calc.calculate(custodial_income, non_custodial_income, children_ages, location, extra_expenses)
            
            st.divider()
            st.subheader("📊 계산 결과")
            
            # 결과 표시
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("부모 합산 소득", f"{res['합산소득']:,}원")
            m_col2.metric("비양육자 분담 비율", f"{res['분담비율']}%")
            m_col3.metric("최종 지급 예상액", f"{res['비양육자지급액']:,}원")
            
            st.info(f"💡 비양육자가 매월 지급해야 할 예상 양육비는 **약 {res['비양육자지급액']:,}원** 입니다.")
            
            st.markdown("---")
            st.write("###### 상세 산출 내역")
            st.write(f"- **자녀별 표준양육비:** {', '.join(res['상세내역'])}")
            st.write(f"- **기본 합계:** {res['기본양육비총액']:,}원")
            
            if res['자녀수'] == 1:
                st.write("- **자녀 수 가산:** 1자녀 가산 (6.5%) 적용됨")
            elif res['자녀수'] >= 3:
                st.write("- **자녀 수 감산:** 다자녀 감산 (21.7%) 적용됨")
                
            if location != "일반":
                st.write(f"- **거주지 조정:** {location} 기준 적용됨")
                
            if extra_expenses > 0:
                st.write(f"- **추가 비용:** {extra_expenses:,}원 합산됨")

        except Exception as e:
            st.error(f"계산 중 오류가 발생했습니다: {e}")

st.markdown("---")
st.caption("※ 본 결과는 2021년 산정기준표에 따른 예상치이며, 실제 법원의 판결은 구체적인 사정에 따라 달라질 수 있습니다.")
