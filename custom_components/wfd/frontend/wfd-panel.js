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

  async call(action, name, extra = {}) {
    await this._hass.callService("wfd", action, { name, ...extra });
  }

  async addMeal() {
    const name = window.prompt("Meal name");
    if (!name) return;
    await this.call("add_meal", name);
  }

  async renameMeal(name) {
    const newName = window.prompt("Rename meal", name);
    if (!newName || newName === name) return;
    await this.call("rename_meal", name, { new_name: newName });
  }

  async archiveMeal(name) {
    await this.call("archive_meal", name);
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
            ? `<ul>${meals.map((meal) => {
                const name = typeof meal === "string" ? meal : meal.name;
                return `<li>${name}
                  <button data-action="rename" data-name="${name}">Edit</button>
                  <button data-action="archive" data-name="${name}">Archive</button>
                </li>`;
              }).join("")}</ul>`
            : "<p>No meals available yet.</p>"}

          <h3 style="margin-top:24px">Archived meals</h3>
          <p>Restore archived meals from this view.</p>
        </div>
      </ha-card>
    `;

    this.querySelector("#add")?.addEventListener("click", () => this.addMeal());

    this.querySelectorAll("button[data-action]").forEach((button) => {
      button.addEventListener("click", async () => {
        const action = button.dataset.action;
        const name = button.dataset.name;
        if (action === "rename") await this.renameMeal(name);
        if (action === "archive") await this.archiveMeal(name);
      });
    });
  }
}

customElements.define("wfd-panel", WfdPanel);
