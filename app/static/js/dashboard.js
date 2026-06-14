document.addEventListener("DOMContentLoaded", () => {

  const stats = JSON.parse(localStorage.getItem("dashboardStats"));
  if (!stats) return;

  setText("dash-total-forms", stats.total_forms);
  setText("dash-active-forms", stats.active_forms);
  setText("dash-finalized-forms", stats.finalized_forms);
  setText("dash-draft-forms", stats.draft_forms);
  setText("dash-total-votes", stats.total_votes);

  // ✅ بعد از اعمال، پاکش می‌کنیم
  localStorage.removeItem("dashboardStats");
});

function setText(id, value) {
  const el = document.getElementById(id);
  if (el && value !== undefined) {
    el.textContent = value;
  }
}
