document.addEventListener("DOMContentLoaded", () => {

  // ✅ فعال / غیرفعال کردن فرم
  document.querySelectorAll(".toggle-form-status").forEach(btn => {
    btn.addEventListener("click", async () => {

      const formId = btn.dataset.formId;
      const action = btn.dataset.action;
      const card = document.getElementById("form-card-" + formId);

      try {

        const res = await fetch(`/admin/form/${formId}/${action}`, {
          headers: {
            "X-Requested-With": "XMLHttpRequest"
          }
        });

        const data = await res.json();
        if (!data.success) throw new Error();

        const isDeactivating = action === "deactivate";

        btn.dataset.action = isDeactivating ? "activate" : "deactivate";
        btn.textContent = isDeactivating ? "فعال کردن" : "غیرفعال کردن";

        if (isDeactivating) {
          btn.classList.remove("danger");
        } else {
          btn.classList.add("danger");
        }

        // ✅ آپدیت state کارت و شمارنده فرم‌های فعال
        if (card) {
          card.dataset.isActive = isDeactivating ? "false" : "true";
        }

        const activeEl = document.getElementById("active-forms-count");
        if (activeEl) {
          let val = parseInt(activeEl.textContent);
          activeEl.textContent = isDeactivating ? val - 1 : val + 1;
        }

        // ✅ ذخیره آمار فعلی در localStorage برای به‌روزرسانی داشبورد
        const totalEl = document.getElementById("total-forms-count");
        localStorage.setItem("dashboardStats", JSON.stringify({
          total_forms: totalEl ? parseInt(totalEl.textContent) : null,
          active_forms: activeEl ? parseInt(activeEl.textContent) : null,
          finalized_forms: null,
          draft_forms: null,
          total_votes: null
        }));

        showToast(data.message || "وضعیت فرم تغییر کرد");

      } catch {
        showToast("خطا در تغییر وضعیت فرم", true);
      }

    });
  });

  // ✅ کپی لینک
  document.querySelectorAll(".copy-link-btn").forEach(btn => {
    btn.addEventListener("click", async () => {

      const token = btn.dataset.token;
      const url = window.location.origin + "/vote/" + token;

      try {
        await navigator.clipboard.writeText(url);
        showToast("لینک کپی شد");
      } catch {
        showToast("خطا در کپی لینک", true);
      }

    });
  });

  // ✅ حذف افراد
  document.querySelectorAll(".delete-voters-btn").forEach(btn => {
    btn.addEventListener("click", async () => {

      if (!confirm("لیست افراد پاک شود؟")) return;

      try {

        const res = await fetch(btn.dataset.url, {
          headers: {
            "X-Requested-With": "XMLHttpRequest"
          }
        });

        const data = await res.json();
        if (!data.success) throw new Error();

        showToast(data.message || "افراد حذف شدند");

      } catch {
        showToast("خطا در حذف افراد", true);
      }

    });
  });

  // ✅ حذف فرم (با انیمیشن فید و آپدیت آمار)
  document.querySelectorAll(".delete-form-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      if (!confirm("فرم حذف شود؟")) return;

      const formId = btn.dataset.formId;
      const card = document.getElementById("form-card-" + formId);
      if (!card) return;

      const isFormActive = card.dataset.isActive === "true";

      try {
        const res = await fetch(btn.dataset.url, {
          headers: { "X-Requested-With": "XMLHttpRequest" }
        });
        const data = await res.json();
        if (!data.success) throw new Error();

        await fadeOutAndRemove(card);

        const totalEl = document.getElementById("total-forms-count");
        const activeEl = document.getElementById("active-forms-count");

        if (totalEl) totalEl.textContent = parseInt(totalEl.textContent) - 1;
        if (activeEl && isFormActive) {
          activeEl.textContent = parseInt(activeEl.textContent) - 1;
        }

        // ✅ ذخیره آمار فعلی در localStorage برای بروزرسانی داشبورد
        localStorage.setItem("dashboardStats", JSON.stringify({
          total_forms: totalEl ? parseInt(totalEl.textContent) : null,
          active_forms: activeEl ? parseInt(activeEl.textContent) : null,
          finalized_forms: null,
          draft_forms: null,
          total_votes: null
        }));

        showToast(data.message || "فرم حذف شد");

      } catch {
        showToast("خطا در حذف فرم", true);
      }
    });
  });

  // ✅ آپلود اکسل
  document.querySelectorAll(".upload-voters-form").forEach(form => {

    const input = form.querySelector(".excel-input");

    input.addEventListener("change", async () => {

      const formData = new FormData(form);

      try {

        const res = await fetch(form.action, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest"
          },
          body: formData
        });

        const data = await res.json();
        if (!data.success) throw new Error();

        showToast(data.message || "افراد اضافه شدند");

      } catch {
        showToast("خطا در آپلود فایل", true);
      }

    });

  });

});

// helpers (بدون تغییر)
function fadeOutAndRemove(el, durationMs = 250) {
  return new Promise(resolve => {
    el.style.willChange = "opacity, transform";
    el.style.transition = `opacity ${durationMs}ms ease, transform ${durationMs}ms ease`;
    el.style.opacity = "1";
    el.style.transform = "translateY(0)";
    void el.offsetHeight;
    el.style.opacity = "0";
    el.style.transform = "translateY(8px)";
    window.setTimeout(() => {
      el.remove();
      resolve();
    }, durationMs);
  });
}

function showToast(message, isError = false) {
  const toast = document.createElement("div");
  toast.textContent = message;
  toast.style.position = "fixed";
  toast.style.bottom = "20px";
  toast.style.right = "20px";
  toast.style.padding = "10px 15px";
  toast.style.borderRadius = "8px";
  toast.style.background = isError
    ? "rgba(255,50,50,0.9)"
    : "rgba(50,200,100,0.9)";
  toast.style.color = "white";
  toast.style.zIndex = "9999";
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2500);
}
