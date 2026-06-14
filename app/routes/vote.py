from flask import Blueprint ,render_template ,request ,redirect ,url_for ,session ,jsonify ,current_app
from app.models.voter import Voter
from app.models.form import Form
from app.models.otp import OTP
from app.services.sms_service import send_sms
from app.extensions import db
from app.models.option import Option
from app.models.vote import Vote
import random
import os
import uuid


vote_bp = Blueprint("vote", __name__)

@vote_bp.route("/<token>", methods=["GET", "POST"])
def vote_page(token):
    form = Form.query.filter_by(token=token).first_or_404()

    # ✅ اول بررسی فعال بودن فرم
    if not form.is_active:
        return "این فرم غیرفعال شده و امکان رأی دادن وجود ندارد."

    if request.method == "POST":
        national_id = request.form.get("national_id", "").strip()

        voter = Voter.query.filter_by(
            form_id=form.id,
            national_id=national_id
        ).first()

        if not voter:
            return "کد ملی معتبر نیست"

        # ✅ تولید OTP
        code = str(random.randint(100000, 999999))

        otp = OTP(
            phone=voter.phone,
            code=code
        )

        db.session.add(otp)
        db.session.commit()

        send_sms(voter.phone, f"Your code: {code}")

        return redirect(
            url_for("vote.verify_otp", token=token, nid=national_id)
        )

    return render_template("vote/login.html", form=form)

@vote_bp.route("/verify/<token>/<nid>", methods=["GET", "POST"])
def verify_otp(token, nid):
    form = Form.query.filter_by(token=token).first_or_404()
    voter = Voter.query.filter_by(form_id=form.id, national_id=nid).first_or_404()
    
    if request.method == "POST":
        entered_code = request.form.get("code", "").strip()

        # آخرین OTP ارسال شده برای این رأی‌دهنده
        otp = (
            OTP.query
            .filter_by(phone=voter.phone)
            .order_by(OTP.id.desc())
            .first()
        )
        if not otp:
            return "OTP پیدانشد"
        if not form.is_active:
            return "فرم غیرفعال است."


        print("Entered:", entered_code)
        print("DB Code:", otp.code)
        print("Type entered:", type(entered_code))
        print("Type db:", type(otp.code))


        if not otp:
            return "OTP پیدا نشد"
        
        if entered_code != str(otp.code):
            return render_template("vote/message.html", message="کد OTP اشتباه است")
        

        if not otp.is_valid():
            return render_template("vote/message.html", message="کد OTP منقضی شده")

        # ✅ اگر قبلاً رأی داده
        if voter.has_voted:
            return redirect(url_for("vote.vote_result", token=token, voter_id=voter.id))

        # ✅ اگر هنوز رأی نداده
        return redirect(url_for("vote.cast_vote", token=token, voter_id=voter.id, page_num=1))



        



    return render_template("vote/otp.html", form=form, voter=voter)


# @vote_bp.route("/cast/<token>/<int:voter_id>", methods=["GET", "POST"])
# def cast_vote(token, voter_id):
#     form = Form.query.filter_by(token=token).first_or_404()
#     voter = Voter.query.get_or_404(voter_id)

#     # قبلاً رأی داده؟
#     if voter.has_voted:
#         return "قبلاً رأی داده‌اید!"

#     # فعال است؟
#     if not form.is_active:
#         return "رأی‌گیری غیرفعال شده است."

#     # POST → پردازش رأی
#     if request.method == "POST":

#         # برای هر سؤال در هر صفحه رأی جمع می‌کنیم
#         for page in form.pages:
#             for question in page.questions:

#                 # دریافت گزینه‌های انتخاب‌شده این سؤال
#                 selected_option_ids = request.form.getlist(f"question_{question.id}")

#                 # چک min/max
#                 if not (question.min_select <= len(selected_option_ids) <= question.max_select):
#                     return f"تعداد انتخاب‌های سؤال «{question.text}» معتبر نیست", 400

#                 # ثبت رأی
#                 for opt_id in selected_option_ids:
#                     option = Option.query.filter_by(id=opt_id, question_id=question.id).first()
#                     if not option:
#                         return f"گزینه نامعتبر در سؤال «{question.text}»", 400

#                     vote = Vote(
#                         form_id=form.id,
#                         voter_id=voter.id,
#                         question_id=question.id,
#                         option_id=option.id
#                     )
#                     db.session.add(vote)

#         # علامت‌گذاری رأی‌دهنده
#         voter.has_voted = True
#         db.session.commit()

#         return "رأی شما با موفقیت ثبت شد"

#     # GET → نمایش فرم رأی‌گیری
#     return render_template("vote/cast.html", form=form, voter=voter)

# @vote_bp.route("/result/<token>/<int:voter_id>")
# def vote_result(token, voter_id):
#     form = Form.query.filter_by(token=token).first_or_404()
#     voter = Voter.query.get_or_404(voter_id)

#     if not voter.has_voted:
#         return redirect(url_for("vote.cast_vote", token=token, voter_id=voter.id, page_num=1))

#     return render_template("vote/result.html", form=form, voter=voter)

@vote_bp.route("/result/<token>/<int:voter_id>")
def vote_result(token, voter_id):
    form = Form.query.filter_by(token=token).first_or_404()
    voter = Voter.query.get_or_404(voter_id)

    if not voter.has_voted:
        return redirect(url_for("vote.cast_vote", token=token, voter_id=voter.id, page_num=1))

    # گرفتن تمام رأی‌های این کاربر
    votes = Vote.query.filter_by(
        form_id=form.id,
        voter_id=voter.id
    ).all()

    # گروه‌بندی بر اساس question
    result_data = {}

    for vote in votes:
        q = vote.question

        if q.id not in result_data:
            result_data[q.id] = {
                "question_text": q.text,
                "options": []
            }

        result_data[q.id]["options"].append(vote.option.text)

    return render_template(
        "vote/result.html",
        form=form,
        voter=voter,
        result_data=result_data
    )

@vote_bp.route("/cast/<token>/<int:voter_id>/<int:page_num>", methods=["GET", "POST"])
def cast_vote(token, voter_id, page_num):
    form = Form.query.filter_by(token=token).first_or_404()
    voter = Voter.query.get_or_404(voter_id)

    # تشخیص AJAX
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    # اگر قبلاً رأی داده
    if voter.has_voted:
        redirect_url = url_for("vote.vote_result", token=token, voter_id=voter.id)
        if is_ajax:
            return jsonify({"redirect": redirect_url})
        return redirect(redirect_url)

    if not form.is_active:
        return "فرم غیرفعال است."

    # مرتب‌سازی صفحات
    pages = sorted(form.pages, key=lambda p: p.id)
    total_pages = len(pages)

    # اگر شماره صفحه معتبر نیست
    if page_num < 1 or page_num > total_pages:
        return "صفحه وجود ندارد.", 404

    page = pages[page_num - 1]

    # ایجاد فضای ذخیره موقت
    if "vote_data" not in session:
        session["vote_data"] = {}

    vote_data = session["vote_data"]
    error_message = None

    if request.method == "POST":
        for question in page.questions:

            key = f"question_{question.id}"

            # -----------------------
            # 1) file / image  (✅ فقط این بخش تغییر کرده)
            # -----------------------
            if question.type in ["file", "image"]:
                uploaded_file = request.files.get(key)

                if uploaded_file and uploaded_file.filename:
                    ext = uploaded_file.filename.rsplit(".", 1)[-1].lower()
                    filename = f"{uuid.uuid4().hex}.{ext}"

                    # مسیر: static/uploads/votes/<form_token>/<national_id>/
                    upload_path = os.path.join(
                        current_app.static_folder,
                        "uploads",
                        "votes",
                        form.token,
                        str(voter.national_id)
                    )
                    os.makedirs(upload_path, exist_ok=True)

                    # ذخیره فایل روی دیسک
                    full_path = os.path.join(upload_path, filename)
                    uploaded_file.save(full_path)

                    # مسیر نسبی برای استفاده در قالب‌ها / session
                    rel_path = f"uploads/votes/{form.token}/{voter.national_id}/{filename}"

                    # ذخیره در vote_data
                    vote_data[str(question.id)] = [f"FILE:{rel_path}"]
                else:
                    vote_data[str(question.id)] = []

            # -----------------------
            # 2) select / multi-select
            # -----------------------
            elif question.type in ["select", "multi-select"]:
                selected = request.form.getlist(key)

                if not (question.min_select <= len(selected) <= question.max_select):
                    error_message = f"تعداد انتخاب‌های سؤال «{question.text}» معتبر نیست"

                    if is_ajax:
                        return jsonify({
                            "error": error_message,
                            "question_id": question.id
                        })

                    return render_template(
                        "vote/cast_page.html",
                        form=form,
                        voter=voter,
                        page=page,
                        page_num=page_num,
                        total_pages=total_pages,
                        vote_data=vote_data,
                        error_message=error_message
                    )

                vote_data[str(question.id)] = selected

            # -----------------------
            # 3) text / textarea / number / date
            # -----------------------
            else:
                value = request.form.get(key, "")
                vote_data[str(question.id)] = [value]

        session.modified = True

        # دکمه next
        if "next" in request.form and page_num < total_pages:
            redirect_url = url_for(
                "vote.cast_vote",
                token=token,
                voter_id=voter_id,
                page_num=page_num + 1
            )
            if is_ajax:
                return jsonify({"redirect": redirect_url})
            return redirect(redirect_url)

        # دکمه prev
        if "prev" in request.form and page_num > 1:
            redirect_url = url_for(
                "vote.cast_vote",
                token=token,
                voter_id=voter_id,
                page_num=page_num - 1
            )
            if is_ajax:
                return jsonify({"redirect": redirect_url})
            return redirect(redirect_url)

        # دکمه finish
        if "finish" in request.form:
            result = finalize_vote(form, voter, vote_data)
            if is_ajax and hasattr(result, "location"):
                return jsonify({"redirect": result.location})
            return result

    return render_template(
        "vote/cast_page.html",
        form=form,
        voter=voter,
        page=page,
        page_num=page_num,
        total_pages=total_pages,
        vote_data=vote_data,
        error_message=error_message
    )

def finalize_vote(form, voter, vote_data):
    Vote.query.filter_by(voter_id=voter.id, form_id=form.id).delete()

    for qid, option_ids in vote_data.items():
        for opt_id in option_ids:
            # اگر فایل است، فعلا در Vote ذخیره نکن (باید مدل جداگانه داشته باشی)
            if isinstance(opt_id, str) and opt_id.startswith("FILE:"):
                # اینجا در آینده می‌تونی مدل FileAnswer بسازی و ذخیره‌اش کنی
                continue

            v = Vote(
                form_id=form.id,
                voter_id=voter.id,
                question_id=int(qid),
                option_id=int(opt_id)
            )
            db.session.add(v)

    voter.has_voted = True
    db.session.commit()
    session.pop("vote_data", None)

    return redirect(
        url_for("vote.vote_result", token=form.token, voter_id=voter.id)
    )
