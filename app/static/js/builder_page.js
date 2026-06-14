document.addEventListener("DOMContentLoaded", function () {

    // ✅ Drag & Drop گزینه‌ها (بدون تغییر)
    document.querySelectorAll(".options-list").forEach(list => {
        const questionId = list.dataset.questionId;
        new Sortable(list, {
            animation: 150,
            onEnd: function () {
                const ids = [...list.querySelectorAll(".option-item")]
                    .map(el => el.dataset.optionId);
                fetch(`/admin/reorder_options/${questionId}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ order: ids })
                });
            }
        });
    });

    // ✅ حذف گزینه (اصلاح‌شده — بدون reload)
    document.querySelectorAll(".delete-option").forEach(btn => {
        btn.addEventListener("click", async function () {
            const id = this.dataset.id;
            if (!confirm("این گزینه حذف شود؟")) return;

            const res = await fetch(`/admin/delete_option/${id}`, { method: "POST" });
            const data = await res.json();
            if (data.status === "ok") {
                this.closest("tr").remove();
            } else {
                console.error("خطا در حذف گزینه:", data.message || data);
            }
        });
    });

    // ✅ حذف صفحه (بدون تغییر)
    document.querySelectorAll(".delete-page").forEach(btn => {
        btn.addEventListener("click", function () {
            const pageId = this.dataset.pageId;
            if (!confirm("آیا از حذف این صفحه مطمئن هستید؟")) return;
            fetch(`/admin/delete_page/${pageId}`, { method: "POST" })
                .then(res => res.json())
                .then(data => {
                    if (data.status === "ok") {
                        const el = document.querySelector(`#page-${pageId}`);
                        if (el) el.remove();
                    }
                })
                .catch(err => console.error("Error deleting page:", err));
        });
    });


    // ✅ حذف سؤال (اصلاح‌شده — بدون reload)
    document.querySelectorAll(".delete-question").forEach(btn => {
        btn.addEventListener("click", async function () {
            const id = this.dataset.id;
            if (!confirm("این سوال حذف شود؟")) return;

            const res = await fetch(`/admin/delete_question/${id}`, { method: "POST" });
            const data = await res.json();
            if (data.status === "ok") {
                this.closest(".dashboard-card").remove();
            } else {
                console.error("خطا در حذف سؤال:", data.message || data);
            }
        });
    });


    // ✅ افزودن سؤال جدید بدون رفرش
    const addQuestionForm = document.querySelector('form[action^="/admin/add_question/"]');
    if (addQuestionForm) {
        addQuestionForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const formData = new FormData(addQuestionForm);
            const res = await fetch(addQuestionForm.action, { method: "POST", body: formData });
            const data = await res.json();

            if (data.status === "ok") {
                addQuestionToUI(data.question);
                addQuestionForm.reset();
            } else {
                console.error("خطا در افزودن سؤال:", data.message || data);
            }
        });
    }

    function addQuestionToUI(q) {
        const container = document.querySelector(".forms-container");
        const div = document.createElement("div");
        div.classList.add("dashboard-card");
        div.innerHTML = `
            <div class="builder-card-header">
                <div class="page-info">
                    <h4 style="margin:0;">${q.text}</h4>
                    <small>انتخاب: حداقل ${q.min_select} / حداکثر ${q.max_select}</small>
                </div>
                <div class="form-actions">
                    <button class="glass-btn danger delete-question" data-id="${q.id}">🗑 حذف سوال</button>
                </div>
            </div>
            <form method="POST" action="/admin/add_option/${q.id}" style="margin-top:20px;">
                <div class="field-group">
                    <input type="text" name="text" placeholder=" " required>
                    <label>متن گزینه</label>
                </div>
                <button class="glass-btn" style="background:#6366f1;">➕ افزودن گزینه</button>
            </form>
            <table class="table-modern" style="margin-top:15px;">
                <thead>
                    <tr><th>گزینه‌ها</th><th style="width:120px;">عملیات</th></tr>
                </thead>
                <tbody></tbody>
            </table>
        `;
        container.appendChild(div);

        // وصل کردن event حذف سؤال جدید
        div.querySelector(".delete-question").addEventListener("click", function () {
            if (!confirm("این سوال حذف شود؟")) return;
            fetch(`/admin/delete_question/${q.id}`, { method: "POST" })
                .then(res => res.json())
                .then(data => { if (data.status === "ok") div.remove(); });
        });

        // وصل رویداد افزودن گزینه روی فرم جدید
        attachOptionFormHandler(div.querySelector('form'));
    }


    // ✅ افزودن گزینه جدید بدون رفرش
    document.querySelectorAll('form[action^="/admin/add_option/"]').forEach(form => attachOptionFormHandler(form));

    function attachOptionFormHandler(form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            const formData = new FormData(form);
            const res = await fetch(form.action, { method: "POST", body: formData });
            const data = await res.json();

            if (data.status === "ok") {
                addOptionToUI(form, data.option);
                form.reset();
            } else {
                console.error("خطا در افزودن گزینه:", data.message || data);
            }
        });
    }

    function addOptionToUI(form, opt) {
        const tbody = form.nextElementSibling.querySelector("tbody");
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${opt.text}</td>
            <td><button class="glass-btn danger delete-option" data-id="${opt.id}">حذف</button></td>
        `;
        tbody.appendChild(tr);

        const btn = tr.querySelector(".delete-option");
        btn.addEventListener("click", async function () {
            if (!confirm("این گزینه حذف شود؟")) return;
            const res = await fetch(`/admin/delete_option/${opt.id}`, { method: "POST" });
            const data = await res.json();
            if (data.status === "ok") tr.remove();
        });
    }


    // const typeSelect = document.querySelector('select[name="type"]');
    // const minSelectField = document.querySelector('input[name="min_select"]')?.closest('.field-group');
    // const maxSelectField = document.querySelector('input[name="max_select"]')?.closest('.field-group');
    

    // function toggleSelectionLimits() {

    //     const selectedType = typeSelect.value;

    //     // فقط اگر "چند انتخابی" بود فیلدها رو نشون بده
    //     if (selectedType === "multi-select") {
            
    //         minSelectField.style.display = "block";
    //         maxSelectField.style.display = "block";
    //     } else {
    //         minSelectField.style.display = "none";
    //         maxSelectField.style.display = "none";
    //         // مقادیر پیش‌فرض رو ۱ بزار که دیتابیس ارور نده
    //         minSelectField.querySelector('input').value = 1;
    //         maxSelectField.querySelector('input').value = 1;
    //     }
    // }

    // if (typeSelect) {
    //     typeSelect.addEventListener("change", toggleSelectionLimits);
    //     toggleSelectionLimits(); // اجرای اولیه برای تنظیم حالت پیش‌فرض
    // }


    const typeSelect = document.querySelector('select[name="type"]');
    const minSelectField = document.querySelector('input[name="min_select"]')?.closest('.field-group');
    const maxSelectField = document.querySelector('input[name="max_select"]')?.closest('.field-group');
    

    function toggleSelectionLimits() {

        const selectedType = typeSelect.value;

        // فقط اگر "چند انتخابی" بود فیلدها رو نشون بده
        if (selectedType === "multi-select") {
            
            minSelectField.style.display = "block";
            maxSelectField.style.display = "block";
        } 
        
        // پنهان برای بقیه انواع
        else {
            minSelectField.style.display = "none";
            maxSelectField.style.display = "none";

            // جلوگیری از Error دیتابیس
            minSelectField.querySelector('input').value = 1;
            maxSelectField.querySelector('input').value = 1;
        }

        // 🔥 NEW: جلوگیری از نمایش گزینه‌ها برای image/file
        const optionsSection = document.querySelector('.options-section');
        if (optionsSection) {
            if (selectedType === "select" || selectedType === "multi-select") {
                optionsSection.style.display = "block";
            } else {
                optionsSection.style.display = "none";
            }
        }
    }

    if (typeSelect) {
        typeSelect.addEventListener("change", toggleSelectionLimits);
        toggleSelectionLimits();
    }


});
