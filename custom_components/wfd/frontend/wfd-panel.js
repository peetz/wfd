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

  async addMeal() {
    const name = window.prompt("Meal name");
    if (!name) return;

    await this._hass.callService("wfd", "add_meal", { name });
    this.render();
  }

  get meals() {
    return this._hass?.states?.["sensor.wfd_meal_library"]?.attributes?.meals || [];
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
            ? `<ul>${meals.map((meal) => `<li>${typeof meal === "string" ? meal : meal.name}</li>`).join("")}</ul>`
            : "<p>No meals available yet.</p>"}

          <h3 style="margin-top:24px">Archived meals</h3>
          <p>Restore archived meals from this view.</p>
        </div>
      </ha-card>
    `;

    this.querySelector("#add")?.addEventListener("click", () => this.addMeal());
  }
}

customElements.define("wfd-panel", WfdPanel);
