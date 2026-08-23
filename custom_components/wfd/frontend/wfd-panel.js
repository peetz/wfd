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

  render() {
    if (!this._hass) return;

    this.innerHTML = `
      <ha-card header="What's For Dinner">
        <div style="padding:16px">
          <h2>Meal Library</h2>
          <p>Manage your household meals from Home Assistant.</p>
          <ha-button id="add" raised>Add meal</ha-button>

          <h3 style="margin-top:24px">Meals</h3>
          <p>Meal actions are connected to WFD services.</p>

          <h3 style="margin-top:24px">Archived meals</h3>
          <p>Restore archived meals from this view.</p>
        </div>
      </ha-card>
    `;

    this.querySelector("#add")?.addEventListener("click", () => this.addMeal());
  }
}

customElements.define("wfd-panel", WfdPanel);
