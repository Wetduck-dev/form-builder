document.addEventListener("DOMContentLoaded", function () {

    // Drag & Drop گزینه‌ها
    document.querySelectorAll(".options-list").forEach(list => {

        const questionId = list.dataset.questionId;

        new Sortable(list, {
            animation: 150,
            onEnd: function () {

                const ids = [...list.querySelectorAll(".option-item")]
                    .map(el => el.dataset.optionId);

                fetch(`/admin/reorder_options/${questionId}`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ order: ids })
                });

            }
        });

    });

    // حذف گزینه
    document.querySelectorAll(".delete-option").forEach(btn => {

        btn.addEventListener("click", function () {

            const id = this.dataset.id;

            if (!confirm("این گزینه حذف شود؟")) return;

            fetch(`/admin/delete_option/${id}`, {
                method: "POST"
            })
            .then(res => res.json())
            .then(() => location.reload());

        });

    });


    // حذف صفحه
    document.querySelectorAll(".delete-page").forEach(btn => {


        btn.addEventListener("click", function () {


            const pageId = this.dataset.pageId;


            if (!confirm("آیا از حذف این صفحه مطمئن هستید؟")) return;


            fetch(`/admin/delete_page/${pageId}`, {

                method: "POST"

            })
            
            .then(res => res.json())
            .then(data => {

                if (data.status === "ok") {

                    // حذف صفحه از DOM
                    const el = document.querySelector(`#page-${pageId}`);

                    if (el) el.remove();

                }

                // اگر خودت بخوای می‌تونی رفرش کنی:
                // location.reload();
            })
            
            .catch(err => console.error("Error deleting page:", err));

        });

    });


    // حذف سوال
    document.querySelectorAll(".delete-question").forEach(btn => {

        btn.addEventListener("click", function () {

            const id = this.dataset.id;

            if (!confirm("این سوال حذف شود؟")) return;

            fetch(`/admin/delete_question/${id}`, {
                method: "POST"
            })
            .then(res => res.json())
            .then(() => location.reload());

        });

    });

});
