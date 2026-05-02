(function () {
  "use strict";

  // ── Utilities ────────────────────────────────────────────────────────────────
  function escHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function escAttr(str) {
    return String(str).replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function relativeTime(iso) {
    const diff = Math.floor((Date.now() - new Date(iso)) / 1000);
    if (diff < 5)    return "just now";
    if (diff < 60)   return diff + "s ago";
    if (diff < 3600) return Math.floor(diff / 60) + "m ago";
    if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
    return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  }

  // ── Toast notifications ───────────────────────────────────────────────────────
  const toastContainer = document.getElementById("toast-container");

  function showToast(message, isError) {
    if (!toastContainer) return;
    const t = document.createElement("div");
    t.className = "toast" + (isError ? " toast-error" : "");
    t.textContent = message;
    toastContainer.appendChild(t);
    setTimeout(() => t.remove(), 3100);
  }

  // ── Status dot + note count ───────────────────────────────────────────────────
  const statusDot = document.getElementById("status-dot");
  const noteCountBadge = document.getElementById("note-count-badge");

  async function checkHealth() {
    try {
      const res = await fetch("/health");
      const data = await res.json();
      if (statusDot) statusDot.classList.toggle("offline", data.status !== "healthy");
      if (noteCountBadge && data.checks) {
        const n = data.checks.note_count;
        noteCountBadge.textContent = n + (n === 1 ? " note" : " notes");
      }
    } catch (_) {
      if (statusDot) statusDot.classList.add("offline");
    }
  }

  checkHealth();
  setInterval(checkHealth, 10000);

  // ── Notes page ────────────────────────────────────────────────────────────────
  const grid = document.getElementById("notes-grid");
  const noteForm = document.getElementById("note-form");
  const editModal = document.getElementById("edit-modal");
  const editForm = document.getElementById("edit-form");
  const cancelEdit = document.getElementById("cancel-edit");

  if (!grid) return; // not on the notes page — stop here

  function buildCard(note) {
    const card = document.createElement("div");
    card.className = "note-card";
    card.dataset.id = note.id;
    const preview = note.content.length > 120
      ? note.content.slice(0, 120) + "…"
      : note.content;
    card.innerHTML = `
      <div class="note-title">${escHtml(note.title)}</div>
      <div class="note-content">${escHtml(preview)}</div>
      <div class="note-date">${relativeTime(note.created_at)}</div>
      <div class="note-actions">
        <button class="btn btn-ghost btn-edit"
          data-id="${note.id}"
          data-title="${escAttr(note.title)}"
          data-content="${escAttr(note.content)}">Edit</button>
        <button class="btn btn-danger btn-delete" data-id="${note.id}">Delete</button>
      </div>`;
    return card;
  }

  function renderNotes(notes) {
    grid.innerHTML = "";
    if (!notes.length) {
      grid.innerHTML = '<p class="empty-state">No notes yet. Add one above.</p>';
      return;
    }
    notes.forEach(n => grid.appendChild(buildCard(n)));
  }

  async function loadNotes() {
    const res = await fetch("/api/notes");
    if (!res.ok) return;
    renderNotes(await res.json());
    await checkHealth();
  }

  noteForm && noteForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("note-title").value.trim();
    const content = document.getElementById("note-content").value.trim();
    if (!title) { showToast("Title is required.", true); return; }

    const res = await fetch("/api/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content }),
    });

    if (res.ok) {
      noteForm.reset();
      showToast("Note saved.");
      await loadNotes();
    } else {
      const data = await res.json().catch(() => ({}));
      showToast(data.error || "Failed to save note.", true);
    }
  });

  grid.addEventListener("click", async (e) => {
    const del  = e.target.closest(".btn-delete");
    const edit = e.target.closest(".btn-edit");

    if (del) {
      if (!confirm("Delete this note?")) return;
      const id = del.dataset.id;
      const res = await fetch(`/api/notes/${id}`, { method: "DELETE" });
      if (res.ok) {
        showToast("Note deleted.");
        await loadNotes();
      } else {
        showToast("Failed to delete note.", true);
      }
    }

    if (edit) {
      document.getElementById("edit-id").value = edit.dataset.id;
      document.getElementById("edit-title").value = edit.dataset.title;
      document.getElementById("edit-content").value = edit.dataset.content;
      editModal.hidden = false;
    }
  });

  editForm && editForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id      = document.getElementById("edit-id").value;
    const title   = document.getElementById("edit-title").value.trim();
    const content = document.getElementById("edit-content").value.trim();
    if (!title) return;

    const res = await fetch(`/api/notes/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content }),
    });

    if (res.ok) {
      editModal.hidden = true;
      showToast("Note updated.");
      await loadNotes();
    } else {
      showToast("Failed to update note.", true);
    }
  });

  cancelEdit && cancelEdit.addEventListener("click", () => { editModal.hidden = true; });
  editModal && editModal.querySelector(".modal-backdrop").addEventListener("click", () => {
    editModal.hidden = true;
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && editModal && !editModal.hidden) editModal.hidden = true;
  });

  loadNotes();
})();
