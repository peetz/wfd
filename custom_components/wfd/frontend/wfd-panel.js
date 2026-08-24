/*
 * What's For Dinner frontend panel.
 */

class WfdPanel extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  connectedCallback() {
    this._busy = new Set();
    this.render();
  }

  get meals() {
    return this._hass?.states?.["sensor.wfd_meal_library"]?.attributes?.meals || [];
  }

  get voters() {
    return this._hass?.states?.["sensor.wfd_household"]?.attributes?.voters || [];
  }

  get householdPersons() {
    return this._hass?.states?.["sensor.wfd_household"]?.attributes?.available_persons || [];
  }

  async call(action, data, key) {
    this._busy.add(key);
    this.render();
    try {
      await this._hass.callService("wfd", action, data);
    } finally {
      this._busy.delete(key);
      this.render();
    }
  }

  async addMeal() {
    const name = window.prompt("Meal name");
    if (name) await this.call("add_meal", { name }, "add-meal");
  }

  async renameMeal(meal) {
    const name = window.prompt("Rename meal", meal.name);
    if (name && name !== meal.name) await this.call("rename_meal", { meal_id: meal.id, name }, meal.id);
  }

  async archiveMeal(meal) { await this.call("archive_meal", { meal_id: meal.id }, meal.id); }
  async restoreMeal(meal) { await this.call("restore_meal", { meal_id: meal.id }, meal.id); }
  async addVoter(person) { await this.call("add_voter", { person_id: person.id }, person.id); }
  async archiveVoter(voter) { await this.call("archive_voter", { person_id: voter.id }, voter.id); }
  async restoreVoter(voter) { await this.call("restore_voter", { person_id: voter.id }, voter.id); }

  renderMeals() {
    const active = this.meals.filter((m) => m.active !== false);
    const archived = this.meals.filter((m) => m.active === false);
    const rows = (items, actions) => items.map((m) => `<li>${m.name} ${actions.map((a) => `<button ${this._busy.has(m.id) ? "disabled" : ""} data-action="${a}" data-id="${m.id}">${a}</button>`).join("")}</li>`).join("");
    return `<ha-button id="add" raised>Add meal</ha-button><h3>Active Meals</h3><ul>${rows(active,["rename","archive"])}</ul><h3>Archived Meals</h3><ul>${rows(archived,["restore"])}</ul>`;
  }

  renderHousehold() {
    const active = this.voters.filter((v) => v.active !== false);
    const archived = this.voters.filter((v) => v.active === false);
    const ids = new Set(this.voters.map((v) => v.id));
    const available = this.householdPersons.filter((p) => !ids.has(p.id));
    const rows = (items, action) => items.map((i) => `<li>${i.name}<button ${this._busy.has(i.id) ? "disabled" : ""} data-action="${action}" data-id="${i.id}">${action}</button></li>`).join("");
    return `<h3>Active Voters</h3><ul>${rows(active,"archive-voter")}</ul><h3>Available People</h3><ul>${rows(available,"add-voter")}</ul><h3>Archived Voters</h3><ul>${rows(archived,"restore-voter")}</ul>`;
  }

  bindActions() {
    this.querySelector("#add")?.addEventListener("click", () => this.addMeal());
    this.querySelectorAll("button[data-action]").forEach((b) => b.addEventListener("click", async () => {
      const id=b.dataset.id; const a=b.dataset.action;
      const meal=this.meals.find((x)=>x.id===id); const voter=this.voters.find((x)=>x.id===id); const person=this.householdPersons.find((x)=>x.id===id);
      if(a==="rename"&&meal) await this.renameMeal(meal);
      if(a==="archive"&&meal) await this.archiveMeal(meal);
      if(a==="restore"&&meal) await this.restoreMeal(meal);
      if(a==="add-voter"&&person) await this.addVoter(person);
      if(a==="archive-voter"&&voter) await this.archiveVoter(voter);
      if(a==="restore-voter"&&voter) await this.restoreVoter(voter);
    }));
  }

  render() {
    if (!this._hass) return;
    const tab=this._activeTab||"meals";
    this.innerHTML=`<ha-card header="What's For Dinner"><div style="padding:16px"><div><button data-tab="meals">Meals</button><button data-tab="household">Voters / Household</button></div>${tab==="meals"?this.renderMeals():this.renderHousehold()}</div></ha-card>`;
    this.querySelectorAll("button[data-tab]").forEach((b)=>b.addEventListener("click",()=>{this._activeTab=b.dataset.tab;this.render();}));
    this.bindActions();
  }
}
customElements.define("wfd-panel", WfdPanel);
