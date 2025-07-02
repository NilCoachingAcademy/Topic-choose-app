from flask import Flask, render_template, request, redirect, url_for
import json
import os

app = Flask(__name__)

TOPICS_FILE = 'data/topics.json'
PARTICIPANTS_FILE = 'data/participants.json'

# ---------- ابزارهای کمکی ----------


def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------- صفحه اصلی (ورود اسم) ----------


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        name = request.form['name'].strip()
        participants = load_json(PARTICIPANTS_FILE)
        for p in participants:
            if p['name'].strip().lower() == name.strip().lower():
                return redirect(url_for('select', name=p['name']))
        return render_template('home.html', error="نام شما در لیست شرکت‌کننده‌ها یافت نشد.")
    return render_template('home.html')

# ---------- انتخاب سرفصل ----------


@app.route('/select/<name>', methods=['GET', 'POST'])
def select(name):
    topics = load_json(TOPICS_FILE)
    participants = load_json(PARTICIPANTS_FILE)

    participant = next((p for p in participants if p['name'] == name), None)
    if not participant:
        return "شرکت‌کننده یافت نشد", 404

    if name.strip().lower() == 'عرفان بشیری':
        return "<h2>شما به عنوان منتور وارد شدید و امکان انتخاب سرفصل ندارید.</h2>"

    selected_count = len(participant['selected'])

    # بررسی تعداد سرفصل‌های قابل انتخاب
    available_topics = [t for t in topics if t.get(
        'blocked') != True and t['chosen_by'] is None]
    remaining_count = len(available_topics)

    # قانون انتخاب: اگر <= ۳ تا سرفصل آزاد مونده → فقط ۱ انتخاب مجازه، وگرنه ۲ تا
    allowed = 1 if remaining_count <= 3 else 2

    if request.method == 'POST':
        selected_topics = request.form.getlist('topics')

        if len(selected_topics) + selected_count > allowed:
            return render_template('select.html', name=name, topics=topics,
                                   error=f"در حال حاضر فقط می‌توانید حداکثر {allowed} سرفصل انتخاب کنید.",
                                   selected=participant['selected'], allowed=allowed)

        conflicts = []
        for topic_id in selected_topics:
            topic = next((t for t in topics if str(t['id']) == topic_id and t.get(
                'blocked') != True and t['chosen_by'] is None), None)
            if topic:
                topic['chosen_by'] = name
                participant['selected'].append(topic['id'])
            else:
                conflicts.append(topic_id)

        if conflicts:
            save_json(TOPICS_FILE, topics)
            save_json(PARTICIPANTS_FILE, participants)
            return render_template('select.html', name=name, topics=topics,
                                   error="برخی سرفصل‌ها قبلاً انتخاب شده‌اند. لطفاً گزینه‌های آزاد را انتخاب کنید.",
                                   selected=participant['selected'], allowed=allowed)

        save_json(TOPICS_FILE, topics)
        save_json(PARTICIPANTS_FILE, participants)
        return redirect(url_for('done', name=name))

    return render_template('select.html', name=name, topics=topics,
                           selected=participant['selected'], allowed=allowed)

# ---------- صفحه پایان ----------


@app.route('/done/<name>')
def done(name):
    return f"<h2>{name} عزیز، انتخاب شما با موفقیت ذخیره شد. سپاسگزاریم.</h2>"

# ---------- پنل ادمین ----------


@app.route('/admin')
def admin():
    topics = load_json(TOPICS_FILE)
    participants = load_json(PARTICIPANTS_FILE)
    return render_template('admin.html', topics=topics, participants=participants)

@app.route('/admin/reset/<name>')
def reset_selection(name):
    topics = load_json(TOPICS_FILE)
    participants = load_json(PARTICIPANTS_FILE)

    person = next((p for p in participants if p['name'] == name), None)
    if not person:
        return f"<h3>شرکت‌کننده‌ای به نام {name} پیدا نشد.</h3>"

    # آزاد کردن سرفصل‌هایی که این فرد انتخاب کرده
    for topic in topics:
        if topic.get("chosen_by") == name:
            topic["chosen_by"] = None

    # پاک کردن انتخاب‌های این فرد
    person["selected"] = []

    save_json(TOPICS_FILE, topics)
    save_json(PARTICIPANTS_FILE, participants)

    return f"<h3>انتخاب‌های {name} با موفقیت پاک شدند ✅</h3>"

# ---------- اجرای برنامه ----------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
