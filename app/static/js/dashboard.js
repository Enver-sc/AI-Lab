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
    var conversation = [];
    var cumulativeCost = 0;
    var cumulativeInputTokens = 0;
    var cumulativeOutputTokens = 0;
    var cumulativeCo2 = 0;
    var originalButtonText = analyzeButton.textContent;
    var status = document.createElement("div");
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    status.style.cssText = "min-height:24px;margin-top:10px;color:#6ee7a0;font-size:.9rem";
    analyzeButton.insertAdjacentElement("afterend", status);
    var modelLabel = document.createElement("label");
    modelLabel.htmlFor = "send-model";
    modelLabel.textContent = "Claude-Modell für den Versand";
    var modelSelect = document.createElement("select");
    modelSelect.id = "send-model";
    modelSelect.innerHTML = '<option value="claude-haiku-4-5-20251001">Claude Haiku 4.5 · $1/$5 je Mio. Input-/Output-Token</option>'
      + '<option value="claude-sonnet-4-6">Claude Sonnet 4.6 · $3/$15 je Mio. Input-/Output-Token</option>';
    element("#provider").insertAdjacentElement("afterend", modelSelect);
    modelSelect.insertAdjacentElement("beforebegin", modelLabel);

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

    function ensureChat() {
      var chat = element("#chat-continuation");
      if (chat) return chat;
      chat = document.createElement("section");
      chat.id = "chat-continuation";
      chat.style.cssText = "display:grid;grid-template-columns:minmax(0,1fr) 260px;align-items:start;gap:20px;margin-top:18px";
      chat.innerHTML = '<div><h3>Chat fortsetzen</h3><div id="chat-messages" style="display:grid;gap:14px;max-height:620px;overflow:auto;padding-right:8px;margin-bottom:16px"></div><label for="chat-input">Nächste Nachricht</label><textarea id="chat-input" rows="3" placeholder="Schreibe eine Folgefrage …"></textarea><button id="chat-send" class="primary" type="button">Nachricht senden</button><div id="chat-compliance" hidden></div></div>'
        + '<aside class="summary" style="position:sticky;top:20px"><h3>Kosten und Nutzung</h3><p>Letzte Runde<br><strong id="chat-turn-cost">$ 0.000000</strong></p><p>Input<br><strong id="chat-input-tokens">0</strong> Token · <strong id="chat-input-cost">$ 0.000000</strong></p><p>Output<br><strong id="chat-output-tokens">0</strong> Token · <strong id="chat-output-cost">$ 0.000000</strong></p><hr><p>Gesamtkosten<br><strong id="chat-total-cost">$ 0.000000</strong></p><p>Gesamttoken<br><strong id="chat-total-tokens">0</strong></p><p>CO₂e gesamt<br><strong id="chat-total-co2">0 g</strong></p></aside>';
      element("#answer").insertAdjacentElement("afterend", chat);
      element("#chat-send").addEventListener("click", continueChat);
      return chat;
    }

    function appendInlineMarkdown(parent, value) {
      var parts = value.split(/(\*\*[^*]+\*\*)/g);
      parts.forEach(function (part) {
        if (part.slice(0, 2) === "**" && part.slice(-2) === "**") {
          var strong = document.createElement("strong");
          strong.textContent = part.slice(2, -2);
          parent.appendChild(strong);
        } else {
          parent.appendChild(document.createTextNode(part));
        }
      });
    }

    function tableCells(line) {
      return line.replace(/^\s*\||\|\s*$/g, "").split("|").map(function (cell) { return cell.trim(); });
    }

    function renderAssistantMarkdown(container, content) {
      var lines = content.replace(/\r\n/g, "\n").split("\n");
      for (var index = 0; index < lines.length; index += 1) {
        var line = lines[index].trim();
        if (!line) continue;
        if (line.indexOf("|") !== -1 && index + 1 < lines.length && /^\s*\|?\s*:?-+/.test(lines[index + 1])) {
          var table = document.createElement("table");
          table.style.cssText = "width:100%;border-collapse:collapse;margin:10px 0;font-size:.92rem";
          var head = document.createElement("thead");
          var headRow = document.createElement("tr");
          tableCells(line).forEach(function (cell) {
            var th = document.createElement("th");
            th.style.cssText = "text-align:left;padding:8px;border-bottom:1px solid #466455";
            appendInlineMarkdown(th, cell);
            headRow.appendChild(th);
          });
          head.appendChild(headRow);
          table.appendChild(head);
          var body = document.createElement("tbody");
          index += 2;
          while (index < lines.length && lines[index].indexOf("|") !== -1 && lines[index].trim()) {
            var row = document.createElement("tr");
            tableCells(lines[index]).forEach(function (cell) {
              var td = document.createElement("td");
              td.style.cssText = "padding:8px;border-bottom:1px solid #29483a;vertical-align:top";
              appendInlineMarkdown(td, cell);
              row.appendChild(td);
            });
            body.appendChild(row);
            index += 1;
          }
          index -= 1;
          table.appendChild(body);
          var wrapper = document.createElement("div");
          wrapper.style.overflowX = "auto";
          wrapper.appendChild(table);
          container.appendChild(wrapper);
          continue;
        }
        var headingMatch = line.match(/^(#{1,3})\s+(.+)$/);
        var listMatch = line.match(/^[-*]\s+(.+)$/);
        var numberedMatch = line.match(/^\d+[.)]\s+(.+)$/);
        var node;
        if (headingMatch) {
          node = document.createElement(headingMatch[1].length === 1 ? "h3" : "h4");
          node.style.margin = "12px 0 6px";
          appendInlineMarkdown(node, headingMatch[2]);
        } else if (listMatch || numberedMatch) {
          node = document.createElement("div");
          node.style.cssText = "display:grid;grid-template-columns:20px 1fr;gap:4px;margin:5px 0";
          var marker = document.createElement("span");
          marker.textContent = numberedMatch ? line.match(/^\d+/)[0] + "." : "•";
          var listText = document.createElement("span");
          appendInlineMarkdown(listText, (listMatch || numberedMatch)[1]);
          node.appendChild(marker);
          node.appendChild(listText);
        } else {
          node = document.createElement("p");
          node.style.margin = "6px 0";
          appendInlineMarkdown(node, line);
        }
        container.appendChild(node);
      }
    }

    function appendChatMessage(role, content, cost) {
      ensureChat();
      var message = document.createElement("article");
      message.className = role === "user" ? "summary" : "panel";
      var heading = document.createElement("strong");
      heading.textContent = role === "user" ? "Du" : "API";
      var text = document.createElement("div");
      text.style.cssText = "line-height:1.6;overflow-wrap:anywhere";
      if (role === "assistant") renderAssistantMarkdown(text, content);
      else text.textContent = content;
      message.appendChild(heading);
      message.appendChild(text);
      if (cost != null) {
        var price = document.createElement("small");
        price.textContent = "Kosten dieser API-Antwort: $ " + cost.toFixed(6);
        message.appendChild(price);
      }
      element("#chat-messages").appendChild(message);
      element("#chat-messages").scrollTop = element("#chat-messages").scrollHeight;
    }

    function recordUsage(data) {
      cumulativeCost += data.actual_cost || 0;
      cumulativeInputTokens += data.input_tokens || 0;
      cumulativeOutputTokens += data.output_tokens || 0;
      cumulativeCo2 += data.sustainability ? data.sustainability.co2_grams || 0 : 0;
      element("#chat-turn-cost").textContent = "$ " + (data.actual_cost || 0).toFixed(6);
      element("#chat-input-tokens").textContent = data.input_tokens || 0;
      element("#chat-output-tokens").textContent = data.output_tokens || 0;
      element("#chat-input-cost").textContent = "$ " + (data.input_cost || 0).toFixed(6);
      element("#chat-output-cost").textContent = "$ " + (data.output_cost || 0).toFixed(6);
      element("#chat-total-cost").textContent = "$ " + cumulativeCost.toFixed(6);
      element("#chat-total-tokens").textContent = cumulativeInputTokens + cumulativeOutputTokens;
      element("#chat-total-co2").textContent = cumulativeCo2.toFixed(4) + " g";
    }

    function resetChatCompliance() {
      var box = element("#chat-compliance");
      if (box) { box.hidden = true; box.innerHTML = ""; }
    }

    function complianceBadge(check) {
      var badge = document.createElement("p");
      var color = check.level === "red" ? "var(--red)" : check.level === "yellow" ? "var(--yellow)" : "var(--green)";
      badge.style.cssText = "margin:10px 0 4px;font-weight:750;color:" + color;
      badge.textContent = "Compliance-Prüfung (Nachricht + Verlauf): " + check.score + "/100 · " + check.level.toUpperCase();
      return badge;
    }

    function showChatCompliance(check, content) {
      var box = element("#chat-compliance");
      box.hidden = false;
      box.innerHTML = "";
      box.appendChild(complianceBadge(check));
      var findings = document.createElement("small");
      findings.textContent = "Treffer: " + (check.findings.join(", ") || "keine lokalen Treffer");
      box.appendChild(findings);
      if (check.level === "green") {
        sendChatMessage(content, "");
        return;
      }
      var hint = document.createElement("div");
      hint.className = "alert warning";
      hint.style.marginTop = "10px";
      hint.textContent = check.level === "red"
        ? "Rote Bewertung: Der Versand ist blockiert, bis du eine frische Begründung (mindestens 10 Zeichen) für genau diese Nachricht angibst."
        : "Gelbe Bewertung: Diese Nachricht oder der bisherige Verlauf enthält möglicherweise sensible Inhalte. Bitte bewusst entscheiden.";
      box.appendChild(hint);
      var reasonInput = null;
      if (check.level === "red") {
        var reasonLabel = document.createElement("label");
        reasonLabel.htmlFor = "chat-override";
        reasonLabel.textContent = "Begründung für diese Nachricht";
        reasonInput = document.createElement("textarea");
        reasonInput.id = "chat-override";
        reasonInput.rows = 2;
        reasonInput.placeholder = "Warum darf diese Nachricht trotz roter Bewertung gesendet werden?";
        box.appendChild(reasonLabel);
        box.appendChild(reasonInput);
      }
      var actions = document.createElement("div");
      actions.className = "actions";
      var confirmButton = document.createElement("button");
      confirmButton.type = "button";
      confirmButton.className = "primary";
      confirmButton.textContent = "Bewusst senden";
      var cancelButton = document.createElement("button");
      cancelButton.type = "button";
      cancelButton.textContent = "Abbrechen";
      actions.appendChild(confirmButton);
      actions.appendChild(cancelButton);
      box.appendChild(actions);
      confirmButton.addEventListener("click", function () {
        var reason = reasonInput ? reasonInput.value.trim() : "";
        if (check.level === "red" && reason.length < 10) {
          toast("Bitte eine Begründung mit mindestens 10 Zeichen angeben.");
          return;
        }
        resetChatCompliance();
        sendChatMessage(content, reason);
      });
      cancelButton.addEventListener("click", function () {
        resetChatCompliance();
        element("#chat-send").disabled = false;
        toast("Senden abgebrochen. Die Nachricht bleibt im Eingabefeld.");
      });
    }

    async function continueChat() {
      var input = element("#chat-input");
      var content = input.value.trim();
      if (!content) { toast("Bitte eine Nachricht eingeben."); return; }
      var selected = providers.find(function (p) { return String(p.id) === element("#provider").value; });
      if (!selected) { toast("Bitte einen Provider auswählen."); return; }
      var button = element("#chat-send");
      button.disabled = true;
      resetChatCompliance();
      try {
        var check = await api("/api/compliance/check", {method: "POST", body: JSON.stringify({prompt: content, messages: conversation.concat([{role: "user", content: content}])})});
        showChatCompliance(check, content);
      } catch (error) {
        toast(error.message);
        button.disabled = false;
      }
    }

    async function sendChatMessage(content, overrideReason) {
      var input = element("#chat-input");
      var button = element("#chat-send");
      var selected = providers.find(function (p) { return String(p.id) === element("#provider").value; });
      if (!selected) { toast("Bitte einen Provider auswählen."); button.disabled = false; return; }
      conversation.push({role: "user", content: content});
      appendChatMessage("user", content);
      try {
        var data = await api("/api/send", {method: "POST", body: JSON.stringify({prompt: content, messages: conversation, provider_id: selected.id, model_name: modelSelect.value, override_reason: overrideReason})});
        conversation.push({role: "assistant", content: data.answer});
        appendChatMessage("assistant", data.answer, data.actual_cost);
        recordUsage(data);
        input.value = "";
      } catch (error) {
        conversation.pop();
        var errorMessage = document.createElement("div");
        errorMessage.className = "alert warning";
        errorMessage.textContent = "Nachricht nicht gesendet: " + error.message;
        element("#chat-messages").appendChild(errorMessage);
        toast(error.message);
      } finally {
        button.disabled = false;
      }
    }

    function selectedProviderEstimate() {
      var selected = providers.find(function (p) { return String(p.id) === element("#provider").value; });
      var warning = element("#model-warning");
      if (!warning) {
        warning = document.createElement("div");
        warning.id = "model-warning";
        warning.className = "alert warning";
        element("#provider").insertAdjacentElement("afterend", warning);
      }
      warning.hidden = true;
      modelLabel.hidden = !selected || selected.provider_type !== "anthropic";
      modelSelect.hidden = !selected || selected.provider_type !== "anthropic";
      if (!last || !selected) return;
      var inputPrice = selected.input_cost_per_million;
      var outputPrice = selected.output_cost_per_million;
      if (selected.provider_type === "anthropic") {
        inputPrice = modelSelect.value === "claude-sonnet-4-6" ? 3 : 1;
        outputPrice = modelSelect.value === "claude-sonnet-4-6" ? 15 : 5;
      }
      var cost = last.input_tokens / 1000000 * inputPrice
        + last.expected_output_tokens / 1000000 * outputPrice;
      element("#cost").textContent = (selected.provider_type === "anthropic" ? "$ " : "€ ") + cost.toFixed(6);
      if (last.recommendation.model_id.indexOf("haiku") !== -1 && modelSelect.value.indexOf("sonnet") !== -1) {
        warning.textContent = "Hinweis: Die lokale Analyse hält Claude Haiku 4.5 für ausreichend. Claude Sonnet 4.6 ist auswählbar, verursacht für diese Anfrage aber voraussichtlich unnötig höhere Kosten.";
        warning.hidden = false;
      }
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
      selectedProviderEstimate();
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
      element("#cost").textContent = (data.recommendation.provider === "Anthropic" ? "$ " : "€ ") + data.estimated_cost.toFixed(6);
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
      var costSymbol = data.recommendation.provider === "Anthropic" ? "$" : "€";
      element("#send-summary").textContent = "Empfehlung: " + data.recommendation.display_name + " · " + data.recommendation.hosting_region + " · Kosten " + costSymbol + data.estimated_cost.toFixed(6) + " · CO₂e " + data.sustainability.co2_grams + " g · Risiko " + data.compliance.level.toUpperCase();
      modelSelect.value = data.recommendation.model_id.indexOf("sonnet") !== -1
        ? "claude-sonnet-4-6"
        : "claude-haiku-4-5-20251001";
      var recommended = providers.find(function (p) { return p.enabled && p.provider_type === "anthropic"; });
      if (recommended) element("#provider").value = String(recommended.id);
      selectedProviderEstimate();
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
    element("#provider").addEventListener("change", function () { selectedProviderEstimate(); syncSend(); });
    modelSelect.addEventListener("change", selectedProviderEstimate);
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
      var selectedModel = selected && selected.provider_type === "anthropic" ? " mit " + modelSelect.options[modelSelect.selectedIndex].text : "";
      if (!window.confirm("Prompt jetzt bewusst an " + (selected ? selected.name : "den Provider") + selectedModel + " senden?")) return;
      try {
        var data = await api("/api/send", {method: "POST", body: JSON.stringify({prompt: prompt.value, provider_id: Number(id), model_name: modelSelect.value, eu_only: euOnly, override_reason: element("#override").value})});
        var oldChat = element("#chat-continuation");
        if (oldChat) oldChat.remove();
        conversation = [
          {role: "user", content: prompt.value},
          {role: "assistant", content: data.answer}
        ];
        cumulativeCost = 0;
        cumulativeInputTokens = 0;
        cumulativeOutputTokens = 0;
        cumulativeCo2 = 0;
        element("#answer").style.display = "block";
        element("#answer").textContent = "Verwendetes Modell: " + (data.model_used || "unbekannt");
        appendChatMessage("user", prompt.value);
        appendChatMessage("assistant", data.answer, data.actual_cost);
        recordUsage(data);
        // Begründung gilt nur für genau diesen Versand -- nie stillschweigend wiederverwenden.
        element("#override").value = "";
        if (element("#discard").checked) { prompt.value = ""; element("#optimized").value = ""; updateCounter(); }
        var summary = "Antwort erhalten mit " + (data.model_used || "dem gewählten Modell") + " (" + data.latency_ms + " ms). ";
        if (data.actual_cost != null) {
          element("#cost").textContent = (data.cost_currency === "USD" ? "$ " : "€ ") + data.actual_cost.toFixed(6);
          summary += "Berechnete Kosten " + data.actual_cost.toFixed(6) + " " + data.cost_currency + ". ";
        }
        if (data.sustainability) summary += "Tatsächliches CO₂e " + data.sustainability.co2_grams + " g. ";
        toast(summary + (data.sustainability_warning || ""));
      } catch (error) { toast(error.message); }
    }

    loadProviders().catch(function (error) { toast(error.message); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
