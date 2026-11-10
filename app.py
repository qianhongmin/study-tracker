from flask import Flask , render_template , request ,redirect
import json, os
import sqlite3
import requests
import markdown
from datetime import date

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),"study.db")

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY","")

@app.route("/ask")
def ask():
    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers= {"Authorization": f"Bearer {DEEPSEEK_KEY}",
                  "Content-Type": "application/json"},
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "用一句话鼓励我学习"}],
        },
    )
    answer = resp.json()["choices"][0]["message"]["content"]
    return f"<h1>AI 说<h1><p>{answer}</p>"




@app.route("/")
def home():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM records").fetchall()

    stats = conn.execute("SELECT subject, SUM(minutes) AS total FROM records GROUP BY subject").fetchall()
    daily = conn.execute("SELECT date, SUM(minutes) AS total FROM records GROUP BY date ORDER BY date").fetchall()
    daily = [{"date": d["date"], "total": d["total"]} for d in daily]

    conn.close()

    return render_template("index.html",records=rows, stats=stats ,daily=daily)




@app.route("/add", methods=["POST"])
def add():
    subject = request.form["科目"]
    minutes = request.form["分钟"]
    note = request.form["笔记"]

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO records (date, subject, minutes, note) VALUES (?,?,?,?)",
        (str(date.today()), subject, minutes, note)
    )
    conn.commit()
    conn.close

    return redirect("/")

@app.route("/ai", methods=["GET", "POST"])
def ai():
    answer = None
    if request.method == "POST" :
        question = request.form["question"]
        resp = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_KEY}",
                     "Content-Type": "application/json"},
            json={"model": "deepseek-chat",
                  "messages": [{"role": "user", "content": question}]},
        )
        answer = resp.json()["choices"][0]["message"]["content"]
    return render_template("ask.html", answer=answer)



@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    questions = None
    if request.method == "POST" :
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        records = conn.execute("SELECT * FROM records").fetchall()
        conn.close()

        records_text = "" 
        for r in records:
            records_text += f"{r['date']}学了{r['subject']}{r['minutes']}分钟，笔记：{r['note']}\n "

        if not records:
            print("还没有学习记录，先去网页记几条再出题。")
        else:
            resp = requests.post(
                    "https://api.deepseek.com/chat/completions",
                    headers= {"Authorization": f"Bearer {DEEPSEEK_KEY}",
                            "Content-Type": "application/json"},
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "你是一位严谨的老师，只根据学生提供的学习记录出题，不要出记录里没有的科目。"},
                            {"role": "user", "content": f"这是我的学习记录：\n{records_text}\n请针对我学过的科目出 3 道复习题，并附答案。"}
                        ],
                    },
                )
            # questions = resp.json()["choices"][0]["message"]["content"]
            raw = resp.json()["choices"][0]["message"]["content"]
            questions = markdown.markdown(raw)

    return render_template("quiz.html",questions=questions)



@app.route("/summary", methods=["GET", "POST"])
def summary():
    summary_text = None
    if request.method == "POST" :
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        records = conn.execute("SELECT * FROM records").fetchall()
        conn.close()

        records_text = "" 
        for r in records:
            records_text += f"{r['date']}学了{r['subject']}{r['minutes']}分钟，笔记：{r['note']}\n "

        if not records:
            print("还没有学习记录，先去网页记几条再出题。")
        else:
            resp = requests.post(
                    "https://api.deepseek.com/chat/completions",
                    headers= {"Authorization": f"Bearer {DEEPSEEK_KEY}",
                            "Content-Type": "application/json"},
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "你是一位贴心的学习教练，根据学生的学习记录做总结并给出可执行的建议。"},
                            {"role": "user", "content": f"这是我最近的学习记录：\n{records_text}\n请帮我：1) 总结我的学习情况 2) 指出问题 3) 给出下周的具体建议。"}
                        ],
                    },
                )
            raw = resp.json()["choices"][0]["message"]["content"]
            summary_text = markdown.markdown(raw)

    return render_template("summary.html",summary=summary_text)




    # record = {"日期":str(date.today()),"科目":subject,"分钟":minutes,"笔记":note}

    # if os.path.exists("study_log.json"):
    #     with open("study_log.json","r",encoding="utf-8") as f:
    #         data = json.load(f)
    # else:
    #     data = []

    # # date = record.append(date)
    # data.append(record)

    with open("study_log.json","w" ,encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)

