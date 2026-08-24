/* WFD Home Assistant panel. Business rules remain in WFD services. */

class WfdPanel extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._activeTab = "meals";
    this._busy = new Set();
    this._selectedMeals = new Set();
    this._draftMealsRequired = 1;
    this._draftVoterId = "";
    this._notice = "";
    this._formInteraction = false;
    this.addEventListener("focusin", (event) => {
      if (["SELECT", "INPUT", "TEXTAREA"].includes(event.target.tagName)) {
        this._formInteraction = true;
      }
    });
    this.addEventListener("focusout", (event) => {
      if (["SELECT", "INPUT", "TEXTAREA"].includes(event.target.tagName)) {
        window.setTimeout(() => {
          const active = this.ownerDocument?.activeElement;
          this._formInteraction = Boolean(
            active && this.contains(active) &&
            ["SELECT", "INPUT", "TEXTAREA"].includes(active.tagName)
          );
        }, 500);
      }
    });
  }

  set hass(hass) {
    this._hass = hass;
    const active = this.ownerDocument?.activeElement;
    const editing = active && this.contains(active) &&
      ["SELECT", "INPUT", "TEXTAREA"].includes(active.tagName);
    if (!this._formInteraction && !editing) this.render();
  }

  connectedCallback() {
    this.render();
  }

  state(id) { return this._hass?.states?.[id]; }
  get meals() { return this.state("sensor.wfd_meal_library")?.attributes?.meals || []; }
  get voters() { return this.state("sensor.wfd_household")?.attributes?.voters || []; }
  get persons() { return this.state("sensor.wfd_household")?.attributes?.available_persons || []; }
  get voting() { return this.state("sensor.wfd_voting")?.attributes || {}; }

  escape(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[character]));
  }

  async call(service, data, key = service, successMessage = "") {
    this._busy.add(key);
    this._notice = "";
    this.render();
    try {
      await this._hass.callService("wfd", service, data);
      this._notice = successMessage;
    } catch (error) {
      this._notice = error?.message || "The action could not be completed.";
    } finally {
      this._busy.delete(key);
      this.render();
    }
  }

  renderMeals() {
    const active = this.meals.filter((meal) => meal.active !== false);
    return `
      <section class="section">
        <div class="section-heading"><div><p class="eyebrow">Meal library</p><h2>Tonight starts here</h2></div>
          <button class="primary" data-action="add-meal">Add meal</button></div>
        <div class="list">${active.map((meal) => `
          <div class="row"><span>${this.escape(meal.name)}</span>
            <button class="quiet" data-action="archive" data-id="${this.escape(meal.id)}">Archive</button>
          </div>`).join("") || "<p class=\"muted\">No active meals yet.</p>"}</div>
      </section>`;
  }

  renderHousehold() {
    const active = this.voters.filter((voter) => voter.active !== false);
    const known = new Set(this.voters.map((voter) => voter.id));
    const available = this.persons.filter((person) => !known.has(person.id));
    return `
      <section class="section"><p class="eyebrow">Household</p><h2>Who gets a say?</h2>
        <div class="list">${active.map((voter) => `
          <div class="row"><span>${this.escape(voter.name)}</span>
            <button class="quiet" data-action="archive-voter" data-id="${this.escape(voter.id)}">Archive</button></div>`).join("") || "<p class=\"muted\">No active voters.</p>"}</div>
      </section>
      <section class="section"><p class="eyebrow">Available people</p><div class="list">${available.map((person) => `
        <div class="row"><span>${this.escape(person.name)}</span>
          <button class="quiet" data-action="add-voter" data-id="${this.escape(person.id)}">Add voter</button></div>`).join("") || "<p class=\"muted\">Everyone is already a voter.</p>"}</div>
      </section>`;
  }

  renderVoting() {
    const voting = this.voting;
    const activeMeals = this.meals.filter((meal) => meal.active !== false);
    const voters = this.voters.filter((voter) => voter.active !== false);
    const busyStart = this._busy.has("start-voting");
    const busySubmit = this._busy.has("submit-vote");
    const busyClose = this._busy.has("close-voting");
    const activeRound = Boolean(voting.round_id);
    const submitted = Number(voting.submitted || 0);
    const voterCount = Number(voting.voters || 0);
    const progress = voterCount ? Math.min(100, Math.round((submitted / voterCount) * 100)) : 0;
    const required = Number(voting.meals_required || this._draftMealsRequired || 1);

    if (!this._draftVoterId && voters[0]) this._draftVoterId = voters[0].id;

    const setup = `
      <div class="setup-grid">
        <label class="field"><span>Meals to choose</span>
          <input id="meals-required" type="number" min="1" max="${activeMeals.length || 1}" step="1" value="${this._draftMealsRequired}" ${busyStart ? "disabled" : ""}>
        </label>
        <div class="field-help">Each voter picks this many different meals.</div>
      </div>
      <button class="primary" data-action="start-voting" ${busyStart ? "disabled" : ""}>
        ${busyStart ? "Starting round..." : "Start voting round"}
      </button>`;

    const votingForm = `
      <div class="progress-row"><div><strong>${submitted} of ${voterCount}</strong> voters submitted</div><span>${progress}%</span></div>
      <div class="progress-track"><div style="width:${progress}%"></div></div>
      <label class="field"><span>Voting as</span>
        <select id="voter">${voters.map((voter) => `<option value="${this.escape(voter.id)}" ${voter.id === this._draftVoterId ? "selected" : ""}>${this.escape(voter.name)}</option>`).join("")}</select>
      </label>
      <div class="meal-prompt"><strong>Choose exactly ${required} meals</strong><span>Your choices stay private.</span></div>
      <div class="meal-grid">${activeMeals.map((meal) => `
        <label class="meal-option ${this._selectedMeals.has(meal.id) ? "chosen" : ""}">
          <input type="checkbox" data-meal="${this.escape(meal.id)}" ${this._selectedMeals.has(meal.id) ? "checked" : ""}>
          <span>${this.escape(meal.name)}</span>
        </label>`).join("")}</div>
      <div class="actions">
        <button class="primary" data-action="submit-vote" ${busySubmit ? "disabled" : ""}>${busySubmit ? "Submitting..." : "Submit private vote"}</button>
        <button class="quiet" data-action="close-voting" ${busyClose ? "disabled" : ""}>${busyClose ? "Closing..." : "Close round"}</button>
      </div>`;

    return `
      <section class="voting-hero"><div><p class="eyebrow">Voting round</p><h2>Pick the dinner shortlist</h2>
        <p class="muted">Everyone chooses privately. The round closes when all voters have submitted.</p></div>
        <span class="status status-${this.escape(voting.status || "idle")}">${this.escape(voting.status || "idle")}</span>
      </section>
      ${this._notice ? `<div class="notice">${this.escape(this._notice)}</div>` : ""}
      <section class="section">${activeRound ? votingForm : setup}</section>`;
  }

  render() {
    if (!this._hass) return;
    const body = this._activeTab === "household" ? this.renderHousehold() : this._activeTab === "voting" ? this.renderVoting() : this.renderMeals();
    this.innerHTML = `
      <style>
        :host { display:block; --ink:#20302b; --muted:#6c7b75; --line:#dbe4df; --mint:#dff1e7; --accent:#19724d; --warm:#f8f5ed; }
        ha-card { color:var(--ink); background:linear-gradient(135deg,#fff 0%,#f7fbf8 100%); }
        .shell { padding:24px; max-width:900px; font-family:ui-sans-serif,system-ui,sans-serif; }
        nav { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:24px; }
        nav button { border:0; border-radius:999px; padding:9px 15px; background:#edf1ee; color:var(--ink); cursor:pointer; }
        nav button.active { background:var(--ink); color:white; }
        h2 { margin:4px 0 8px; font-size:26px; letter-spacing:-.03em; } p { margin:0; }
        .eyebrow { color:var(--accent); font-size:12px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }
        .muted,.field-help { color:var(--muted); line-height:1.5; } .section { padding:20px 0; border-top:1px solid var(--line); }
        .section-heading,.voting-hero,.progress-row,.actions,.row { display:flex; align-items:center; justify-content:space-between; gap:16px; }
        .list { display:grid; gap:8px; margin-top:16px; } .row { border:1px solid var(--line); border-radius:12px; padding:13px 15px; background:#fff; }
        button { font:inherit; border:0; cursor:pointer; } button:disabled { opacity:.55; cursor:wait; }
        .primary { background:var(--accent); color:#fff; border-radius:10px; padding:11px 16px; font-weight:700; }
        .quiet { background:transparent; color:var(--accent); padding:9px 10px; border-radius:8px; } .quiet:hover { background:var(--mint); }
        .voting-hero { padding:20px; border-radius:16px; background:var(--warm); margin-bottom:16px; }
        .status { border-radius:999px; padding:7px 11px; background:#e8ece9; font-size:12px; font-weight:700; text-transform:capitalize; }
        .status-active { background:var(--mint); color:var(--accent); } .notice { margin:12px 0; padding:12px 14px; border-radius:10px; background:#fff5d9; }
        .setup-grid { display:grid; grid-template-columns:220px 1fr; gap:18px; align-items:end; margin-bottom:18px; }
        .field { display:grid; gap:7px; margin:16px 0; } .field span { font-size:13px; font-weight:700; }
        input,select { box-sizing:border-box; width:100%; border:1px solid #bccbc2; border-radius:9px; padding:11px 12px; background:white; color:var(--ink); font:inherit; }
        .progress-track { height:8px; border-radius:99px; overflow:hidden; background:#e7ede9; margin:10px 0 20px; }
        .progress-track div { height:100%; background:var(--accent); border-radius:inherit; transition:width .25s ease; }
        .meal-prompt { display:flex; justify-content:space-between; gap:16px; margin:22px 0 12px; } .meal-prompt span { color:var(--muted); font-size:13px; }
        .meal-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:10px; }
        .meal-option { display:flex; align-items:flex-start; gap:10px; min-height:44px; padding:12px; border:1px solid var(--line); border-radius:10px; background:#fff; cursor:pointer; }
        .meal-option.chosen { border-color:var(--accent); background:var(--mint); } .meal-option input { width:auto; margin-top:3px; }
        .actions { justify-content:flex-start; margin-top:20px; }
        @media (max-width:600px) { .shell { padding:16px; } .setup-grid { grid-template-columns:1fr; gap:4px; } .voting-hero,.section-heading,.meal-prompt { align-items:flex-start; flex-direction:column; } }
      </style>
      <ha-card header="What's For Dinner"><div class="shell">
        <nav>${["meals", "household", "voting"].map((tab) => `<button class="${this._activeTab === tab ? "active" : ""}" data-tab="${tab}">${tab[0].toUpperCase() + tab.slice(1)}</button>`).join("")}</nav>
        ${body}
      </div></ha-card>`;
    this.bindActions();
  }

  bindActions() {
    this.querySelectorAll("[data-tab]").forEach((button) => button.addEventListener("click", () => {
      this._activeTab = button.dataset.tab;
      this.render();
    }));
    this.querySelectorAll("[data-action]").forEach((button) => button.addEventListener("click", () => this.action(button)));
    this.querySelector("#meals-required")?.addEventListener("input", (event) => {
      const value = Math.max(1, Number(event.target.value) || 1);
      this._draftMealsRequired = value;
      event.target.value = value;
    });
    this.querySelector("#voter")?.addEventListener("change", (event) => {
      this._draftVoterId = event.target.value;
    });
    this.querySelectorAll("[data-meal]").forEach((input) => input.addEventListener("change", (event) => {
      if (event.target.checked) this._selectedMeals.add(event.target.dataset.meal);
      else this._selectedMeals.delete(event.target.dataset.meal);
      event.target.closest(".meal-option")?.classList.toggle("chosen", event.target.checked);
    }));
  }

  async action(button) {
    const action = button.dataset.action;
    if (action === "add-meal") {
      const name = window.prompt("Meal name");
      if (name) await this.call("add_meal", { name }, "add-meal", "Meal added.");
    }
    if (action === "archive") await this.call("archive_meal", { meal_id: button.dataset.id }, button.dataset.id, "Meal archived.");
    if (action === "add-voter") await this.call("add_voter", { person_id: button.dataset.id }, button.dataset.id, "Voter added.");
    if (action === "archive-voter") await this.call("archive_voter", { person_id: button.dataset.id }, button.dataset.id, "Voter archived.");
    if (action === "start-voting") {
      await this.call("start_voting", { meals_required: this._draftMealsRequired }, "start-voting", "Voting round started.");
    }
    if (action === "submit-vote") {
      const required = Number(this.voting.meals_required || this._draftMealsRequired || 1);
      if (this._selectedMeals.size !== required) {
        this._notice = `Choose exactly ${required} meals before submitting.`;
        this.render();
        return;
      }
      await this.call("submit_vote", { round_id: this.voting.round_id, user_id: this._draftVoterId || this.querySelector("#voter").value, meal_ids: [...this._selectedMeals] }, "submit-vote", "Private vote submitted.");
      this._selectedMeals.clear();
    }
    if (action === "close-voting") {
      await this.call("close_voting", { round_id: this.voting.round_id }, "close-voting", "Round closed.");
    }
  }
}

customElements.define("wfd-panel", WfdPanel);
