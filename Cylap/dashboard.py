"""HoneyLens dashboard. Run with:  python -m streamlit run dashboard.py"""
import html
import json
from datetime import datetime
from pathlib import Path

import streamlit as st

NEWS_FILE = Path(__file__).resolve().parent / "news.json"

VULNS = [
    {
        "name": "Log4Shell", "cve": "CVE-2021-44228", "sev": "Critical 10.0",
        "en": "A flaw in the Log4j logging library lets an attacker make the server fetch and run code just by getting a crafted string written to a log, such as a User-Agent header.",
        "en_fix": "Fix: upgrade Log4j to 2.17.1 or later.",
        "ar": "ثغرة في مكتبة Log4j لتسجيل الأحداث. المهاجم يبعت نص خاص (زي في الـ User-Agent) والسيرفر يسجّله فيتنفّذ كود من بعيد.",
        "ar_fix": "الحل: تحديث Log4j لإصدار 2.17.1 أو أحدث.",
    },
    {
        "name": "EternalBlue", "cve": "CVE-2017-0144", "sev": "Critical 8.1",
        "en": "A bug in Microsoft SMBv1 allows remote code execution without logging in. It powered the WannaCry and NotPetya outbreaks.",
        "en_fix": "Fix: apply MS17-010 and disable SMBv1.",
        "ar": "ثغرة في بروتوكول SMBv1 من مايكروسوفت بتسمح بتنفيذ كود عن بُعد من غير تسجيل دخول. استُخدمت في هجمات WannaCry وNotPetya.",
        "ar_fix": "الحل: تثبيت تحديث MS17-010 وتعطيل SMBv1.",
    },
    {
        "name": "Heartbleed", "cve": "CVE-2014-0160", "sev": "High 7.5",
        "en": "A missing bounds check in OpenSSL's heartbeat feature lets attackers read chunks of server memory, which can include private keys and passwords.",
        "en_fix": "Fix: upgrade OpenSSL and rotate keys and certificates.",
        "ar": "نقص في فحص الحدود داخل خاصية heartbeat في OpenSSL بيخلّي المهاجم يقرا أجزاء من ذاكرة السيرفر، ممكن تحتوي على مفاتيح خاصة وباسوردات.",
        "ar_fix": "الحل: تحديث OpenSSL وتغيير المفاتيح والشهادات.",
    },
    {
        "name": "Shellshock", "cve": "CVE-2014-6271", "sev": "Critical 9.8",
        "en": "Bash executes commands hidden after a function definition in an environment variable. Web servers running CGI scripts passed attacker input straight into it.",
        "en_fix": "Fix: update Bash and retire old CGI scripts.",
        "ar": "الـ Bash بينفّذ أوامر مخفية بعد تعريف دالة جوه متغير بيئة. سيرفرات الويب اللي بتشغّل CGI كانت بتمرّر مدخلات المهاجم له مباشرة.",
        "ar_fix": "الحل: تحديث Bash والتخلص من سكربتات CGI القديمة.",
    },
    {
        "name": "regreSSHion", "cve": "CVE-2024-6387", "sev": "High 8.1",
        "en": "A race condition in OpenSSH's signal handler can give unauthenticated remote code execution as root on glibc-based Linux. Directly relevant to an SSH honeypot.",
        "en_fix": "Fix: upgrade OpenSSH to 9.8 or later.",
        "ar": "ثغرة race condition في معالج الإشارات داخل OpenSSH ممكن تدّي المهاجم تنفيذ كود عن بُعد بصلاحية root من غير مصادقة. مهمة جدًا لمشروع SSH honeypot.",
        "ar_fix": "الحل: تحديث OpenSSH لإصدار 9.8 أو أحدث.",
    },
]

st.set_page_config(page_title="HoneyLens", page_icon="🍯", layout="wide")
st.title("🍯 HoneyLens")
st.caption("Cyber news collected daily, plus famous vulnerabilities in English and Arabic")


@st.cache_data(ttl=60)
def load(path_str):
    p = Path(path_str)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def news_tab():
    data = load(str(NEWS_FILE))
    if data is None:
        st.error("news.json not found. Run  python news_collector.py  first, in the same folder.")
        return
    items = data.get("items", [])
    if not items:
        st.warning("news.json is empty. Run the collector again.")
        return

    st.caption(f"Last updated (UTC): {data.get('updated', 'unknown')}")
    tags = sorted({i["tag"] for i in items})
    sources = sorted({i["source"] for i in items})

    c1, c2, c3 = st.columns(3)
    c1.metric("Stories", len(items))
    c2.metric("Sources", len(sources))
    c3.metric("Ransomware stories", sum(i["tag"] == "Ransomware" for i in items))

    left, right = st.columns([1, 2])
    with left:
        chosen_tags = st.multiselect("Category", tags, default=tags)
        chosen_src = st.multiselect("Source", sources, default=sources)
        query = st.text_input("Search")
        st.bar_chart({t: sum(i["tag"] == t for i in items) for t in tags})

    shown = [
        i for i in items
        if i["tag"] in chosen_tags and i["source"] in chosen_src
        and query.lower() in (i["title"] + " " + i["summary"]).lower()
    ]
    with right:
        st.subheader(f"{len(shown)} stories")
        for i in shown[:100]:
            try:
                day = datetime.fromisoformat(i["published"]).strftime("%d %b %Y")
            except ValueError:
                day = ""
            st.markdown(f"**[{i['title']}]({i['link']})**")
            st.caption(f"{i['tag']} · {i['source']} · {day}")
            if i["summary"]:
                st.write(i["summary"])
            st.divider()


def vulns_tab():
    lang = st.radio("Language", ["English + عربي", "English", "عربي"], horizontal=True)
    cols = st.columns(2)
    for n, v in enumerate(VULNS):
        with cols[n % 2].container(border=True):
            st.subheader(v["name"])
            st.caption(f"{v['cve']} · {v['sev']}")
            if lang != "عربي":
                st.write(v["en"])
                st.markdown(f"**{v['en_fix']}**")
            if lang != "English":
                st.markdown(
                    f"<div dir='rtl' style='text-align:right'>{html.escape(v['ar'])}"
                    f"<br><b>{html.escape(v['ar_fix'])}</b></div>",
                    unsafe_allow_html=True,
                )


tab1, tab2 = st.tabs(["📰 News", "🛡️ Famous vulnerabilities"])
with tab1:
    news_tab()
with tab2:
    vulns_tab()
