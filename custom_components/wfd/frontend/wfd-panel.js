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

  _meals() {
    const entity = this._hass?.states?.sensor?.wfd_meal_library;
    return entity?.attributes?.meals || [];
  }

  async restoreMeal(id) {
    await this._hass.callService("wfd", "restore_meal", { meal_id: id });
  }

  async archiveMeal(id) {
    await this._hass.callService("wfd", "archive_meal", { meal_id: id });
  }

  render() {
    const meals = this._meals();
    const active = meals.filter((meal) => meal.active !== false);
    const archived = meals.filter((meal) => meal.active === false);

    const mealRows = (items, action) => items.map((meal) => `
      <div style="display:flex;justify-content:space-between;padding:8px 0">
        <span>${meal.name}</span>
        ${action ? `<button data-id="${meal.id}" class="meal-action">${action.label}</button>` : ""}
      </div>
    `).join("");

    this.innerHTML = `
      <ha-card header="Meal Library">
        <div style="padding:16px">
          <h3>Active Meals</h3>
          ${mealRows(active, {label: "Archive"}) || "No active meals"}
          <h3>Archived Meals</h3>
          ${mealRows(archived, {label: "Restore"}) || "No archived meals"}
        </div>
      </ha-card>
    `;

    this.querySelectorAll("button.meal-action").forEach((button) => {
      button.addEventListener("click", () => {
        const meal = meals.find((item) => item.id === button.dataset.id);
        if (!meal) return;
        if (meal.active === false) {
          this.restoreMeal(meal.id);
        } else {
          this.archiveMeal(meal.id);
        }
      });
    });
  }
}

customElements.define("wfd-panel", WfdPanel);
