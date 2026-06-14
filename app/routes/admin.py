from flask import Blueprint, render_template, request, redirect, url_for, send_file, jsonify, flash
from app.extensions import db
from io import BytesIO
import pandas as pd
from app.models.voter import Voter
from app.models.form import Form
from app.services.token_service import generate_token
from app.models.vote import Vote
from app.models.option import Option
from app.models.page import Page
from app.models.question import Question
from flask_login import login_required
from datetime import datetime
from app.models.history import FormHistory
import json


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/")
@login_required
def index():
    return redirect(url_for("admin.dashboard"))



@admin_bp.route("/forms")
@login_required
def forms_list():
    forms = Form.query.all()

    stats = {
        "total_forms": Form.query.count(),
        "active_forms": Form.query.filter_by(is_active=True).count(),
        "finalized_forms": Form.query.filter_by(is_finalized=True).count(),
        "draft_forms": Form.query.filter_by(status="draft").count(),
        "total_votes": Vote.query.count()
    }

    return render_template(
        "admin/forms_list.html",
        forms=forms,
        stats=stats
    )




@admin_bp.route("/create_form", methods=["GET", "POST"])
@login_required
def create_form():
    if request.method == "POST":
        action = request.form.get("action")
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if action == "cancel":
            flash("ایجاد فرم لغو شد.", "info")
            return redirect(url_for("admin.forms_list"))

        if not title:
            flash("عنوان فرم اجباری است.", "danger")
            return render_template("admin/create_form.html", title=title, description=description)

        if action in ("create", "create_and_builder"):
            form = Form(
                title=title,
                description=description,
                is_active=True
            )
            db.session.add(form)
            db.session.commit()

            flash("فرم با موفقیت ایجاد شد.", "success")

            if action == "create_and_builder":
                return redirect(url_for("admin.builder", form_id=form.id))

            return redirect(url_for("admin.forms_list"))

    return render_template("admin/create_form.html")


@admin_bp.route("/builder/<int:form_id>", methods=["GET"])
@login_required
def builder(form_id):
    form = Form.query.get_or_404(form_id)
    pages = Page.query.filter_by(form_id=form_id)\
    .order_by(Page.order)\
    .all()


    has_pages = len(pages) > 0   

    return render_template(
        "admin/builder.html",
        form=form,
        pages=pages,
        has_pages=has_pages      
    )


@admin_bp.route("/builder/<int:form_id>/page/<int:page_id>", methods=["GET"])
@login_required
def builder_page(form_id, page_id):
    form = Form.query.get_or_404(form_id)

    if form.is_finalized:
        flash("این فرم نهایی شده و قابل ویرایش نیست.", "warning")
        return redirect(url_for("admin.builder", form_id=form.id))

    page = Page.query.get_or_404(page_id)
    questions = Question.query.filter_by(page_id=page_id).all()

    # اضافه کردن مرتب‌سازی گزینه‌ها بر اساس فیلد order
    for q in questions:
        q.options = sorted(q.options, key=lambda o: o.order)

    questions = Question.query.filter_by(page_id=page_id).all()

    return render_template(
        "admin/builder_page.html",
        form=form,
        page=page,
        questions=questions
    )

@admin_bp.route("/add_page/<int:form_id>", methods=["POST"])
@login_required
def add_page(form_id):

    form = Form.query.get_or_404(form_id)

    if form.is_finalized:
        return jsonify({"status": "error"}), 403

    title = request.form.get("title")

    # گرفتن آخرین order
    last_page = Page.query.filter_by(form_id=form_id)\
        .order_by(Page.order.desc())\
        .first()

    next_order = 1
    if last_page:
        next_order = last_page.order + 1

    page = Page(
        form_id=form_id,
        title=title,
        order=next_order
    )

    db.session.add(page)
    db.session.commit()

    return jsonify({
        "status": "ok",
        "page": {
            "id": page.id,
            "title": page.title
        }
    })


@admin_bp.route("/add_question/<int:page_id>", methods=["POST"])
@login_required
def add_question(page_id):

    page = Page.query.get_or_404(page_id)
    form_id = page.form_id

    text = request.form.get("text")
    type = request.form["type"]
    min_select = request.form.get("min_select", 1)
    max_select = request.form.get("max_select", 1)

    question = Question(
        text=text,
        type=type,
        page_id=page.id,
        min_select=int(min_select),
        max_select=int(max_select)
    )

    db.session.add(question)
    db.session.commit()

    # ✅ ثبت در history
    save_history(
        form_id=form_id,
        action="add",
        entity_type="question",
        entity_id=question.id,
        data={
            "text": text,
            "min_select": min_select,
            "max_select": max_select
        }
    )
    print(request.form)
 

    return jsonify({

        "status": "ok",
        "question": {
            "id": question.id,
            "text": question.text,
            "min_select": question.min_select,
            "max_select": question.max_select,
            "options": []

        }
    })





@admin_bp.route("/add_option/<int:question_id>", methods=["POST"])
@login_required
def add_option(question_id):

    question = Question.query.get_or_404(question_id)
    form = Form.query.get_or_404(question.page.form_id)

    if form.is_finalized:
        flash("فرم نهایی شده و امکان افزودن گزینه وجود ندارد.", "warning")
        return redirect(url_for("admin.builder", form_id=form.id))

    text = request.form.get("text")

    opt = Option(question_id=question_id, text=text)
    db.session.add(opt)
    db.session.commit()

    save_history(
        form_id=form.id,   # ✅ استفاده از form موجود
        action="add",
        entity_type="option",
        entity_id=opt.id,
        data={
            "text": opt.text,
            "question_id": question_id
        }
    )

    page_id = opt.question.page_id

    return jsonify({

        "status": "ok",
        "option": {
            "id": opt.id,
            "text": opt.text
        }
    })





@admin_bp.route("/upload_direct/<int:form_id>", methods=["POST"])
@login_required
def upload_voters_direct(form_id):
    form = Form.query.get_or_404(form_id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    file = request.files.get("excel_file")
    if not file:
        msg = "هیچ فایلی انتخاب نشد."
        if is_ajax:
            return jsonify({"success": False, "message": msg}), 400
        flash(msg, "danger")
        return redirect(url_for("admin.forms_list"))

    try:
        df = pd.read_excel(
            file,
            converters={
                "national_id": lambda x: str(x).strip().replace(".0", ""),
                "phone": lambda x: str(x).strip().replace(".0", "")
            }
        )

        df["national_id"] = df["national_id"].astype(str).str.strip().str.zfill(10)

        count = 0
        for _, row in df.iterrows():
            voter = Voter(
                form_id=form.id,
                national_id=str(row["national_id"]).strip(),
                full_name=row["name"],
                phone=str(row["phone"]).strip()
            )
            db.session.add(voter)
            count += 1

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        msg = "خطا در پردازش فایل اکسل."
        if is_ajax:
            return jsonify({"success": False, "message": msg}), 500
        flash(msg, "danger")
        return redirect(url_for("admin.forms_list"))

    msg = f"لیست رأی‌دهندگان با موفقیت آپلود شد. ({count} نفر)"
    if is_ajax:
        return jsonify({
            "success": True,
            "message": msg,
            "added": count,
            "form_id": form.id
        })
    flash(msg, "success")
    return redirect(url_for("admin.forms_list"))


@admin_bp.route("/delete_voters/<int:form_id>")
@login_required
def delete_voters(form_id):
    form = Form.query.get_or_404(form_id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    deleted = Voter.query.filter_by(form_id=form.id).delete()
    db.session.commit()

    msg = f"{deleted} رأی‌دهنده حذف شد."
    if is_ajax:
        return jsonify({
            "success": True,
            "message": msg,
            "deleted": deleted,
            "form_id": form.id
        })
    flash(msg, "info")
    return redirect(url_for("admin.forms_list"))


@admin_bp.route('/finalize_form/<int:form_id>', methods=['POST'])
@login_required
def finalize_form(form_id):
    form = Form.query.get_or_404(form_id)

    if not form.pages:
        flash("فرم بدون صفحه قابل نهایی‌سازی نیست", "danger")
        return redirect(url_for("admin.builder", form_id=form_id))

    if not form.token or form.token.strip() == "":
        form.token = generate_token()

    form.is_finalized = True
    form.is_active = True

    db.session.commit()
    

    flash(f"فرم «{form.title}» با موفقیت نهایی شد.", "success")
    return redirect(url_for('admin.forms_list'))



@admin_bp.route("/delete_form/<int:form_id>")
@login_required
def delete_form(form_id):
    form = Form.query.get_or_404(form_id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    # حذف وابستگی‌ها
    Vote.query.filter_by(form_id=form.id).delete()
    Voter.query.filter_by(form_id=form.id).delete()

    pages = Page.query.filter_by(form_id=form.id).order_by(Page.order).all()
    for page in pages:
        questions = Question.query.filter_by(page_id=page.id).all()
        for q in questions:
            Option.query.filter_by(question_id=q.id).delete()
            db.session.delete(q)
        db.session.delete(page)

    db.session.delete(form)
    db.session.commit()

    msg = "فرم و تمام اطلاعات مرتبط با موفقیت حذف شد."
    if is_ajax:
        return jsonify({
            "success": True,
            "message": msg,
            "form_id": form_id
        })
    flash(msg, "success")
    return redirect(url_for("admin.forms_list"))


@admin_bp.route("/results/<int:form_id>")
@login_required
def results(form_id):
    form = Form.query.get_or_404(form_id)

    options = (
        Option.query
        .join(Question, Option.question_id == Question.id)
        .join(Page, Question.page_id == Page.id)
        .filter(Page.form_id == form_id)
        .all()
    )

    labels = []
    votes = []
    percentages = []

    total_votes = (
        Vote.query
        .join(Option, Vote.option_id == Option.id)
        .join(Question, Option.question_id == Question.id)
        .join(Page, Question.page_id == Page.id)
        .filter(Page.form_id == form_id)
        .count()
    )

    for option in options:
        count = Vote.query.filter_by(option_id=option.id).count()

        labels.append(option.text)
        votes.append(count)

        if total_votes > 0:
            percent = round((count / total_votes) * 100, 2)
        else:
            percent = 0

        percentages.append(percent)

    return render_template(
        "admin/results.html",
        form=form,
        labels=labels,
        votes=votes,
        percentages=percentages,
        total_votes=total_votes
    )


@admin_bp.route("/results/<int:form_id>/export")
@login_required
def export_results(form_id):
    form = Form.query.get_or_404(form_id)

    votes = (
        Vote.query
        .join(Voter, Vote.voter_id == Voter.id)
        .join(Option, Vote.option_id == Option.id)
        .filter(Vote.form_id == form.id)
        .all()
    )

    data = []

    for v in votes:
        data.append({
            "full_name": v.voter.full_name,
            "national_id": v.voter.national_id,
            "phone": v.voter.phone,
            "selected_option": v.option.text
        })

    df = pd.DataFrame(data)

    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    safe_title = form.title.replace(" ", "_")
    filename = f"{safe_title}_{now}.xlsx"

    return send_file(
        output,
        download_name=filename,
        as_attachment=True
    )


@admin_bp.route("/results/<int:form_id>/export-full")
@login_required
def export_full_results(form_id):
    form = Form.query.get_or_404(form_id)

    voters = Voter.query.filter_by(form_id=form.id).all()

    data = []

    for voter in voters:
        vote = Vote.query.filter_by(
            voter_id=voter.id,
            form_id=form.id
        ).first()

        if vote:
            option = Option.query.get(vote.option_id)
            option_text = option.text
            vote_time = vote.created_at
            voted = "YES"
        else:
            option_text = ""
            vote_time = ""
            voted = "NO"

        data.append({
            "full_name": voter.full_name,
            "national_id": voter.national_id,
            "phone": voter.phone,
            "voted": voted,
            "selected_option": option_text,
            "vote_time": vote_time
        })

    df = pd.DataFrame(data)

    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    safe_title = form.title.replace(" ", "_")
    filename = f"{safe_title}_{now}.xlsx"

    return send_file(
        output,
        download_name=filename,
        as_attachment=True
    )


@admin_bp.route('/results_data/<int:form_id>')
@login_required
def results_data(form_id):

    options = (
        Option.query
        .join(Question, Option.question_id == Question.id)
        .join(Page, Question.page_id == Page.id)
        .filter(Page.form_id == form_id)
        .all()
    )

    labels = []
    votes = []

    for option in options:
        count = Vote.query.filter_by(option_id=option.id).count()
        labels.append(option.text)
        votes.append(count)

    total_votes = sum(votes)

    percentages = [
        round((v / total_votes) * 100, 2) if total_votes > 0 else 0
        for v in votes
    ]

    return jsonify({
        "labels": labels,
        "votes": votes,
        "percentages": percentages,
        "total_votes": total_votes
    })


@admin_bp.route("/form/<int:form_id>/deactivate")
@login_required
def deactivate_form(form_id):
    form = Form.query.get_or_404(form_id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    form.is_active = False
    db.session.commit()

    if is_ajax:
        return jsonify({
            "success": True,
            "message": "فرم غیرفعال شد.",
            "form_id": form.id,
            "is_active": False
        })
    return redirect(url_for("admin.forms_list"))


@admin_bp.route("/form/<int:form_id>/activate")
@login_required
def activate_form(form_id):
    form = Form.query.get_or_404(form_id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    form.is_active = True
    db.session.commit()

    if is_ajax:
        return jsonify({
            "success": True,
            "message": "فرم فعال شد.",
            "form_id": form.id,
            "is_active": True
        })
    return redirect(url_for("admin.forms_list"))


@admin_bp.route("/form_created/<int:form_id>")
@login_required
def form_created(form_id):
    form = Form.query.get_or_404(form_id)
    return render_template("admin/form_created.html", form=form)


@admin_bp.route("/delete_question/<int:question_id>", methods=["POST"])
@login_required
def delete_question(question_id):
    q = Question.query.get_or_404(question_id)
    form = Form.query.get_or_404(q.page.form_id)

    if form.is_finalized:
        return jsonify({"status": "error", "message": "فرم نهایی شده است"}), 403

    # حذف گزینه‌های سؤال
    Option.query.filter_by(question_id=q.id).delete()

    page_id = q.page_id
    db.session.delete(q)
    db.session.commit()
    save_history(
    form_id=form.id,
    action="delete",
    entity_type="question",
    entity_id=q.id,
    data={
        "text": q.text,
        "page_id": q.page_id,
        "min_select": q.min_select,
        "max_select": q.max_select,
        "options": [{"id": o.id, "text": o.text, "order": o.order} for o in q.options]

        }
        )


    return jsonify({"status": "ok", "page_id": page_id})

@admin_bp.route("/delete_option/<int:option_id>", methods=["POST"])
@login_required
def delete_option(option_id):
    opt = Option.query.get_or_404(option_id)
    form = Form.query.get_or_404(opt.question.page.form_id)

    if form.is_finalized:
        return jsonify({"status": "error", "message": "فرم نهایی شده است"}), 403

    question_id = opt.question_id

    db.session.delete(opt)
    db.session.commit()
    save_history(
    form_id=form.id,
    action="delete",
    entity_type="option",
    entity_id=opt.id,
    data={"text": opt.text, "question_id": opt.question_id, "order": opt.order}

    )


    return jsonify({"status": "ok", "question_id": question_id})


@admin_bp.route("/delete_page/<int:page_id>", methods=["POST"])
@login_required
def delete_page(page_id):

    page = Page.query.get_or_404(page_id)
    form = Form.query.get_or_404(page.form_id)

    # ✅ اول سوالات را بگیر
    questions = Question.query.filter_by(page_id=page.id).all()

    save_history(
        form_id=form.id,
        action="delete",
        entity_type="page",
        entity_id=page.id,
        data={
            "title": page.title,
            "questions": [
                {
                    "id": q.id,
                    "text": q.text,
                    "min_select": q.min_select,
                    "max_select": q.max_select,
                    "options": [
                        {"id": o.id, "text": o.text, "order": o.order}
                        for o in q.options
                    ]
                }
                for q in questions
            ]
        }
    )

    if form.is_finalized:
        return jsonify({"status": "error", "message": "فرم نهایی شده است"}), 403

    # حذف سوالات و گزینه‌ها
    for q in questions:
        Option.query.filter_by(question_id=q.id).delete()
        db.session.delete(q)

    db.session.delete(page)
    db.session.commit()

    return jsonify({"status": "ok", "form_id": form.id})









@admin_bp.route("/reorder_options/<int:question_id>", methods=["POST"])
@login_required
def reorder_options(question_id):
    question = Question.query.get_or_404(question_id)
    form = Form.query.get_or_404(question.page.form_id)

    if form.is_finalized:
        return jsonify({"status": "error", "message": "فرم نهایی شده است"}), 403

    order_list = request.json.get("order", [])

    # اعمال ترتیب جدید
    for index, option_id in enumerate(order_list):
        opt = Option.query.get(int(option_id))
        if opt:
            opt.order = index

    db.session.commit()

    return jsonify({"status": "ok"})

@admin_bp.route("/form/<int:form_id>/preview", methods=["GET"])
@login_required
def preview_form(form_id):
    form = Form.query.get_or_404(form_id)

    pages = Page.query.filter_by(form_id=form.id)\
        .order_by(Page.order)\
        .all()

    if not pages:
        return render_template(
            "admin/preview_form.html",
            form=form,
            page=None,
            page_number=1,
            total_pages=0
        )

    page_number = request.args.get("page", 1, type=int)
    total_pages = len(pages)

    page_number = max(1, min(page_number, total_pages))

    current_page = pages[page_number - 1]

    for q in current_page.questions:
        q.options = sorted(q.options, key=lambda o: o.order)

    return render_template(
        "admin/preview_form.html",
        form=form,
        page=current_page,
        page_number=page_number,
        total_pages=total_pages
    )





@admin_bp.route("/preview/<string:token>", methods=["GET"])
def public_preview(token):
    form = Form.query.filter_by(token=token).first_or_404()

    if not form.is_finalized:
        return render_template("public/not_ready.html"), 403

    # pages = Page.query.filter_by(form_id=form.id).all()
    pages = Page.query.filter_by(form_id=form.id).order_by(Page.order).all()


    if not pages:
        return render_template(
            "public/preview_form_public.html",
            form=form,
            page=None,
            page_number=1,
            total_pages=0
        )

    page_number = request.args.get("page", 1, type=int)
    total_pages = len(pages)

    if page_number < 1:
        page_number = 1
    if page_number > total_pages:
        page_number = total_pages

    current_page = pages[page_number - 1]

    for q in current_page.questions:
        q.options = sorted(q.options, key=lambda o: o.order)

    return render_template(
        "public/preview_form_public.html",
        form=form,
        page=current_page,
        page_number=page_number,
        total_pages=total_pages
    )
def save_history(form_id, action, entity_type, entity_id, data):
    record = FormHistory(
        form_id=form_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        snapshot=json.dumps(data, ensure_ascii=False)
    )
    db.session.add(record)
    db.session.commit()

@admin_bp.route("/history/restore/<int:history_id>", methods=["POST"])
@login_required
def restore(history_id):

    h = FormHistory.query.get_or_404(history_id)
    data = json.loads(h.snapshot)

    # بازگردانی بر اساس نوع موجودیت
    if h.entity_type == "page":
        page = Page(id=h.entity_id, form_id=h.form_id, title=data["title"])
        db.session.merge(page)

    elif h.entity_type == "question":
        q = Question(
            id=h.entity_id,
            page_id=data["page_id"],
            text=data["text"],
            min_select=data["min_select"],
            max_select=data["max_select"],
        )
        db.session.merge(q)

        # گزینه‌ها
        for opt_data in data.get("options", []):
            opt = Option(
                id=opt_data["id"],
                text=opt_data["text"],
                question_id=q.id,
                order=opt_data["order"]
            )
            db.session.merge(opt)

    elif h.entity_type == "option":
        opt = Option(
            id=h.entity_id,
            text=data["text"],
            question_id=data["question_id"],
            order=data.get("order", 0)
        )

        db.session.merge(opt)

    db.session.commit()

    return jsonify({"status": "ok"})

@admin_bp.route("/history/<int:form_id>")
@login_required
def history_list(form_id):
    print("form_id =", form_id)


    records = FormHistory.query.filter_by(form_id=form_id)\
        .order_by(FormHistory.created_at.desc())\
        .limit(50)\
        .all()

    data = []

    for r in records:
        data.append({
            "id": r.id,
            "form_id": r.form_id,  
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")
        })

    return jsonify(data)

@admin_bp.route("/reorder_pages/<int:form_id>", methods=["POST"])
@login_required
def reorder_pages(form_id):

    data = request.get_json()
    new_order = data.get("pages", [])

    for index, page_id in enumerate(new_order, start=1):
        page = Page.query.filter_by(id=page_id, form_id=form_id).first()
        if page:
            page.order = index

    db.session.commit()

    return jsonify({"status": "ok"})

@admin_bp.route("/rename_page/<int:page_id>", methods=["POST"])
@login_required
def rename_page(page_id):

    data = request.get_json()
    new_title = data.get("title")

    if not new_title:
        return jsonify({"status": "error"}), 400

    page = Page.query.get_or_404(page_id)
    page.title = new_title

    db.session.commit()

    return jsonify({"status": "ok"})



@admin_bp.route("/duplicate_page/<int:page_id>", methods=["POST"])
@login_required
def duplicate_page(page_id):

    page = Page.query.get_or_404(page_id)

    # پیدا کردن آخرین order
    last_page = (
        Page.query
        .filter_by(form_id=page.form_id)
        .order_by(Page.order.desc())
        .first()
    )

    new_order = (last_page.order + 1) if last_page else 0

    # ساخت صفحه جدید
    new_page = Page(
        form_id=page.form_id,
        title=f"{page.title} (Copy)",
        order=new_order
    )

    db.session.add(new_page)
    db.session.flush()

    # کپی سوال‌ها
    for question in page.questions:

        new_question = Question(
            page_id=new_page.id,
            type=type,
            text=question.text,
            min_select=question.min_select,
            max_select=question.max_select
        )

        db.session.add(new_question)
        db.session.flush()

        # کپی گزینه‌ها
        for option in question.options:

            new_option = Option(
                question_id=new_question.id,
                text=option.text,
                order=option.order
            )

            db.session.add(new_option)

    db.session.commit()

    return jsonify({
        "status": "ok",
        "page": {

            "id": new_page.id,
            "title": new_page.title,
            "form_id": new_page.form_id,
        }
    })


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    stats = {
        "total_forms": Form.query.count(),
        "active_forms": Form.query.filter_by(is_active=True).count(),
        "finalized_forms": Form.query.filter_by(is_finalized=True).count(),
        "total_votes": Vote.query.count(),
        "draft_forms": Form.query.filter_by(status="draft").count()
    }
    forms = Form.query.order_by(Form.created_at.desc()).all()
    
    return render_template(
    "admin/dashboard.html",
    stats=stats,
    forms=forms)


@admin_bp.route("/upload_answer_file/<int:question_id>", methods=["POST"])
def upload_answer_file(question_id):
    uploaded = request.files.get("file")
    if not uploaded:
        return {"error": "no file"}, 400

    os.makedirs(f"static/uploads/{question_id}", exist_ok=True)

    filename = secure_filename(uploaded.filename)
    path = f"static/uploads/{question_id}/{filename}"
    uploaded.save(path)

    return {
        "file_url": url_for("static", filename=f"uploads/{question_id}/{filename}")
    }
