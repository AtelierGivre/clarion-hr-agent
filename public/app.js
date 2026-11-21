const els = {
  thread: document.getElementById("thread"),
  empty: document.getElementById("empty"),
  suggestions: document.getElementById("suggestions"),
  form: document.getElementById("ask"),
  input: document.getElementById("question"),
  send: document.getElementById("send"),
  employee: document.getElementById("employee"),
  reset: document.getElementById("reset"),
  status: document.getElementById("status"),
  statusText: document.getElementById("status-text"),
  chatCard: document.querySelector(".chat-card"),
};

const state = {
  employeeId: "E102",
  busy: false,
};

const ROUTE_LABEL = {
  policy: "Policy library",
  employee: "Your records",
  "policy+employee": "Policy and records",
  blocked: "Blocked",
  error: "Error",
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function answerHtml(text) {
  return escapeHtml(text).replace(/\[(\d{1,2})\]/g, '<span class="cite">$1</span>');
}

function statusClass(status) {
  const map = {
    pass: "pass",
    blocked: "blocked",
    redacted: "redacted",
    cited: "cited",
  };
  return map[status] || "idle";
}

function scrollToEnd() {
  requestAnimationFrame(() => {
    els.thread.scrollTop = els.thread.scrollHeight;
  });
}

function reveal(node) {
  requestAnimationFrame(() => {
    node.scrollIntoView({ block: "nearest", behavior: "smooth" });
  });
}

function focusInput() {
  try {
    els.input.focus({ preventScroll: true });
  } catch {
    els.input.focus();
  }
}

function hideEmpty() {
  if (els.empty) els.empty.style.display = "none";
}

function showEmpty() {
  if (els.empty) els.empty.style.display = "";
}

function setBusy(busy) {
  state.busy = busy;
  els.send.disabled = busy;
  els.input.disabled = busy;
  els.thread.setAttribute("aria-busy", String(busy));
}

function addUserMessage(text) {
  hideEmpty();
  els.chatCard.classList.add("has-messages");
  const node = document.createElement("div");
  node.className = "msg user";
  node.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
  els.thread.appendChild(node);
  scrollToEnd();
  reveal(node);
}

function addTyping() {
  const node = document.createElement("div");
  node.className = "msg agent";
  node.id = "typing";
  node.innerHTML = `
    <div class="bubble">
      <div class="who"><span class="avatar">C</span><strong>Clarion</strong><span class="sep">·</span><span>Reading policy and records</span></div>
      <div class="typing" aria-label="Thinking"><i></i><i></i><i></i></div>
    </div>`;
  els.thread.appendChild(node);
  scrollToEnd();
  return node;
}

function sourcesHtml(sources) {
  if (!sources.length) return "";
  const items = sources
    .map(
      (source) => `
      <li>
        <span class="src-num">${source.n}</span>
        <div class="src-main">
          <strong>${escapeHtml(source.title)}</strong>
          <span>${escapeHtml(source.section)}</span>
          <p>${escapeHtml(source.snippet)}</p>
        </div>
        <span class="src-score">${Math.round(source.score * 100)}%</span>
      </li>`
    )
    .join("");
  const label = sources.length === 1 ? "1 source" : `${sources.length} sources`;
  return `
    <details class="sources">
      <summary>${label}</summary>
      <ul class="source-list">${items}</ul>
    </details>`;
}

function toolsHtml(tools) {
  if (!tools.length) return "";
  const rows = tools
    .map((tool) => {
      const mark = tool.status === "ok" ? '<span class="ok">ok</span>' : '<span class="no">denied</span>';
      return `<div class="tool-row"><span>MCP</span><code>${escapeHtml(tool.name)}("${escapeHtml(tool.employee_id)}")</code><span>${mark}</span></div>`;
    })
    .join("");
  return `<div class="tools">${rows}</div>`;
}

function checksHtml(checks) {
  if (!checks.length) return "";
  const chips = checks
    .map(
      (check) =>
        `<span class="chip ${statusClass(check.status)}"><span class="dot"></span>${escapeHtml(check.name)}: ${escapeHtml(check.status)}</span>`
    )
    .join("");
  return `<div class="chips">${chips}</div>`;
}

function addAgentMessage(result) {
  const node = document.createElement("div");
  node.className = "msg agent";
  if (result.blocked) node.classList.add("blocked");
  if (result.route === "error") node.classList.add("error");

  const route = ROUTE_LABEL[result.route] || result.route;
  const seconds = (result.latency_ms / 1000).toFixed(1);
  const sources = result.sources || [];
  const tools = result.tool_calls || [];
  const checks = result.checks || [];

  node.innerHTML = `
    <div class="bubble">
      <div class="who">
        <span class="avatar">C</span><strong>Clarion</strong>
        <span class="sep">·</span><span>${escapeHtml(route)}</span>
        <span class="sep">·</span><span>${seconds}s</span>
      </div>
      <div class="answer">${answerHtml(result.answer || "")}</div>
      <div class="meta">
        ${checksHtml(checks)}
        ${toolsHtml(tools)}
        ${sourcesHtml(sources)}
      </div>
    </div>`;
  els.thread.appendChild(node);
  scrollToEnd();
  reveal(node);
}

function addErrorMessage(detail) {
  const node = document.createElement("div");
  node.className = "msg agent error";
  node.innerHTML = `
    <div class="bubble">
      <div class="who"><span class="avatar">C</span><strong>Clarion</strong><span class="sep">·</span><span>Offline</span></div>
      <div class="answer">I could not reach the agent just now. Please try again in a moment.</div>
      <div class="meta"><div class="chips"><span class="chip blocked"><span class="dot"></span>${escapeHtml(detail)}</span></div></div>
    </div>`;
  els.thread.appendChild(node);
  scrollToEnd();
}

async function ask(question) {
  if (state.busy) return;
  const text = question.trim();
  if (!text) return;

  setBusy(true);
  addUserMessage(text);
  els.input.value = "";
  const typing = addTyping();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, employee_id: state.employeeId }),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || `HTTP ${response.status}`);
    }
    const result = await response.json();
    typing.remove();
    addAgentMessage(result);
  } catch (error) {
    typing.remove();
    addErrorMessage(error.message || "Request failed");
  } finally {
    setBusy(false);
    focusInput();
  }
}

async function loadEmployees() {
  const response = await fetch("/api/employees");
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();
  els.employee.innerHTML = data.employees
    .map(
      (employee) =>
        `<option value="${escapeHtml(employee.employee_id)}">${escapeHtml(employee.employee_id)} · ${escapeHtml(employee.name)}</option>`
    )
    .join("");
  els.employee.value = state.employeeId;
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    const ok = response.ok && data.status === "ok";
    els.status.classList.toggle("ok", ok);
    els.status.classList.toggle("down", !ok);
    els.statusText.textContent = ok ? "Live" : "Database offline";
  } catch {
    els.status.classList.add("down");
    els.statusText.textContent = "Offline";
  }
}

els.form.addEventListener("submit", (event) => {
  event.preventDefault();
  ask(els.input.value);
});

els.suggestions.addEventListener("click", (event) => {
  const button = event.target.closest(".suggestion");
  if (button) ask(button.dataset.q);
});

els.employee.addEventListener("change", () => {
  state.employeeId = els.employee.value;
  els.input.placeholder = `Ask as ${state.employeeId}`;
  els.input.focus();
});

els.reset.addEventListener("click", () => {
  if (state.busy) return;
  [...els.thread.children].forEach((child) => {
    if (child !== els.empty) child.remove();
  });
  showEmpty();
  els.chatCard.classList.remove("has-messages");
  els.input.focus();
});

checkHealth();
loadEmployees().catch(() => {});
if (window.matchMedia("(min-width: 941px)").matches) focusInput();
