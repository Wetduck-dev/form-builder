from flask import Blueprint ,render_template ,request ,redirect ,url_for ,session
from app.models.voter import Voter
from app.models.form import Form
from app.models.otp import OTP
from app.services.sms_service import send_sms
from app.extensions import db
from app.models.option import Option
from app.models.vote import Vote
import random


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

        # مقایسه به صورت string
        if entered_code != str(otp.code):
            return "کد OTP اشتباه است"

        if not otp.is_valid():
            return "کد OTP منقضی شده"
        
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


@vote_bp.route("/cast/<token>/<int:voter_id>/<int:page_num>", methods=["GET", "POST"])
def cast_vote(token, voter_id, page_num):
    form = Form.query.filter_by(token=token).first_or_404()
    voter = Voter.query.get_or_404(voter_id)

    # اگر قبلاً رأی داده
    if voter.has_voted:
        return "قبلاً رأی داده‌اید!"

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

    # POST → ذخیره موقت پاسخ‌های این صفحه
    if request.method == "POST":
        for question in page.questions:
            selected = request.form.getlist(f"question_{question.id}")

            # محدودیت min/max
            if not (question.min_select <= len(selected) <= question.max_select):
                return f"تعداد انتخاب‌های سؤال «{question.text}» معتبر نیست", 400

            vote_data[str(question.id)] = selected

        session.modified = True  # ذخیره شود

        # اگر دکمه بعدی زده شد
        if "next" in request.form:
            return redirect(url_for("vote.cast_vote", token=token, voter_id=voter_id, page_num=page_num + 1))

        # اگر دکمه قبلی زده شد
        if "prev" in request.form:
            return redirect(url_for("vote.cast_vote", token=token, voter_id=voter_id, page_num=page_num - 1))

        # اگر در آخرین صفحه دکمه پایان زده شد
        if "finish" in request.form:
            return finalize_vote(form, voter, vote_data)

    return render_template(
        "vote/cast_page.html",
        form=form,
        voter=voter,
        page=page,
        page_num=page_num,
        total_pages=total_pages,
        vote_data=vote_data
    )

def finalize_vote(form, voter, vote_data):
    # حذف رأی‌های قبلی (نباید باشد ولی برای اطمینان)
    Vote.query.filter_by(voter_id=voter.id, form_id=form.id).delete()

    for qid, option_ids in vote_data.items():
        for opt_id in option_ids:
            v = Vote(
                form_id=form.id,
                voter_id=voter.id,
                question_id=int(qid),
                option_id=int(opt_id)
            )
            db.session.add(v)

    voter.has_voted = True
    db.session.commit()

    # پاک کردن session  
    session.pop("vote_data", None)

    return "رأی شما ثبت شد! "
