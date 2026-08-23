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

  render() {
    if (!this._hass) {
      return;
    }

    this.innerHTML = `
      <ha-card header="What's For Dinner">
        <div style="padding:16px">
          <h2>Meal Library</h2>
          <p>Manage your household meals from Home Assistant.</p>

          <ha-button raised>Add meal</ha-button>

          <h3 style="margin-top:24px">Meals</h3>
          <p>No meals available yet.</p>

          <h3 style="margin-top:24px">Archived meals</h3>
          <p>No archived meals.</p>
        </div>
      </ha-card>
    `;
  }
}

customElements.define("wfd-panel", WfdPanel);
