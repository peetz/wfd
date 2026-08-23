/*
 * What's For Dinner frontend panel.
 */

class WfdPanel extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  connectedCallback() {
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

  async call(action, data) {
    await this._hass.callService("wfd", action, data);
  }

  async addMeal() {
    const name = window.prompt("Meal name");
    if (!name) return;
    await this.call("add_meal", { name });
  }

  async renameMeal(meal) {
    const newName = window.prompt("Rename meal", meal.name);
    if (!newName || newName === meal.name) return;
    await this.call("rename_meal", { meal_id: meal.id, name: newName });
  }

  async archiveMeal(meal) {
    await this.call("archive_meal", { meal_id: meal.id });
  }

  async restoreMeal(meal) {
    await this.call("restore_meal", { meal_id: meal.id });
  }

  async addVoter(person) {
    await this.call("add_voter", { person_id: person.id });
  }

  async archiveVoter(voter) {
    await this.call("archive_voter", { person_id: voter.id });
  }

  async restoreVoter(voter) {
    await this.call("restore_voter", { person_id: voter.id });
  }

  renderMeals() {
    const meals = this.meals;
    const active = meals.filter((meal) => meal.active !== false);
    const archived = meals.filter((meal) => meal.active === false);
    const rows = (items, actions) => items.map((meal) => `
      <li>
        ${meal.name}
        ${actions.map((action) => `<button data-action="${action}" data-id="${meal.id}">${action}</button>`).join("")}
      </li>
    `).join("");

    return `
      <ha-button id="add" raised>Add meal</ha-button>
      <h3>Active Meals</h3>
      ${active.length ? `<ul>${rows(active, ["rename", "archive"])}</ul>` : "<p>No active meals.</p>"}
      <h3>Archived Meals</h3>
      ${archived.length ? `<ul>${rows(archived, ["restore"])}</ul>` : "<p>No archived meals.</p>"}
    `;
  }

  renderHousehold() {
    const voters = this.voters;
    const active = voters.filter((voter) => voter.active !== false);
    const archived = voters.filter((voter) => voter.active === false);
    const activeIds = new Set(voters.map((voter) => voter.id));
    const available = this.householdPersons.filter((person) => !activeIds.has(person.id));

    const rows = (items, action) => items.map((item) => `
      <li>
        ${item.name}
        <button data-action="${action}" data-id="${item.id}">${action}</button>
      </li>
    `).join("");

    return `
      <h3>Active Voters</h3>
      ${active.length ? `<ul>${rows(active, "archive-voter")}</ul>` : "<p>No active voters.</p>"}
      <h3>Available People</h3>
      ${available.length ? `<ul>${rows(available, "add-voter")}</ul>` : "<p>No additional HA Persons available.</p>"}
      <h3>Archived Voters</h3>
      ${archived.length ? `<ul>${rows(archived, "restore-voter")}</ul>` : "<p>No archived voters.</p>"}
    `;
  }

  bindActions() {
    this.querySelector("#add")?.addEventListener("click", () => this.addMeal());
    this.querySelectorAll("button[data-action]").forEach((button) => {
      button.addEventListener("click", async () => {
        const id = button.dataset.id;
        const action = button.dataset.action;
        const meals = this.meals;
        const voters = this.voters;
        const persons = this.householdPersons;
        if (action === "rename") {
          const meal = meals.find((item) => item.id === id);
          if (meal) await this.renameMeal(meal);
        } else if (action === "archive") {
          const meal = meals.find((item) => item.id === id);
          if (meal) await this.archiveMeal(meal);
        } else if (action === "restore") {
          const meal = meals.find((item) => item.id === id);
          if (meal) await this.restoreMeal(meal);
        } else if (action === "add-voter") {
          const person = persons.find((item) => item.id === id);
          if (person) await this.addVoter(person);
        } else if (action === "archive-voter") {
          const voter = voters.find((item) => item.id === id);
          if (voter) await this.archiveVoter(voter);
        } else if (action === "restore-voter") {
          const voter = voters.find((item) => item.id === id);
          if (voter) await this.restoreVoter(voter);
        }
      });
    });
  }

  render() {
    if (!this._hass) return;
    const activeTab = this._activeTab || "meals";

    this.innerHTML = `
      <ha-card header="What's For Dinner">
        <div style="padding:16px">
          <div role="tablist" style="display:flex;gap:8px;margin-bottom:16px">
            <button data-tab="meals" class="tab-button">Meals</button>
            <button data-tab="household" class="tab-button">Voters / Household</button>
          </div>
          <div id="tab-content">
            ${activeTab === "meals" ? this.renderMeals() : this.renderHousehold()}
          </div>
        </div>
      </ha-card>
    `;

    this.querySelectorAll("button[data-tab]").forEach((button) => {
      button.addEventListener("click", () => {
        this._activeTab = button.dataset.tab;
        this.render();
      });
    });
    this.bindActions();
  }
}

customElements.define("wfd-panel", WfdPanel);
