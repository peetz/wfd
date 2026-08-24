/* WFD Home Assistant panel. Business rules remain in WFD services. */

class WfdPanel extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._activeTab = "voting";
    this._busy = new Set();
    this._selectedMeals = new Set();
    this._selectionOwner = "";
    this._draftMealsRequired = 1;
    this._notice = "";
    this._formInteraction = false;
    this._lastSignature = "";
    this.addEventListener("focusin", (event) => {
      if (["SELECT", "INPUT", "TEXTAREA"].includes(event.target.tagName)) this._formInteraction = true;
    });
    this.addEventListener("focusout", (event) => {
      if (["SELECT", "INPUT", "TEXTAREA"].includes(event.target.tagName)) {
        window.setTimeout(() => {
          const active = this.ownerDocument?.activeElement;
          this._formInteraction = Boolean(active && this.contains(active) && ["SELECT", "INPUT", "TEXTAREA"].includes(active.tagName));
        }, 500);
      }
    });
  }

  set hass(hass) {
    this._hass = hass;
    const active = this.ownerDocument?.activeElement;
    const editing = active && this.contains(active) && ["SELECT", "INPUT", "TEXTAREA"].includes(active.tagName);
    const signature = this.viewSignature();
    if (!this._formInteraction && !editing && signature !== this._lastSignature) this.render();
  }

  viewSignature() {
    const ids = ["sensor.wfd_meal_library", "sensor.wfd_household", "sensor.wfd_voting"];
    return JSON.stringify({
      user: this._hass?.user?.id || "",
      states: ids.map((id) => {
        const state = this.state(id);
        return [id, state?.state || "", state?.last_changed || "", state?.last_updated || ""];
      }),
    });
  }

  connectedCallback() { this.render(); }
  state(id) { return this._hass?.states?.[id]; }
  get meals() { return this.state("sensor.wfd_meal_library")?.attributes?.meals || []; }
  get voters() { return this.state("sensor.wfd_household")?.attributes?.voters || []; }
  get persons() { return this.state("sensor.wfd_household")?.attributes?.available_persons || []; }
  get voting() { return this.state("sensor.wfd_voting")?.attributes || {}; }

  get currentVoter() {
    const user = this._hass?.user;
    if (!user) return null;
    const personState = Object.values(this._hass.states || {}).find((state) => (
      state.entity_id?.startsWith("person.") && state.attributes?.user_id === user.id
    ));
    const personId = personState?.entity_id;
    return this.voters.find((voter) => voter.id === personId) ||
      this.voters.find((voter) => voter.name?.toLowerCase() === user.name?.toLowerCase()) || null;
  }

  get isAdmin() {
    return this._hass?.user?.is_admin === true;
  }

  escape(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[character]));
  }

  storageKey(roundId, voterId) { return `wfd.vote.${roundId}.${voterId}`; }

  storedVote(roundId, voterId) {
    try {
      const value = window.localStorage.getItem(this.storageKey(roundId, voterId));
      return value ? JSON.parse(value) : null;
    } catch (_) {
      return null;
    }
  }

  saveVote(roundId, voterId, mealIds) {
    try {
      window.localStorage.setItem(this.storageKey(roundId, voterId), JSON.stringify(mealIds));
    } catch (_) {
      // The backend remains authoritative if browser storage is unavailable.
    }
  }

  async call(service, data, key = service, successMessage = "") {
    this._busy.add(key);
    this._notice = "";
    this.render();
    let succeeded = false;
    try {
      await this._hass.callService("wfd", service, data);
      this._notice = successMessage;
      succeeded = true;
    } catch (error) {
      this._notice = error?.message || "The action could not be completed.";
    } finally {
      this._busy.delete(key);
      this.render();
    }
    return succeeded;
  }

  syncSelectionOwner(voterId) {
    if (this._selectionOwner === voterId) return;
    this._selectionOwner = voterId || "";
    this._selectedMeals = new Set();
  }

  renderMeals() {
    const active = this.meals.filter((meal) => meal.active !== false);
    const archived = this.meals.filter((meal) => meal.active === false);
    const rows = (items, action) => items.map((meal) => `
      <div class="row"><span>${this.escape(meal.name)}</span>
        <button class="quiet" data-action="${action}" data-id="${this.escape(meal.id)}">${action === "restore" ? "Restore" : "Archive"}</button>
      </div>`).join("") || '<p class="muted">None.</p>';
    return `
      <section class="section"><div class="section-heading"><div><p class="eyebrow">Admin</p><h2>Meal library</h2></div>
        <button class="primary" data-action="add-meal">Add meal</button></div>
        <h3>Active meals</h3><div class="list">${rows(active, "archive")}</div>
      </section>
      <section class="section"><p class="eyebrow">History</p><h2>Archived meals</h2><div class="list">${rows(archived, "restore")}</div></section>`;
  }

  renderHousehold() {
    const active = this.voters.filter((voter) => voter.active !== false);
    const archived = this.voters.filter((voter) => voter.active === false);
    const known = new Set(this.voters.map((voter) => voter.id));
    const available = this.persons.filter((person) => !known.has(person.id));
    const rows = (items, action, label) => items.map((item) => `
      <div class="row"><span>${this.escape(item.name)}</span>
        <button class="quiet" data-action="${action}" data-id="${this.escape(item.id)}">${label}</button>
      </div>`).join("") || '<p class="muted">None.</p>';
    return `
      <section class="section"><p class="eyebrow">Admin</p><h2>Household voters</h2>
        <h3>Active voters</h3><div class="list">${rows(active, "archive-voter", "Archive")}</div>
        <h3>Available people</h3><div class="list">${rows(available, "add-voter", "Add voter")}</div>
      </section>
      <section class="section"><p class="eyebrow">History</p><h2>Archived voters</h2><div class="list">${rows(archived, "restore-voter", "Restore")}</div>
      </section>`;
  }

  renderResults() {
    const selected = new Set(this.voting.selected_meals || []);
    const meals = this.meals.filter((meal) => selected.has(meal.id));
    return `
      <section class="voting-hero"><div><p class="eyebrow">Round complete</p><h2>Tonight's chosen meals</h2>
        <p class="muted">The voting round is closed.</p></div><span class="status status-results">Complete</span></section>
      <section class="section"><div class="chosen-grid">${meals.map((meal) => `<div class="chosen-meal">${this.escape(meal.name)}</div>`).join("") || '<p class="muted">No selected meals were recorded.</p>'}</div></section>`;
  }

  renderVoting() {
    const voting = this.voting;
    if (voting.status === "results_stored") return this.renderResults();
    const activeMeals = this.meals.filter((meal) => meal.active !== false);
    const voter = this.currentVoter;
    const activeRound = Boolean(voting.round_id);
    if (!activeRound) {
      if (!this.isAdmin) {
        return `<section class="voting-hero"><div><p class="eyebrow">Voting</p><h2>No round is open</h2>
          <p class="muted">The WFD administrator will start the next round.</p></div><span class="status">Waiting</span></section>`;
      }
      return `
        <section class="voting-hero"><div><p class="eyebrow">Admin controls</p><h2>Start a voting round</h2>
          <p class="muted">Everyone will choose privately from the active meal list.</p></div><span class="status">Ready</span></section>
        ${this._notice ? `<div class="notice">${this.escape(this._notice)}</div>` : ""}
        <section class="section"><label class="field"><span>Meals each person chooses</span>
          <input id="meals-required" type="number" min="1" max="${activeMeals.length || 1}" step="1" value="${this._draftMealsRequired}">
        </label><button class="primary" data-action="start-voting" ${this._busy.has("start-voting") ? "disabled" : ""}>
          ${this._busy.has("start-voting") ? "Starting..." : "Start voting round"}</button></section>`;
    }
    if (!voter) {
      return `<section class="voting-hero"><div><p class="eyebrow">Voting</p><h2>Person link needed</h2>
        <p class="muted">Your Home Assistant user is not linked to an active WFD Person.</p></div></section>`;
    }
    this.syncSelectionOwner(voter.id);
    const saved = this.storedVote(voting.round_id, voter.id);
    const alreadyVoted = Array.isArray(saved);
    if (alreadyVoted) this._selectedMeals = new Set(saved);
    const required = Number(voting.meals_required || 1);
    const submitted = Number(voting.submitted || 0);
    const voterCount = Number(voting.voters || 0);
    const progress = voterCount ? Math.min(100, Math.round((submitted / voterCount) * 100)) : 0;
    const selectedCards = activeMeals.map((meal) => `
      <label class="meal-option ${this._selectedMeals.has(meal.id) ? "chosen" : ""}">
        <input type="checkbox" data-meal="${this.escape(meal.id)}" ${this._selectedMeals.has(meal.id) ? "checked" : ""} ${alreadyVoted ? "disabled" : ""}>
        <span>${this.escape(meal.name)}</span>
      </label>`).join("");
    return `
      <section class="voting-hero"><div><p class="eyebrow">Voting round</p><h2>Pick the dinner shortlist</h2>
        <p class="muted">Voting as <strong>${this.escape(voter.name)}</strong>. Your choices stay private.</p></div>
        <span class="status status-active">Active</span></section>
      ${this._notice ? `<div class="notice">${this.escape(this._notice)}</div>` : ""}
      <section class="section"><div class="progress-row"><strong>${submitted} of ${voterCount} voters submitted</strong><span>${progress}%</span></div>
        <div class="progress-track"><div style="width:${progress}%"></div></div>
        ${alreadyVoted ? '<div class="already-voted"><strong>Already voted</strong><span>Your submitted choices are shown below.</span></div>' : `<div class="meal-prompt"><strong>Choose exactly ${required} meals</strong><span>One submission only.</span></div>`}
        <div class="meal-grid">${selectedCards}</div>
        ${alreadyVoted ? "" : `<button class="primary" data-action="submit-vote" ${this._busy.has("submit-vote") ? "disabled" : ""}>${this._busy.has("submit-vote") ? "Submitting..." : "Submit private vote"}</button>`}
      </section>
      ${this.isAdmin ? `<section class="section"><button class="quiet" data-action="close-voting" ${this._busy.has("close-voting") ? "disabled" : ""}>${this._busy.has("close-voting") ? "Closing..." : "Close round"}</button></section>` : ""}`;
  }

  render() {
    if (!this._hass) return;
    this._lastSignature = this.viewSignature();
    if (!this.isAdmin && this._activeTab !== "voting") this._activeTab = "voting";
    const tabs = this.isAdmin ? ["meals", "household", "voting"] : ["voting"];
    const body = this._activeTab === "meals" && this.isAdmin ? this.renderMeals() :
      this._activeTab === "household" && this.isAdmin ? this.renderHousehold() : this.renderVoting();
    this.innerHTML = `
      <style>
        :host { display:block; --ink:#20302b; --muted:#6c7b75; --line:#dbe4df; --mint:#dff1e7; --accent:#19724d; --warm:#f8f5ed; }
        ha-card { color:var(--ink); background:linear-gradient(135deg,#fff 0%,#f7fbf8 100%); }
        .shell { padding:24px; max-width:900px; font-family:ui-sans-serif,system-ui,sans-serif; }
        nav { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:24px; } nav button { border:0; border-radius:999px; padding:9px 15px; background:#edf1ee; color:var(--ink); cursor:pointer; }
        nav button.active { background:var(--ink); color:white; } h2 { margin:4px 0 8px; font-size:26px; letter-spacing:-.03em; } h3 { margin:22px 0 8px; font-size:15px; } p { margin:0; }
        .eyebrow { color:var(--accent); font-size:12px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; } .muted { color:var(--muted); line-height:1.5; }
        .section { padding:20px 0; border-top:1px solid var(--line); } .section-heading,.voting-hero,.progress-row,.row { display:flex; align-items:center; justify-content:space-between; gap:16px; }
        .list { display:grid; gap:8px; margin-top:10px; } .row { border:1px solid var(--line); border-radius:12px; padding:13px 15px; background:#fff; }
        button { font:inherit; border:0; cursor:pointer; } button:disabled { opacity:.55; cursor:wait; } .primary { background:var(--accent); color:#fff; border-radius:10px; padding:11px 16px; font-weight:700; }
        .quiet { background:transparent; color:var(--accent); padding:9px 10px; border-radius:8px; } .quiet:hover { background:var(--mint); }
        .voting-hero { padding:20px; border-radius:16px; background:var(--warm); margin-bottom:16px; } .status { border-radius:999px; padding:7px 11px; background:#e8ece9; font-size:12px; font-weight:700; text-transform:capitalize; }
        .status-active { background:var(--mint); color:var(--accent); } .status-results { background:var(--mint); color:var(--accent); } .notice,.already-voted { margin:12px 0; padding:12px 14px; border-radius:10px; background:#fff5d9; display:grid; gap:3px; }
        .field { display:grid; gap:7px; max-width:320px; margin:0 0 18px; } .field span { font-size:13px; font-weight:700; } input { box-sizing:border-box; width:100%; border:1px solid #bccbc2; border-radius:9px; padding:11px 12px; background:white; color:var(--ink); font:inherit; }
        .progress-track { height:8px; border-radius:99px; overflow:hidden; background:#e7ede9; margin:10px 0 22px; } .progress-track div { height:100%; background:var(--accent); border-radius:inherit; transition:width .25s ease; }
        .meal-prompt { display:flex; justify-content:space-between; gap:16px; margin:0 0 12px; } .meal-prompt span,.already-voted span { color:var(--muted); font-size:13px; }
        .meal-grid,.chosen-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:10px; margin-bottom:20px; }
        .meal-option,.chosen-meal { display:flex; align-items:flex-start; gap:10px; min-height:44px; padding:12px; border:1px solid var(--line); border-radius:10px; background:#fff; }
        .meal-option.chosen,.chosen-meal { border-color:var(--accent); background:var(--mint); } .meal-option input { width:auto; margin-top:3px; }
        @media (max-width:600px) { .shell { padding:16px; } .voting-hero,.section-heading,.meal-prompt { align-items:flex-start; flex-direction:column; } }
      </style>
      <ha-card header="What's For Dinner"><div class="shell"><nav>${tabs.map((tab) => `<button class="${this._activeTab === tab ? "active" : ""}" data-tab="${tab}">${tab[0].toUpperCase() + tab.slice(1)}</button>`).join("")}</nav>${body}</div></ha-card>`;
    this.bindActions();
  }

  bindActions() {
    this.querySelectorAll("[data-tab]").forEach((button) => button.addEventListener("click", () => { this._activeTab = button.dataset.tab; this.render(); }));
    this.querySelectorAll("[data-action]").forEach((button) => button.addEventListener("click", () => this.action(button)));
    this.querySelector("#meals-required")?.addEventListener("input", (event) => { this._draftMealsRequired = Math.max(1, Number(event.target.value) || 1); event.target.value = this._draftMealsRequired; });
    this.querySelectorAll("[data-meal]").forEach((input) => input.addEventListener("change", (event) => { if (event.target.checked) this._selectedMeals.add(event.target.dataset.meal); else this._selectedMeals.delete(event.target.dataset.meal); }));
  }

  async action(button) {
    const action = button.dataset.action;
    if (action === "add-meal") { const name = window.prompt("Meal name"); if (name) await this.call("add_meal", { name }, "add-meal", "Meal added."); }
    if (action === "archive") await this.call("archive_meal", { meal_id: button.dataset.id }, button.dataset.id, "Meal archived.");
    if (action === "restore") await this.call("restore_meal", { meal_id: button.dataset.id }, button.dataset.id, "Meal restored.");
    if (action === "add-voter") await this.call("add_voter", { person_id: button.dataset.id }, button.dataset.id, "Voter added.");
    if (action === "archive-voter") await this.call("archive_voter", { person_id: button.dataset.id }, button.dataset.id, "Voter archived.");
    if (action === "restore-voter") await this.call("restore_voter", { person_id: button.dataset.id }, button.dataset.id, "Voter restored.");
    if (action === "start-voting") await this.call("start_voting", { meals_required: this._draftMealsRequired }, "start-voting", "Voting round started.");
    if (action === "submit-vote") {
      const required = Number(this.voting.meals_required || 1);
      if (this._selectedMeals.size !== required) { this._notice = `Choose exactly ${required} meals before submitting.`; this.render(); return; }
      const ok = await this.call("submit_vote", { round_id: this.voting.round_id, meal_ids: [...this._selectedMeals] }, "submit-vote", "Private vote submitted.");
      if (ok && this.currentVoter) this.saveVote(this.voting.round_id, this.currentVoter.id, [...this._selectedMeals]);
    }
    if (action === "close-voting") await this.call("close_voting", { round_id: this.voting.round_id }, "close-voting", "Round closed.");
  }
}

customElements.define("wfd-panel", WfdPanel);
