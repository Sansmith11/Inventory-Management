import streamlit as st
import plotly.graph_objects as go

from data import PRODUCTS_DF
from inventory_tools import get_low_stock, inventory_value, calculate_reorder, what_if
from sarvam_client import speech_to_text, text_to_speech
from agent import ask_agent

st.set_page_config(page_title="AI Inventory Copilot", page_icon="🎙️", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []  # list of {role, content}

st.title("🎙️ AI Inventory Copilot")
st.caption("Multilingual voice assistant for Indian retail shops — powered by Sarvam AI")

# ---------- Overview metrics ----------
low_stock = get_low_stock()
total_value = inventory_value()["total_inventory_value"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Products", len(PRODUCTS_DF))
c2.metric("Inventory Value", f"₹{total_value:,.0f}")
c3.metric("🔴 Needs Reorder", len(low_stock))
c4.metric("🟢 Healthy Stock", len(PRODUCTS_DF) - len(low_stock))

st.divider()

# ---------- Voice assistant ----------
left, right = st.columns([1, 1])

with left:
    st.subheader("🎤 Talk to Inventory AI")
    audio = st.audio_input("Speak your question (any Indian language)")

    if audio is not None:
        with st.spinner("Transcribing..."):
            try:
                stt_result = speech_to_text(audio.getvalue(), filename="query.wav")
                transcript = stt_result["transcript"]
                lang = stt_result["language_code"]
            except Exception as e:
                st.error(f"Speech-to-text failed: {e}")
                transcript, lang = None, None

        if transcript:
            st.info(f"**Heard ({lang}):** {transcript}")
            with st.spinner("Thinking..."):
                try:
                    result = ask_agent(transcript, st.session_state.history)
                    reply = result["reply"]
                except Exception as e:
                    reply = None
                    st.error(f"Agent failed: {e}")

            if reply:
                st.session_state.history.append({"role": "user", "content": transcript})
                st.session_state.history.append({"role": "assistant", "content": reply})
                st.success(reply)
                with st.spinner("Generating voice reply..."):
                    try:
                        audio_bytes = text_to_speech(reply, language_code=lang or "en-IN")
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                    except Exception as e:
                        st.warning(f"Text-to-speech failed (showing text only): {e}")

    st.divider()
    st.subheader("💬 Conversation")
    for turn in st.session_state.history[-10:]:
        with st.chat_message(turn["role"]):
            st.write(turn["content"])

with right:
    st.subheader("📊 Products Requiring Attention")
    if low_stock:
        st.table(low_stock)
    else:
        st.write("Everything is healthy 🎉")

    st.subheader("📈 Stock vs Reorder Point")
    products = PRODUCTS_DF["product"].tolist()
    stocks = PRODUCTS_DF["current_stock"].tolist()
    rops = [calculate_reorder(p)["reorder_point"] for p in products]
    fig = go.Figure()
    fig.add_bar(name="Current Stock", x=products, y=stocks)
    fig.add_bar(name="Reorder Point", x=products, y=rops)
    fig.update_layout(barmode="group", height=350, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------- Scenario analysis ----------
st.subheader("🔮 What If? Scenario Analysis")
s1, s2 = st.columns([1, 2])
with s1:
    product_choice = st.selectbox("Product", PRODUCTS_DF["product"].tolist())
    pct = st.slider("Demand increase %", -50, 100, 20, step=5)
    if st.button("Run Scenario"):
        result = what_if(product_choice, pct)
        st.session_state["scenario_result"] = result

with s2:
    result = st.session_state.get("scenario_result")
    if result:
        b = result["baseline_recommended_order"]
        n = result["scenario_recommended_order"]
        st.write(f"**{result['product']}** — demand change: {result['demand_increase_pct']:+.0f}%")
        m1, m2, m3 = st.columns(3)
        m1.metric("Current Recommendation", f"{b} units")
        m2.metric("New Recommendation", f"{n} units", delta=f"{n - b:+d} units")
        m3.metric("Stockout Risk", "Reduced" if n > b else "Similar")
