import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import os
import tempfile

# === yfinance Cloud cache 防護（解決常見後續錯誤）===
os.environ["YFINANCE_CACHE_DIR"] = tempfile.gettempdir()

st.set_page_config(page_title="HSI 短線助手", page_icon="🟦", layout="centered")
st.title("🟦 HSI 短線交易助手")
st.caption("全自動網頁版 v2.2 • 永久連結 • 已解決 yfinance 安裝問題")

hk_tz = pytz.timezone('Asia/Hong_Kong')
st.sidebar.markdown(f"**香港時間**<br>{datetime.now(hk_tz).strftime('%Y-%m-%d %H:%M:%S')}", unsafe_allow_html=True)

if st.button("🔄 一鍵抓取最新數據", type="primary", use_container_width=True):
    with st.spinner("正在從 Yahoo Finance 即時拉數據..."):
        try:
            # 恒指
            hsi = yf.Ticker("^HSI")
            hist_hsi = hsi.history(period="5d")
            yest_close = round(hist_hsi['Close'].iloc[-2], 1)
            today_open = round(hist_hsi['Open'].iloc[-1], 1) if len(hist_hsi) > 1 and not pd.isna(hist_hsi['Open'].iloc[-1]) else yest_close
            open_diff = today_open - yest_close

            # FXI
            fxi = yf.Ticker("FXI")
            hist_fxi = fxi.history(period="5d")
            fxi_open = round(hist_fxi['Open'].iloc[-1], 2)
            fxi_close = round(hist_fxi['Close'].iloc[-1], 2)
            fxi_is_bull = fxi_close > fxi_open

            # 外圍
            nasdaq = yf.Ticker("NQ=F")
            nikkei = yf.Ticker("NK=F")
            nasdaq_change = nasdaq.info.get('regularMarketChangePercent', 0)
            nikkei_change = nikkei.info.get('regularMarketChangePercent', 0)

            # 顯示
            col1, col2 = st.columns(2)
            with col1:
                st.metric("恒指昨日收市", f"{yest_close}", f"{open_diff:+.1f}點")
                st.metric("今日開盤", f"{today_open}")
            with col2:
                st.metric("FXI 開市", f"{fxi_open}", f"{fxi_close - fxi_open:+.2f}")
                st.metric("FXI 收市", f"{fxi_close}")

            st.metric("納指100期貨", f"{nasdaq_change:.2f}%", delta="升" if nasdaq_change > 0 else "跌")
            st.metric("日經225期貨", f"{nikkei_change:.2f}%", delta="升" if nikkei_change > 0 else "跌")

            # 計分（同之前一樣）
            open_score = 0
            if open_diff >= 400: open_score = -10
            elif open_diff >= 100: open_score = -2
            elif open_diff <= -400: open_score = 10
            elif open_diff <= -100: open_score = 2

            fxi_score = 2 if fxi_is_bull else -2
            nasdaq_score = 1 if nasdaq_change > 0 else -1
            nikkei_score = 1 if nikkei_change > 0 else -1
            outer_score = nasdaq_score + nikkei_score

            cbbc_score = st.selectbox("💰 JPM 牛熊證資金流（手動）",
                options=[0, 2, -2],
                format_func=lambda x: "中性" if x==0 else "熊證多 (+2)" if x==2 else "牛證多 (-2)",
                index=0)

            total = open_score + cbbc_score + outer_score + fxi_score

            # 信號
            if total >= 3: signal, color = "🟢 強買入信號", "green"
            elif total >= 1: signal, color = "🟡 偏好買入", "orange"
            elif total == 0: signal, color = "⚪ 觀望", "gray"
            elif total >= -2: signal, color = "🟠 偏好沽出", "orange"
            else: signal, color = "🔴 強沽出信號", "red"

            st.markdown(f"<h1 style='text-align:center; color:{color}; font-size:3rem;'>{signal}</h1>", unsafe_allow_html=True)
            st.metric("🎯 總分", total)

            st.dataframe(pd.DataFrame({"項目": ["開盤差", "牛熊證", "外圍(美+日)", "FXI"], "分數": [open_score, cbbc_score, outer_score, fxi_score]}), use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"網絡問題：{str(e)}")
            st.info("請稍後再試")

else:
    st.info("👆 點擊藍色按鈕就自動出信號！")
    st.caption("牛熊證仍需手動選擇（去 JPM 官網睇總和）")

st.caption("資料來源：Yahoo Finance • v2.2 已加 cache 防護")
