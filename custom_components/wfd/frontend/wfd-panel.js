/*
 * What's For Dinner frontend panel foundation.
 *
 * Minimal custom panel bootstrap. Future issues will add views,
 * services and Lovelace widgets using this shared entry point.
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
    this.innerHTML = `
      <ha-card header="What's For Dinner">
        <div style="padding:16px">
          Frontend foundation loaded.
        </div>
      </ha-card>
    `;
  }
}

customElements.define("wfd-panel", WfdPanel);
