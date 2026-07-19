(function () {
  "use strict";

  function start() {
    function element(selector) { return document.querySelector(selector); }
    var prompt = element("#prompt");
    var analyzeButton = element("#analyze");
    var csrfMeta = element('meta[name="csrf-token"]');

    if (!prompt || !analyzeButton || !csrfMeta) {
      window.alert("Das Dashboard konnte nicht initialisiert werden. Bitte die Seite neu laden.");
      return;
    }

    var csrf = csrfMeta.content;
    var last = null;
    var providers = [];
    var originalButtonText = analyzeButton.textContent;
    var status = document.createElement("div");
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    status.style.cssText = "min-height:24px;margin-top:10px;color:#6ee7a0;font-size:.9rem";
    analyzeButton.insertAdjacentElement("afterend", status);

    function toast(message) {
      var box = element("#toast");
      box.textContent = message;
      box.classList.add("show");
      window.setTimeout(function () { box.classList.remove("show"); }, 5000);
    }

    async function api(url, options) {
      options = options || {};
      options.headers = Object.assign({"Content-Type": "application/json", "X-CSRF-Token": csrf}, options.headers || {});
      var response = await fetch(url, options);
      var data;
      try { data = response.status === 204 ? {} : await response.json(); }
      catch (_) { throw new Error("Der Server lieferte keine gültige Antwort."); }
      if (!response.ok) throw new Error(data.error || "Anfrage fehlgeschlagen.");
      return data;
    }

    function updateCounter() {
      element("#chars").textContent = prompt.value.length;
      element("#tokens").textContent = Math.max(1, Math.round(prompt.value.length / 4));
    }

    function syncSend() {
      element("#send").disabled = !(element("#confirm").checked && element("#provider").value && last);
      element("#send-eu").disabled = !(element("#confirm").checked && providers.some(function (p) { return p.enabled && p.is_eu_hosted; }) && last && last.compliance.level !== "red");
    }

    function setAnalyzing(active) {
      analyzeButton.disabled = active;
      analyzeButton.textContent = active ? "Analyse läuft …" : originalButtonText;
      analyzeButton.setAttribute("aria-busy", active ? "true" : "false");
      status.textContent = active ? "Der Prompt wird lokal geprüft. Auf langsamen Rechnern kann die Ollama-Analyse mehrere Minuten dauern." : "";
      if (!active) syncSend();
    }

    async function loadProviders() {
      providers = await api("/api/providers");
      var html = '<option value="">Provider wählen …</option>';
      providers.filter(function (p) { return p.enabled; }).forEach(function (p) {
        html += '<option value="' + p.id + '">' + p.name + " · " + p.model_name + (p.is_eu_hosted ? " · EU" : "") + "</option>";
      });
      element("#provider").innerHTML = html;
      syncSend();
    }

    function renderSustainabilityTiles(sustainability) {
      element("#co2").textContent = sustainability.co2_grams + " g";
      element("#energy").textContent = sustainability.energy_kwh + " kWh";
      element("#water").textContent = sustainability.water_liters != null ? sustainability.water_liters + " L" : "–";
      element("#adpe").textContent = sustainability.adpe_ug_sb_eq != null ? sustainability.adpe_ug_sb_eq + " µg Sb-Äq." : "nicht verfügbar";
      element("#electricity-cost").textContent = sustainability.electricity_cost_eur != null ? "€ " + sustainability.electricity_cost_eur.toFixed(6) : "– (nur lokal)";
    }

    function renderOptimizationComparison(data) {
      var comparison = element("#optimization-comparison");
      if (!data.optimized) { comparison.hidden = true; return; }
      comparison.hidden = false;
      var original = data.sustainability.co2_grams;
      var optimized = data.optimized.sustainability.co2_grams;
      element("#co2-original").textContent = original + " g";
      element("#co2-optimized").textContent = optimized + " g";
      var balance = element("#co2-saving");
      if (original > 0) {
        // Positiv = optimierter Prompt verursacht mehr CO2e als das Original, negativ = weniger.
        var deltaPct = Math.round((optimized - original) / original * 100);
        balance.textContent = (deltaPct > 0 ? "+" : "") + deltaPct + " %";
        balance.className = deltaPct > 0 ? "red" : (deltaPct < 0 ? "green" : "");
      } else {
        balance.textContent = "–";
        balance.className = "";
      }
    }

    function render(data) {
      last = data;
      renderSustainabilityTiles(data.sustainability);
      element("#cost").textContent = "€ " + data.estimated_cost.toFixed(6);
      element("#duration").textContent = data.duration.min_seconds + "–" + data.duration.max_seconds + " s";
      element("#compliance").textContent = data.compliance.score + "/100";
      element("#compliance").className = data.compliance.level;
      element("#compliance-findings").textContent = data.compliance.findings.join(", ") || "Keine lokalen Treffer";
      element("#model").textContent = data.recommendation.display_name;
      element("#reason").textContent = data.recommendation.reason;
      element("#region").textContent = data.recommendation.hosting_region;
      element("#eu").textContent = data.recommendation.is_eu_hosted ? "Ja" : "Nein";
      element("#suggestions").innerHTML = data.analysis.optimization_suggestions.map(function (item) { return "<li>" + item + "</li>"; }).join("");
      element("#optimized").value = data.analysis.optimized_prompt;
      renderOptimizationComparison(data);
      element("#send-summary").textContent = "Empfehlung: " + data.recommendation.display_name + " · " + data.recommendation.hosting_region + " · Kosten €" + data.estimated_cost.toFixed(6) + " · CO₂e " + data.sustainability.co2_grams + " g · Risiko " + data.compliance.level.toUpperCase();
      var warnings = [data.warning, data.sustainability_warning].filter(Boolean);
      if (warnings.length) toast(warnings.join(" "));
      syncSend();
    }

    async function analyze(event) {
      if (event) event.preventDefault();
      if (!prompt.value.trim()) { toast("Bitte zuerst einen Prompt eingeben."); prompt.focus(); return; }
      setAnalyzing(true);
      try {
        var data = await api("/api/analyze", {method: "POST", body: JSON.stringify({prompt: prompt.value, mode: element("#mode").value})});
        render(data);
        status.textContent = "Analyse abgeschlossen.";
      } catch (error) {
        status.textContent = "Analyse fehlgeschlagen: " + error.message;
        toast(error.message);
      } finally {
        analyzeButton.disabled = false;
        analyzeButton.textContent = originalButtonText;
        analyzeButton.setAttribute("aria-busy", "false");
      }
    }

    prompt.addEventListener("input", updateCounter);
    updateCounter();
    analyzeButton.addEventListener("click", analyze);
    element("#use-optimized").addEventListener("click", function () { prompt.value = element("#optimized").value; updateCounter(); toast("Optimierter Prompt übernommen. Bitte vor Versand prüfen."); });
    element("#confirm").addEventListener("change", syncSend);
    element("#provider").addEventListener("change", syncSend);
    element("#send").addEventListener("click", function () { send(false); });
    element("#send-eu").addEventListener("click", function () { send(true); });

    async function send(euOnly) {
      var id = element("#provider").value;
      if (euOnly) {
        var euProvider = providers.find(function (p) { return p.enabled && p.is_eu_hosted; });
        if (!euProvider) { toast("Kein aktiver EU-Provider."); return; }
        id = String(euProvider.id); element("#provider").value = id;
      }
      var selected = providers.find(function (p) { return String(p.id) === String(id); });
      if (!window.confirm("Prompt jetzt bewusst an " + (selected ? selected.name : "den Provider") + " senden?")) return;
      try {
        var data = await api("/api/send", {method: "POST", body: JSON.stringify({prompt: prompt.value, provider_id: Number(id), eu_only: euOnly, override_reason: element("#override").value})});
        element("#answer").style.display = "block"; element("#answer").textContent = data.answer;
        if (element("#discard").checked) { prompt.value = ""; element("#optimized").value = ""; updateCounter(); }
        var summary = "Antwort erhalten (" + data.latency_ms + " ms). ";
        if (data.sustainability) summary += "Tatsächliches CO₂e " + data.sustainability.co2_grams + " g. ";
        toast(summary + (data.sustainability_warning || ""));
      } catch (error) { toast(error.message); }
    }

    loadProviders().catch(function (error) { toast(error.message); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
