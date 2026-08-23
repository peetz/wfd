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

  render() {
    if (!this._hass) return;

    const meals = this.meals;

    this.innerHTML = `
      <ha-card header="What's For Dinner">
        <div style="padding:16px">
          <h2>Meal Library</h2>
          <p>Manage your household meals from Home Assistant.</p>
          <ha-button id="add" raised>Add meal</ha-button>

          <h3 style="margin-top:24px">Meals</h3>
          ${meals.length
            ? `<ul>${meals.map((meal) => `<li>${meal.name}
                <button data-action="rename" data-id="${meal.id}">Edit</button>
                <button data-action="archive" data-id="${meal.id}">Archive</button>
              </li>`).join("")}</ul>`
            : "<p>No meals available yet.</p>"}
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
      });
    });
  }
}

customElements.define("wfd-panel", WfdPanel);
