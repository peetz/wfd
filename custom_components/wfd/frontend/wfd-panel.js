/*
 * What's For Dinner meal library frontend.
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

  render() {
    if (!this._hass) return;

    const meals = this.meals;
    const active = meals.filter((meal) => meal.active !== false);
    const archived = meals.filter((meal) => meal.active === false);

    const rows = (items, actions) => items.map((meal) => `
      <li>
        ${meal.name}
        ${actions.map((action) => `<button data-action="${action}" data-id="${meal.id}">${action}</button>`).join("")}
      </li>
    `).join("");

    this.innerHTML = `
      <ha-card header="What's For Dinner">
        <div style="padding:16px">
          <h2>Meal Library</h2>
          <ha-button id="add" raised>Add meal</ha-button>

          <h3>Active Meals</h3>
          ${active.length ? `<ul>${rows(active, ["rename", "archive"])}</ul>` : "<p>No active meals.</p>"}

          <h3>Archived Meals</h3>
          ${archived.length ? `<ul>${rows(archived, ["restore"])}</ul>` : "<p>No archived meals.</p>"}
        </div>
      </ha-card>
    `;

    this.querySelector("#add")?.addEventListener("click", () => this.addMeal());

    this.querySelectorAll("button[data-action]").forEach((button) => {
      button.addEventListener("click", async () => {
        const meal = meals.find((item) => item.id === button.dataset.id);
        if (!meal) return;
        if (button.dataset.action === "rename") await this.renameMeal(meal);
        if (button.dataset.action === "archive") await this.archiveMeal(meal);
        if (button.dataset.action === "restore") await this.restoreMeal(meal);
      });
    });
  }
}

customElements.define("wfd-panel", WfdPanel);
