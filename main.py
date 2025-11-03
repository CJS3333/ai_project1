import streamlit as st
st.title('나의 첫 웹 서비스 만들기!!')
name=st.text_input('이름을 입력하세요:')
menu=st.selectbox('좋아하는 음식을 선택해주세요:',['마라탕'])
if st.button('인사말 생성'):
  st.info(name+'님! 안녕하세요')
  st.warning(menu+를 좋아하시나봐요! 저도 좋아해요!')
  st.error('정말 반가워요!!')
  st.balloons()
