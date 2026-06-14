console.log("BUILDER.JS >>> I AM NEW VERSION");
console.log("window.formId at load:", window.formId);
console.log("builder.js loaded");
console.log("window.formId at load:", window.formId);
document.addEventListener("DOMContentLoaded", () => {


    // DUPLICATE PAGE
    document.addEventListener("click", function(e) {


        const btn = e.target.closest(".duplicate-page");
        if (!btn) return;

        const pageId = btn.dataset.pageId;

        fetch(`/admin/duplicate_page/${pageId}`, {

            method: "POST"

        })
        .then(res => res.json())
        .then(data => {


            if (data.status !== "ok") {
                alert("خطا در کپی صفحه");
                return;

            }

            const page = data.page;
            const container = document.getElementById("pagesContainer");
            const html = `

            <div class="builder-card" id="page-${page.id}">

                <div class="builder-card-header">


                    <div class="page-info">
                        <div class="drag-handle">☰</div>
                        <div>
                            <h4 class="page-title-text"
                                data-page-id="${page.id}">
                                ${page.title}
                            </h4>
                            <small style="color: rgba(255,255,255,0.4);">
                                ID: #${page.id}
                            </small>
                        </div>
                    </div>

                    <div class="form-actions">
                        <button class="glass-btn duplicate-page"
                            data-page-id="${page.id}">
                            📄 کپی
                        </button>

                        <a href="/admin/builder/${window.formId}/page/${page.id}"
                            class="glass-btn">
                            ✏️ ویرایش محتوا
                        </a>

                        <button class="glass-btn danger delete-page"
                            data-page-id="${page.id}">
                            🗑 حذف
                        </button>
                    </div>

                </div>
            </div>
            `;

            container.insertAdjacentHTML("beforeend", html);

        });

    });

    // بقیه فایل بدون تغییر






    // =======================================
// INLINE RENAME PAGE
// =======================================

    document.addEventListener("dblclick", function(e) {


        const titleEl = e.target.closest(".page-title-text");
        if (!titleEl) return;


        const pageId = titleEl.dataset.pageId;
        const oldTitle = titleEl.innerText;

        const input = document.createElement("input");
        input.type = "text";
        input.value = oldTitle;
        input.className = "inline-rename-input";

        titleEl.replaceWith(input);
        input.focus();
        input.select();

        function save() {

            const newTitle = input.value.trim();

            if (!newTitle || newTitle === oldTitle) {
                input.replaceWith(titleEl);
                return;
            }

            fetch(`/admin/rename_page/${pageId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title: newTitle })
            })
            .then(res => res.json())
            .then(data => {

                if (data.status === "ok") {
                    titleEl.innerText = newTitle;
                }

                input.replaceWith(titleEl);
            });
        }

    input.addEventListener("blur", save);

    input.addEventListener("keydown", function(e) {
        if (e.key === "Enter") save();
        if (e.key === "Escape") input.replaceWith(titleEl);
    });

});




    // =============================
// DRAG & DROP PAGE SORTING
// =============================

    const pagesContainer = document.getElementById("pagesContainer");


    if (pagesContainer) {

        new Sortable(pagesContainer, {

            animation: 150,

            handle: ".drag-handle",
            ghostClass: "drag-ghost",
            onEnd: () => {
                saveNewPageOrder();

            }

        });
    }

    function saveNewPageOrder() {

        const ids = [...document.querySelectorAll(".builder-card")]
            .map(card => parseInt(card.id.replace("page-","")));

        fetch(`/admin/reorder_pages/${window.formId}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ pages: ids })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status !== "ok") {
                alert("خطا در ذخیره ترتیب صفحات");
            }
        });
    }





    // =============================
// ADD PAGE (AJAX)
// =============================

    const addPageForm = document.getElementById("addPageForm");

    if (addPageForm) {

        addPageForm.addEventListener("submit", function(e) {

            e.preventDefault();


            const formData = new FormData(addPageForm);
            const action = addPageForm.action;

            fetch(action, {
                method: "POST",
                body: formData
            })
            .then(res => res.json())
            .then(data => {

                if (data.status !== "ok") {
                    alert("خطا در ایجاد صفحه");
                    return;
                }

                const page = data.page;

                const container = document.getElementById("pagesContainer");

                const card = document.createElement("div");
                card.className = "builder-card";
                card.id = `page-${page.id}`;

                card.style.opacity = "0";
                card.style.transform = "translateY(20px)";
                card.innerHTML = `
                    <div class="builder-card-header">

                        <div class="page-info">

                            <div class="drag-handle">☰</div>

                            <div>
                                <h4 class="page-title-text"
                                    data-page-id="${page.id}"
                                    style="color:white; margin:0; cursor:pointer;">
                                    ${page.title}
                                </h4>

                                <small style="color: rgba(255,255,255,0.4);">
                                    ID: #${page.id}
                                </small>
                            </div>

                        </div>

                        <div class="form-actions">

                            <button class="glass-btn duplicate-page"
                                data-page-id="${page.id}">
                                📄 کپی
                            </button>

                            <a href="/admin/builder/${window.formId}/page/${page.id}"
                            class="glass-btn">
                            ✏️ ویرایش محتوا
                            </a>

                            <button class="glass-btn danger delete-page"
                                data-page-id="${page.id}">
                                🗑 حذف
                            </button>

                        </div>

                    </div>
                `;


                container.appendChild(card);

                // animation
                setTimeout(() => {
                    card.style.transition = "all .4s ease";
                    card.style.opacity = "1";
                    card.style.transform = "translateY(0)";
                }, 50);

                addPageForm.reset();
            });

        });

    }


    // =====================================================================
    // حذف صفحه
    // =====================================================================
    document.addEventListener("click", function(e) {
        
        const btn = e.target.closest(".delete-page");

        if (!btn) return;


        const pageId = btn.dataset.pageId;

        const card = document.querySelector(`#page-${pageId}`);


        if (!confirm("آیا از حذف این صفحه مطمئن هستید؟")) return;


        fetch(`/admin/delete_page/${pageId}`, {

            method: "POST"

        })
        .then(res => res.json())
        .then(data => {

            if (data.status === "ok") {

                card.style.transition = "all .4s ease";
                card.style.opacity = "0";
                card.style.transform = "translateX(50px)";

                setTimeout(() => card.remove(), 400);

            } else {
                alert("خطا در حذف");
            }

        });

    });




    // =====================================================================
    // حذف سوال
    // =====================================================================
    document.addEventListener("click", function(e) {

        if (e.target.classList.contains("delete-question")) {

            const qId = e.target.dataset.id;

            if (!confirm("سوال حذف شود؟")) return;

            fetch(`/admin/delete_question/${qId}`, {
                method: "POST"
            })
            .then(res => res.json())
            .then(data => {

                if (data.status === "ok") {
                    // حذف کارت سوال
                    document.querySelector(`#question-${qId}`)?.remove();
                }
            });
        }

    });


    // =====================================================================
    // حذف گزینه
    // =====================================================================
    document.addEventListener("click", function(e) {

        if (e.target.classList.contains("delete-option")) {

            const optId = e.target.dataset.id;

            if (!confirm("گزینه حذف شود؟")) return;

            fetch(`/admin/delete_option/${optId}`, {
                method: "POST"
            })
            .then(res => res.json())
            .then(data => {

                if (data.status === "ok") {
                    document.querySelector(`#option-${optId}`)?.remove();
                }
            });
        }

    });

});

// =============================
// HISTORY MODAL
// =============================

let historyRequestToken = 0;

window.openHistory = function() {

    const list = document.getElementById("historyList");
    const modal = document.getElementById("historyModal");

    // تولید توکن جدید برای این درخواست
    const currentToken = ++historyRequestToken;

    // پاکسازی فوری
    list.innerHTML = "<p style='opacity:0.6; padding:10px'>در حال بارگذاری...</p>";
    modal.style.display = "flex";

    fetch(`/admin/history/${window.formId}`)
    .then(res => res.json())
    .then(data => {

        // اگر این پاسخ مربوط به آخرین درخواست نیست، نادیده بگیر
        if (currentToken !== historyRequestToken) return;

        list.innerHTML = "";

        if (!data || data.length === 0) {
            list.innerHTML = "<p style='color:#ccc'>تاریخچه‌ای وجود ندارد.</p>";
            return;
        }

        data.forEach(item => {

            let icon = "📝";
            let badge = "";

            if (item.action === "add") {
                icon = "➕";
                badge = "history-add";
            }

            if (item.action === "delete") {
                icon = "🗑";
                badge = "history-delete";
            }

            if (item.action === "update") {
                icon = "✏️";
                badge = "history-update";
            }

            const div = document.createElement("div");
            div.className = "history-item";

            div.innerHTML = `
                <div class="history-dot"></div>

                <div style="color:white; font-size:14px; margin-bottom:4px;">
                    ${icon}
                    <span class="history-badge ${badge}">
                        ${item.action}
                    </span>
                    ${item.entity_type}
                </div>

                <div class="history-time">
                    ${item.created_at}
                </div>

                <div style="margin-top:8px;">
                    <button class="glass-btn" onclick="restoreHistory(${item.id})">
                        ↩ بازگردانی
                    </button>
                </div>
            `;

            list.appendChild(div);
        });
    });
}

window.closeHistory = function() {
    document.getElementById("historyModal").style.display = "none";
}

window.restoreHistory = function(id) {

    if (!confirm("این تغییر بازگردانی شود؟")) return;

    fetch(`/admin/history/restore/${id}`, {
        method: "POST"
    })
    .then(res => res.json())
    .then(() => {
        alert("بازگردانی انجام شد");
        location.reload();
    });
}

