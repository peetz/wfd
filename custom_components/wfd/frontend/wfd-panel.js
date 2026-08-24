/* WFD Home Assistant panel. Business rules remain in WFD services. */

class WfdPanel extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._activeTab = "meals";
    this._busy = new Set();
    this._selectedMeals = new Set();
  }

  set hass(hass) { this._hass = hass; this.render(); }
  connectedCallback() { this.render(); }

  state(id) { return this._hass?.states?.[id]; }
  get meals() { return this.state("sensor.wfd_meal_library")?.attributes?.meals || []; }
  get voters() { return this.state("sensor.wfd_household")?.attributes?.voters || []; }
  get persons() { return this.state("sensor.wfd_household")?.attributes?.available_persons || []; }
  get voting() { return this.state("sensor.wfd_voting")?.attributes || {}; }

  async call(service, data, key = service) {
    this._busy.add(key); this.render();
    try { await this._hass.callService("wfd", service, data); }
    finally { this._busy.delete(key); this.render(); }
  }

  renderMeals() {
    const active = this.meals.filter((meal) => meal.active !== false);
    return `<button data-action="add-meal">Add meal</button>
      <h3>Active Meals</h3><ul>${active.map((meal) => `<li>${meal.name}
      <button data-action="archive" data-id="${meal.id}">Archive</button></li>`).join("") || "<li>No meals</li>"}</ul>`;
  }

  renderHousehold() {
    const active = this.voters.filter((voter) => voter.active !== false);
    const known = new Set(this.voters.map((voter) => voter.id));
    const available = this.persons.filter((person) => !known.has(person.id));
    return `<h3>Active Voters</h3><ul>${active.map((voter) => `<li>${voter.name}
      <button data-action="archive-voter" data-id="${voter.id}">Archive</button></li>`).join("") || "<li>No voters</li>"}</ul>
      <h3>Available People</h3><ul>${available.map((person) => `<li>${person.name}
      <button data-action="add-voter" data-id="${person.id}">Add</button></li>`).join("") || "<li>No people available</li>"}</ul>`;
  }

  renderVoting() {
    const v = this.voting;
    const active = this.meals.filter((meal) => meal.active !== false);
    const voters = this.voters.filter((voter) => voter.active !== false);
    const round = v.round_id ? `<p>Progress: ${v.submitted || 0}/${v.voters || 0} voters</p>
      <label>Voter <select id="voter">${voters.map((x) => `<option value="${x.id}">${x.name}</option>`).join("")}</select></label>
      <div>${active.map((meal) => `<label><input type="checkbox" data-meal="${meal.id}"> ${meal.name}</label>`).join(" ")}</div>
      <button data-action="submit-vote">Submit vote</button>
      <button data-action="close-voting">Close round</button>` : `<label>Meals to select <input id="meals-required" type="number" min="1" value="1"></label>
      <button data-action="start-voting">Start voting</button>`;
    return `<p>Status: ${v.status || "idle"}</p>${round}`;
  }

  render() {
    if (!this._hass) return;
    const body = this._activeTab === "household" ? this.renderHousehold() : this._activeTab === "voting" ? this.renderVoting() : this.renderMeals();
    this.innerHTML = `<ha-card header="What's For Dinner"><div style="padding:16px">
      <nav><button data-tab="meals">Meals</button><button data-tab="household">Household</button><button data-tab="voting">Voting</button></nav>${body}</div></ha-card>`;
    this.querySelectorAll("[data-tab]").forEach((button) => button.addEventListener("click", () => { this._activeTab = button.dataset.tab; this.render(); }));
    this.querySelectorAll("[data-action]").forEach((button) => button.addEventListener("click", () => this.action(button)));
  }

  async action(button) {
    const action = button.dataset.action;
    if (action === "add-meal") { const name = window.prompt("Meal name"); if (name) await this.call("add_meal", { name }); }
    if (action === "archive") await this.call("archive_meal", { meal_id: button.dataset.id }, button.dataset.id);
    if (action === "add-voter") await this.call("add_voter", { person_id: button.dataset.id }, button.dataset.id);
    if (action === "archive-voter") await this.call("archive_voter", { person_id: button.dataset.id }, button.dataset.id);
    if (action === "start-voting") await this.call("start_voting", { meals_required: Number(this.querySelector("#meals-required").value) });
    if (action === "submit-vote") {
      const meal_ids = [...this.querySelectorAll("[data-meal]:checked")].map((input) => input.dataset.meal);
      await this.call("submit_vote", { round_id: this.voting.round_id, user_id: this.querySelector("#voter").value, meal_ids });
    }
    if (action === "close-voting") await this.call("close_voting", { round_id: this.voting.round_id });
  }
}

customElements.define("wfd-panel", WfdPanel);
