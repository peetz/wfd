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
    const meals = this._hass?.states || {};

    this.innerHTML = `
      <ha-card header="What's For Dinner">
        <div style="padding:16px">
          <h2>Meal Library</h2>
          <p>Manage your household meals from Home Assistant.</p>
          <ha-button raised>Add meal</ha-button>
          <p style="margin-top:16px">Meal management actions will use WFD services.</p>
        </div>
      </ha-card>
    `;
  }
}

customElements.define("wfd-panel", WfdPanel);
