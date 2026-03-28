// User profile skills UI (variant 2)
(function () {
  document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("skills-container");
    if (!container) return;

    const userId = container.dataset.userId;
    const addBtn = document.getElementById("add-skill-btn");
    const inputWrapper = document.getElementById("skill-input-wrapper");
    const input = document.getElementById("skill-input");
    const suggestions = document.getElementById("skill-suggestions");

    if (!userId || !addBtn || !inputWrapper || !input || !suggestions) return;

    addBtn.addEventListener("click", () => {
      addBtn.classList.add("hidden");
      inputWrapper.classList.remove("hidden");
      input.value = "";
      suggestions.innerHTML = "";
      suggestions.classList.add("hidden");
      input.focus();
    });

    let t = null;
    input.addEventListener("input", () => {
      const q = input.value.trim();
      clearTimeout(t);
      if (!q) {
        suggestions.classList.add("hidden");
        suggestions.innerHTML = "";
        return;
      }
      t = setTimeout(async () => {
        const res = await fetch(`/users/skills/?q=${encodeURIComponent(q)}`);
        if (!res.ok) return;
        const data = await res.json();

        suggestions.innerHTML = "";
        data.forEach((s) => {
          const li = document.createElement("li");
          li.textContent = s.name;
          li.dataset.id = s.id;
          li.className = "suggestion-item";
          suggestions.appendChild(li);
        });

        const exact = data.some((s) => s.name.toLowerCase() === q.toLowerCase());
        if (!exact) {
          const liNew = document.createElement("li");
          liNew.textContent = `Создать «${q}»`;
          liNew.dataset.name = q;
          liNew.className = "create-new";
          suggestions.appendChild(liNew);
        }

        suggestions.classList.remove("hidden");
      }, 200);
    });

    suggestions.addEventListener("mousedown", async (e) => {
      const li = e.target.closest("li");
      if (!li) return;

      if (li.classList.contains("create-new")) {
        await addSkillByName(li.dataset.name);
      } else if (li.dataset.id) {
        await addSkillById(li.dataset.id, li.textContent.trim());
      }
      hideInput();
    });

    input.addEventListener("keydown", async (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const q = input.value.trim();
        if (!q) return;

        const first = suggestions.querySelector("li");
        if (first && first.dataset.id) {
          await addSkillById(first.dataset.id, first.textContent.trim());
        } else {
          await addSkillByName(q);
        }
        hideInput();
      }
      if (e.key === "Escape") {
        hideInput();
      }
    });

    input.addEventListener("blur", () => setTimeout(hideInput, 120));

    function hideInput() {
      inputWrapper.classList.add("hidden");
      suggestions.classList.add("hidden");
      addBtn.classList.remove("hidden");
    }

    container.addEventListener("click", async (e) => {
      if (e.target.classList.contains("remove-skill-btn")) {
        const chip = e.target.closest(".skill-chip");
        const skillId = chip.dataset.id;
        const res = await fetch(`/users/${userId}/skills/${skillId}/remove/`, {
          method: "POST",
          headers: { "X-CSRFToken": getCookie("csrftoken") },
        });
        if (res.ok) {
          chip.remove();
        }
      }
    });

    async function addSkillById(skillId, skillName) {
      const res = await fetch(`/users/${userId}/skills/add/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ skill_id: skillId }),
      });
      if (!res.ok) return;
      const data = await res.json();
      if (data.added) {
        appendChip(data.skill_id, skillName);
      }
    }

    async function addSkillByName(name) {
      const res = await fetch(`/users/${userId}/skills/add/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ name }),
      });
      if (!res.ok) return;
      const data = await res.json();
      if (data.added) {
        appendChip(data.skill_id, name);
      }
    }

    function appendChip(id, name) {
      if (container.querySelector(`.skill-chip[data-id="${id}"]`)) return;

      const chip = document.createElement("span");
      chip.className = "skill-chip";
      chip.dataset.id = id;
      chip.innerHTML = `${name} <button type="button" class="remove-skill-btn" aria-label="Удалить" title="Удалить">×</button>`;

      container.insertBefore(chip, addBtn);

      const empty = container.querySelector(".skill-empty");
      if (empty) empty.remove();
    }

    function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
          cookie = cookie.trim();
          if (cookie.startsWith(name + "=")) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
  });
})();
