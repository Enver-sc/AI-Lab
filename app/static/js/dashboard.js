(function () {
  "use strict";

  function start() {
    function element(selector) { return document.querySelector(selector); }
    function currencySymbol(currency) { return currency === "USD" ? "$" : "€"; }
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
    var cumulativeEnergy = 0;
    var cumulativeWater = 0;
    var cumulativeWaterAvailable = true;
    var lastCostCurrency = "EUR";
    // Gemeinsame Alltags-Referenz fuer CO2/Energie/Wasser: eine (kleinere) Tasse Tee kochen
    // (150 mL Wasser von ca. 20 auf 100 Grad erhitzt). Grobe physikalische Ueberschlagsrechnung,
    // keine zitierte Quelle -- linear aus der 250-mL-Herleitung skaliert (Faktor 0,6, da Energie
    // bei gleicher Temperaturdifferenz proportional zur Wassermenge ist): 150 g * 4,186 J/(g*K)
    // * 80 K = 50,2 kJ ideal, mit ~85% Wasserkocher-Wirkungsgrad ~15 Wh real; CO2 daraus mit
    // demselben CARBON_INTENSITY_G_PER_KWH (350 g/kWh) abgeleitet wie die serverseitige
    // Formel-Schaetzung, statt eine unabhaengige Zahl zu erfinden. ADPe bleibt bewusst ohne
    // Referenz (Herstellungs-, kein Nutzungseffekt).
    var TEA_CUP_WATER_ML = 150;
    var TEA_CUP_ENERGY_WH = 15;
    var TEA_CUP_CO2_G = 5.25;
    // Sensibilisierungs-Hochrechnung: "was waere, wenn diese Konversation 500-mal vorkaeme"
    // (Testfassung, willkuerlich gewaehlter Faktor, keine reale Nutzerzahl-Prognose).
    var REQUEST_MULTIPLIER = 500;
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

    // Navigation zu einer anderen Seite (z. B. Provider-Einstellungen) und zurueck ist ein
    // vollstaendiger Seitenneuaufbau, kein SPA-Tab -- ohne Persistenz waeren Prompt und Analyse
    // jedes Mal weg. sessionStorage statt localStorage: verschwindet mit dem Tab/Browser, passt
    // zum bestehenden Privacy-by-Design-Ansatz (Prompts werden serverseitig nicht gespeichert).
    // Bewusst nur Prompt + letztes Analyse-Ergebnis, kein laufender Chat-Verlauf (Nutzer-Entscheidung).
    var STATE_STORAGE_KEY = "sag-dashboard-state";
    function saveState() {
      try {
        sessionStorage.setItem(STATE_STORAGE_KEY, JSON.stringify({prompt: prompt.value, last: last}));
      } catch (error) {
        // Persistenz ist ein Komfortfeature (z. B. privater Modus blockiert sessionStorage) --
        // darf die App nie zum Absturz bringen.
      }
    }
    function restoreState() {
      var raw;
      try { raw = sessionStorage.getItem(STATE_STORAGE_KEY); } catch (error) { return; }
      if (!raw) return;
      var state;
      try { state = JSON.parse(raw); } catch (error) { return; }
      if (state.prompt) { prompt.value = state.prompt; updateCounter(); }
      if (state.last) { render(state.last); status.textContent = "Wiederhergestellt aus der letzten Analyse."; }
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
      chat.innerHTML = '<div><h3>Chat fortsetzen</h3><div id="chat-messages" class="chat-messages"></div><label for="chat-input">Nächste Nachricht</label><textarea id="chat-input" rows="3" placeholder="Schreibe eine Folgefrage …"></textarea><div class="chat-actions"><button id="chat-estimate-btn" class="secondary" type="button">Fußabdruck schätzen</button><button id="chat-send" class="primary" type="button">Nachricht senden</button></div><p id="chat-estimate-result" class="chat-estimate-result"></p></div>'
        + '<aside class="summary chat-summary">'
        + '<div class="panel projection-panel"><h3>Kosten und Nutzung</h3>'
        + '<p>Letzte Runde<br><strong id="chat-turn-cost">$ 0.000000</strong></p><p>Input<br><strong id="chat-input-tokens">0</strong> Token · <strong id="chat-input-cost">$ 0.000000</strong></p><p>Output<br><strong id="chat-output-tokens">0</strong> Token · <strong id="chat-output-cost">$ 0.000000</strong></p><hr><p>Gesamtkosten<br><strong id="chat-total-cost">$ 0.000000</strong></p><p>Gesamttoken<br><strong id="chat-total-tokens">0</strong></p></div>'
        + '<div class="panel projection-panel"><h3>Fußabdruck dieser Unterhaltung</h3>'
        + '<div class="rings"><svg viewBox="0 0 120 120" width="140" height="140">'
        + '<circle class="ring-track" cx="60" cy="60" r="52"></circle><circle id="ring-water" class="ring-fill water" cx="60" cy="60" r="52"></circle>'
        + '<circle class="ring-track" cx="60" cy="60" r="41"></circle><circle id="ring-co2" class="ring-fill co2" cx="60" cy="60" r="41"></circle>'
        + '<circle class="ring-track" cx="60" cy="60" r="30"></circle><circle id="ring-energy" class="ring-fill energy" cx="60" cy="60" r="30"></circle>'
        + '</svg></div>'
        + '<p>💧 Wasser · <strong id="chat-eco-water">–</strong></p>'
        + '<p>🌿 CO₂e&nbsp; · <strong id="chat-eco-co2">–</strong></p>'
        + '<p>' + BATTERY_ICON + ' Energie · <strong id="chat-eco-energy">–</strong></p>'
        + '<hr>'
        + '<p class="meter-note">Referenz: 150 mL Tasse heißer Tee.</p>'
        + '<p><small id="chat-eco-indicator"></small></p></div>'
        + '<div class="panel projection-panel"><h3>500 KI-Anfragen (Näherung)</h3>'
        + '<div id="chat-500x-water-segments" class="cup-segments water"></div>'
        + '<div id="chat-500x-co2-segments" class="cup-segments co2"></div>'
        + '<div id="chat-500x-energy-segments" class="cup-segments energy"></div>'
        + '<hr><p class="cup-legend">💧 Wasser · 🌿 CO₂e · ' + BATTERY_ICON + ' Energie</p>'
        + '<p class="meter-note">Referenz: 150 mL Tasse heißer Tee.</p>'
        + '<p class="meter-note">Hochgerechnet: Fußabdruck, wenn deine bisherige Nutzung in diesem Chat 500 andere Anwender ebenfalls so ausführen würden.</p></div></aside>';
      element("#answer").insertAdjacentElement("afterend", chat);
      element("#chat-send").addEventListener("click", continueChat);
      element("#chat-estimate-btn").addEventListener("click", estimateChatFootprint);
      return chat;
    }

    async function estimateChatFootprint() {
      var input = element("#chat-input");
      var content = input.value.trim();
      var result = element("#chat-estimate-result");
      if (!content) { toast("Bitte eine Nachricht eingeben."); return; }
      var selected = providers.find(function (p) { return String(p.id) === element("#provider").value; });
      if (!selected) { toast("Bitte einen Provider auswählen."); return; }
      try {
        var data = await api("/api/estimate-footprint", {method: "POST", body: JSON.stringify({
          text: content,
          provider_id: selected.id,
          model_name: modelSelect.value,
          model_class: last ? last.recommendation.model_class : null
        })});
        var costSymbol = selected.provider_type === "anthropic" ? "$" : "€";
        var sustainabilityText = data.sustainability
          ? " · CO₂e " + data.sustainability.co2_grams + " g"
            + " · Energie " + data.sustainability.energy_wh + " Wh"
            + " · Wasser " + (data.sustainability.water_ml != null ? data.sustainability.water_ml + " mL" : "–")
          : "";
        result.textContent = "Geschätzt für diese Nachricht: " + data.expected_output_tokens + " Ausgabe-Token · "
          + costSymbol + " " + data.estimated_cost.toFixed(6)
          + sustainabilityText
          + " · " + ecoIndicatorLabel(data.sustainability);
        if (data.sustainability_warning) toast(data.sustainability_warning);
      } catch (error) {
        toast(error.message);
      }
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

    function appendChatMessage(role, content, cost, currency) {
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
        price.textContent = "Kosten dieser API-Antwort: " + currencySymbol(currency) + " " + cost.toFixed(6);
        message.appendChild(price);
      }
      element("#chat-messages").appendChild(message);
      element("#chat-messages").scrollTop = element("#chat-messages").scrollHeight;
    }

    // Fuellstand + Bruch-Angabe gegen eine echte Alltags-Referenzgroesse (statt session-relativ) --
    // ein Bruch ("~1/500") ist bei so kleinen Anteilen leichter erfassbar als eine Prozentzahl.
    function updateRing(id, ratio) {
      var circle = element(id);
      if (!circle) return;
      var circumference = 2 * Math.PI * parseFloat(circle.getAttribute("r"));
      circle.style.strokeDasharray = circumference;
      circle.style.strokeDashoffset = circumference * (1 - Math.min(1, ratio));
      // Ein voller Ring sieht bei 1,0x genauso aus wie bei 5x -- ein Leuchtrand macht
      // wenigstens sichtbar "das ist ueber der Referenz", auch ohne die genaue Vielfachheit
      // im Ring selbst darzustellen (die steht in der Tassen-Segmentreihe/im Text daneben).
      circle.classList.toggle("overflow", ratio >= 1);
    }

    // Echte Tassen-Silhouette statt generischer Balken -- Fuellung per CSS clip-path von unten,
    // dieselbe --fill-Custom-Property wie zuvor, nur jetzt auf eine Tassenform statt ein Rechteck
    // angewandt. Optionale Zahl in der Tasse (fuer die "grosse Tasse pro volle Reihe"-Logik unten).
    // Statisches Batterie-Icon statt 🔋-Emoji: Emoji-Farben sind vom Betriebssystem/der
    // Schriftart vorgegeben (meist gruen), nicht per CSS aenderbar -- fuer die einheitliche
    // Rot-Zuordnung von Energie (Ring/Tasse nutzen bereits var(--red)) reicht ein einfaches
    // SVG. 3/4 rot gefuellt, Rest schwarz, roter Rahmen fuer Erkennbarkeit (Nutzerwunsch).
    var BATTERY_ICON = '<svg class="battery-icon" viewBox="0 0 28 16" aria-hidden="true">'
      + '<rect class="battery-outline" x="1" y="1" width="22" height="14" rx="2"></rect>'
      + '<rect class="battery-fill" x="24" y="5" width="3" height="6" rx="1"></rect>'
      + '<rect class="battery-empty" x="3" y="3" width="18" height="10"></rect>'
      + '<rect class="battery-fill" x="3" y="3" width="13.5" height="10"></rect>'
      + '</svg>';

    function cupIconMarkup(number) {
      var numberMarkup = number ? '<text x="12" y="18" text-anchor="middle" class="cup-number">' + number + '</text>' : '';
      return '<svg viewBox="0 0 24 28" class="cup-icon" aria-hidden="true">'
        + '<path class="cup-fill" d="M4,6 L20,6 L18.5,24 Q18.5,26 16,26 L8,26 Q5.5,26 5.5,24 Z"></path>'
        + '<path class="cup-handle" d="M20,10 a4.5,4.5 0 0 1 0,9" fill="none"></path>'
        + '<path class="cup-outline" d="M4,6 L20,6 L18.5,24 Q18.5,26 16,26 L8,26 Q5.5,26 5.5,24 Z" fill="none"></path>'
        + numberMarkup
        + '</svg>';
    }

    function createCupSegment(state, number) {
      var span = document.createElement("span");
      span.className = "cup-segment " + state;
      span.innerHTML = cupIconMarkup(number);
      return span;
    }

    // Segment-Reihe ("wie viele ganze Tassen"): eine volle Reihe (SEGMENTS_PER_ROW Tassen) wird
    // durch eine einzelne groessere Tasse mit der Reihengroesse als Zahl ersetzt -- dadurch bleibt
    // die Anzeige immer eine ganze, gut lesbare Zahl statt eines "+X,Y"-Zusatzes. Erst wenn selbst
    // das unrealistisch viele grosse Tassen ergaebe (MAX_BIG_CUPS ueberschritten), greift der
    // "+X"-Text als Fallback fuer den nicht mehr darstellbaren Rest.
    function renderCupSegments(containerId, ratio) {
      var container = element(containerId);
      if (!container) return;
      container.innerHTML = "";
      if (!(ratio > 0)) return;
      // 5 statt 10: bei der 260px breiten Statusleiste passen je nach Aufloesung nur ca. 5-7
      // Tassen nebeneinander in eine Zeile (siehe Live-Test-Screenshot), nicht 10 -- die
      // Gruppierung "volle Zeile = grosse Tasse" muss zur tatsaechlichen Kapazitaet passen.
      // Layout laeuft dazu jetzt ueber ein festes CSS-Grid mit ebenfalls 5 Spalten (statt
      // aufloesungsabhaengigem Flex-Umbruch), damit "eine Zeile" ueberall gleich viele Tassen sind.
      var segmentsPerRow = 5;
      var maxBigCups = 8;
      var bigCupCount = Math.floor(ratio / segmentsPerRow);
      var shownBigCups = Math.min(bigCupCount, maxBigCups);
      for (var b = 0; b < shownBigCups; b += 1) {
        container.appendChild(createCupSegment("big full", segmentsPerRow));
      }
      if (bigCupCount > maxBigCups) {
        var more = document.createElement("span");
        more.className = "cup-segment-more";
        more.textContent = "+" + (ratio - maxBigCups * segmentsPerRow).toFixed(1);
        container.appendChild(more);
        return;
      }
      var remaining = ratio - bigCupCount * segmentsPerRow;
      var fullCount = Math.floor(remaining);
      var remainder = remaining - fullCount;
      for (var i = 0; i < fullCount; i += 1) {
        container.appendChild(createCupSegment("full"));
      }
      if (remainder > 0) {
        var partial = createCupSegment("partial");
        partial.style.setProperty("--fill", Math.round(remainder * 100) + "%");
        container.appendChild(partial);
      }
    }

    // Sensibilisierungs-Ansicht: nur noch die Tassen-Segmentreihe fuer die "was waere bei 500
    // Anfragen"-Hochrechnung, siehe REQUEST_MULTIPLIER oben -- bewusst ohne Absolutwert-/Bruch-Text
    // ("auf die exakten Werte verzichten"), Metrik-Zuordnung laeuft ueber die gemeinsame Legende
    // unter der Tassen-Kachel statt einer Beschriftung pro Zeile.
    function updateProjectedMetric(segmentsId, value, reference) {
      var ratio = reference > 0 ? (value * REQUEST_MULTIPLIER) / reference : 0;
      renderCupSegments(segmentsId, ratio);
    }

    function recordUsage(data) {
      cumulativeCost += data.actual_cost || 0;
      cumulativeInputTokens += data.input_tokens || 0;
      cumulativeOutputTokens += data.output_tokens || 0;
      cumulativeCo2 += data.sustainability ? data.sustainability.co2_grams || 0 : 0;
      cumulativeEnergy += data.sustainability ? data.sustainability.energy_wh || 0 : 0;
      if (data.sustainability && data.sustainability.water_ml != null) cumulativeWater += data.sustainability.water_ml;
      else if (data.sustainability) cumulativeWaterAvailable = false;
      lastCostCurrency = data.cost_currency || lastCostCurrency;
      var symbol = currencySymbol(lastCostCurrency);
      element("#chat-turn-cost").textContent = symbol + " " + (data.actual_cost || 0).toFixed(6);
      element("#chat-input-tokens").textContent = data.input_tokens || 0;
      element("#chat-output-tokens").textContent = data.output_tokens || 0;
      element("#chat-input-cost").textContent = symbol + " " + (data.input_cost || 0).toFixed(6);
      element("#chat-output-cost").textContent = symbol + " " + (data.output_cost || 0).toFixed(6);
      element("#chat-total-cost").textContent = symbol + " " + cumulativeCost.toFixed(6);
      element("#chat-total-tokens").textContent = cumulativeInputTokens + cumulativeOutputTokens;
      element("#chat-eco-indicator").textContent = "Letzte Runde: " + ecoIndicatorLabel(data.sustainability);
      element("#chat-eco-water").textContent = cumulativeWaterAvailable ? cumulativeWater.toFixed(4) + " mL" : "–";
      element("#chat-eco-co2").textContent = cumulativeCo2.toFixed(4) + " g";
      element("#chat-eco-energy").textContent = cumulativeEnergy.toFixed(4) + " Wh";
      updateRing("#ring-co2", TEA_CUP_CO2_G > 0 ? cumulativeCo2 / TEA_CUP_CO2_G : 0);
      updateRing("#ring-energy", TEA_CUP_ENERGY_WH > 0 ? cumulativeEnergy / TEA_CUP_ENERGY_WH : 0);
      updateRing("#ring-water", TEA_CUP_WATER_ML > 0 ? cumulativeWater / TEA_CUP_WATER_ML : 0);
      updateProjectedMetric("#chat-500x-water-segments", cumulativeWater, TEA_CUP_WATER_ML);
      updateProjectedMetric("#chat-500x-co2-segments", cumulativeCo2, TEA_CUP_CO2_G);
      updateProjectedMetric("#chat-500x-energy-segments", cumulativeEnergy, TEA_CUP_ENERGY_WH);
    }

    async function continueChat() {
      var input = element("#chat-input");
      var content = input.value.trim();
      if (!content) { toast("Bitte eine Nachricht eingeben."); return; }
      var selected = providers.find(function (p) { return String(p.id) === element("#provider").value; });
      if (!selected) { toast("Bitte einen Provider auswählen."); return; }
      var button = element("#chat-send");
      button.disabled = true;
      conversation.push({role: "user", content: content});
      appendChatMessage("user", content);
      try {
        var data = await api("/api/send", {method: "POST", body: JSON.stringify({prompt: content, messages: conversation, provider_id: selected.id, model_name: modelSelect.value, override_reason: element("#override").value})});
        conversation.push({role: "assistant", content: data.answer});
        appendChatMessage("assistant", data.answer, data.actual_cost, data.cost_currency);
        recordUsage(data);
        input.value = "";
        element("#chat-estimate-result").textContent = "";
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
      if (last.recommendation.model_id.indexOf("haiku") !== -1 && modelSelect.value.indexOf("sonnet") !== -1) {
        warning.textContent = "Hinweis: Die lokale Analyse hält Claude Haiku 4.5 für ausreichend. Claude Sonnet 4.6 ist auswählbar, verursacht für diese Anfrage aber voraussichtlich unnötig höhere Kosten.";
        warning.hidden = false;
      }
      refreshTilesForSelectedProvider(selected);
    }

    async function refreshTilesForSelectedProvider(selected) {
      // Kacheln bisher nur bei der urspruenglich empfohlenen Modellklasse korrekt (aus
      // analyze()/refreshFootprint()) -- wechselt der Nutzer manuell auf einen anderen
      // Provider/ein anderes Modell, sollen CO2/Energie/Wasser/Kosten dem tatsaechlich
      // gewaehlten Ziel entsprechen, nicht der Empfehlung eingefroren bleiben.
      try {
        var data = await api("/api/estimate-footprint", {method: "POST", body: JSON.stringify({
          text: prompt.value,
          provider_id: selected.id,
          model_name: modelSelect.value,
          model_class: last ? last.recommendation.model_class : null
        })});
        var costSymbol = selected.provider_type === "anthropic" ? "$" : "€";
        element("#cost").textContent = costSymbol + " " + data.estimated_cost.toFixed(6);
        renderSustainabilityTiles(data.sustainability);
        var co2Text = data.sustainability ? data.sustainability.co2_grams + " g" : "nicht verfügbar";
        element("#send-summary").textContent = "Empfehlung: " + last.recommendation.display_name + " · " + last.recommendation.hosting_region + " · Kosten " + costSymbol + data.estimated_cost.toFixed(6) + " · CO₂e " + co2Text + " · Risiko " + last.compliance.level.toUpperCase();
        if (data.sustainability_warning) toast(data.sustainability_warning);
      } catch (error) {
        // Provider evtl. noch nicht sendebereit konfiguriert -- Kacheln behalten den letzten
        // bekannten (empfehlungsbasierten) Schaetzwert, statt bei jedem Dropdown-Wechsel
        // eine Fehlermeldung zu zeigen.
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

    function ecoIndicatorLabel(sustainability) {
      // Erste Testfassung (unstyled) fuer Designvorschlag B: mode-Feld aus ecologits_service.py auswerten.
      if (!sustainability) return "Nicht verfügbar";
      if (sustainability.mode === "llm_impacts") return "EcoLogits DB";
      if (sustainability.mode === "compute_llm_impacts") return "Näherung";
      if (sustainability.mode === "local_cpu_estimate") return "Lokale CPU-Schätzung";
      if (sustainability.mode === "formula") return "Grobe Schätzung";
      return "Nicht verfügbar";
    }

    function renderSustainabilityTiles(sustainability) {
      var indicator = ecoIndicatorLabel(sustainability);
      // Indikator pro Kachel nur zeigen, wenn dieses konkrete Feld auch einen Wert hat --
      // Formel-/lokale-CPU-Schaetzung liefern nie Wasser/ADPe, "Grobe Schaetzung" neben "–"
      // waere dort irrefuehrend (suggeriert einen Schaetzwert, den es nicht gibt).
      function indicatorFor(value) { return value != null ? indicator : "Nicht verfügbar"; }
      element("#co2").textContent = sustainability && sustainability.co2_grams != null ? sustainability.co2_grams + " g" : "–";
      element("#co2-indicator").textContent = indicatorFor(sustainability && sustainability.co2_grams);
      element("#energy").textContent = sustainability && sustainability.energy_wh != null ? sustainability.energy_wh + " Wh" : "–";
      element("#energy-indicator").textContent = indicatorFor(sustainability && sustainability.energy_wh);
      element("#water").textContent = sustainability && sustainability.water_ml != null ? sustainability.water_ml + " mL" : "–";
      element("#water-indicator").textContent = indicatorFor(sustainability && sustainability.water_ml);
      element("#adpe").textContent = sustainability && sustainability.adpe_ug_sb_eq != null ? sustainability.adpe_ug_sb_eq + " µg Sb-Äq." : "–";
      element("#adpe-indicator").textContent = indicatorFor(sustainability && sustainability.adpe_ug_sb_eq);
    }

    function render(data) {
      last = data;
      element("#footprint-basis").textContent = "Basis: Originalprompt";
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
      var costSymbol = data.recommendation.provider === "Anthropic" ? "$" : "€";
      element("#send-summary").textContent = "Empfehlung: " + data.recommendation.display_name + " · " + data.recommendation.hosting_region + " · Kosten " + costSymbol + data.estimated_cost.toFixed(6) + " · CO₂e " + data.sustainability.co2_grams + " g · Risiko " + data.compliance.level.toUpperCase();
      // Provider-Dropdown passend zur tatsaechlichen Empfehlung vorbelegen, nicht blind auf
      // Anthropic setzen -- sonst landet eine "lokal"-Empfehlung trotzdem beim Cloud-Versand.
      var recommendedProviderType = data.recommendation.provider === "Ollama" ? "ollama"
        : data.recommendation.provider === "Anthropic" ? "anthropic"
        : null;
      var recommended = recommendedProviderType && providers.find(function (p) { return p.enabled && p.provider_type === recommendedProviderType; });
      if (recommended) {
        element("#provider").value = String(recommended.id);
        if (recommendedProviderType === "anthropic") {
          modelSelect.value = data.recommendation.model_id.indexOf("sonnet") !== -1
            ? "claude-sonnet-4-6"
            : "claude-haiku-4-5-20251001";
        }
      } else {
        // Kein zur Empfehlung passender Provider konfiguriert -- eine evtl. noch von einer
        // frueheren (Cloud-)Analyse stehengebliebene Auswahl darf hier nicht weiterleben,
        // sonst sendet "bewusst senden" trotz lokaler Empfehlung stillschweigend extern.
        element("#provider").value = "";
      }
      selectedProviderEstimate();
      var warnings = [data.warning, data.sustainability_warning].filter(Boolean);
      if (warnings.length) toast(warnings.join(" "));
      syncSend();
      saveState();
    }

    async function refreshFootprint() {
      if (!last) return;
      try {
        var data = await api("/api/estimate-footprint", {method: "POST", body: JSON.stringify({
          text: prompt.value,
          model_class: last.recommendation.model_class,
          complexity_score: last.analysis.complexity_score
        })});
        last.input_tokens = data.input_tokens;
        last.expected_output_tokens = data.expected_output_tokens;
        last.estimated_cost = data.estimated_cost;
        last.duration = data.duration;
        last.sustainability = data.sustainability;
        last.sustainability_warning = data.sustainability_warning;
        element("#footprint-basis").textContent = "Basis: Optimierter Prompt";
        renderSustainabilityTiles(data.sustainability);
        element("#cost").textContent = (last.recommendation.provider === "Anthropic" ? "$ " : "€ ") + data.estimated_cost.toFixed(6);
        element("#duration").textContent = data.duration.min_seconds + "–" + data.duration.max_seconds + " s";
        var costSymbol = last.recommendation.provider === "Anthropic" ? "$" : "€";
        element("#send-summary").textContent = "Empfehlung: " + last.recommendation.display_name + " · " + last.recommendation.hosting_region + " · Kosten " + costSymbol + data.estimated_cost.toFixed(6) + " · CO₂e " + data.sustainability.co2_grams + " g · Risiko " + last.compliance.level.toUpperCase();
        selectedProviderEstimate();
        if (data.sustainability_warning) toast(data.sustainability_warning);
      } catch (error) {
        toast(error.message);
      }
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

    prompt.addEventListener("input", function () { updateCounter(); saveState(); });
    updateCounter();
    analyzeButton.addEventListener("click", analyze);
    element("#use-optimized").addEventListener("click", function () {
      prompt.value = element("#optimized").value;
      updateCounter();
      saveState();
      refreshFootprint();
    });
    // Manche Browser stellen Checkbox-Zustaende ueber Neuladen/Neustart hinweg wieder her --
    // diese Checkbox ist eine bewusste Versand-Bestaetigung und darf nie vorausgefuellt sein.
    element("#confirm").checked = false;
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
        cumulativeEnergy = 0;
        cumulativeWater = 0;
        cumulativeWaterAvailable = true;
        lastCostCurrency = "EUR";
        element("#answer").style.display = "block";
        element("#answer").textContent = "Verwendetes Modell: " + (data.model_used || "unbekannt");
        appendChatMessage("user", prompt.value);
        appendChatMessage("assistant", data.answer, data.actual_cost, data.cost_currency);
        recordUsage(data);
        if (element("#discard").checked) { prompt.value = ""; element("#optimized").value = ""; updateCounter(); saveState(); }
        var summary = "Antwort erhalten mit " + (data.model_used || "dem gewählten Modell") + " (" + data.latency_ms + " ms). ";
        if (data.actual_cost != null) {
          element("#cost").textContent = (data.cost_currency === "USD" ? "$ " : "€ ") + data.actual_cost.toFixed(6);
          summary += "Berechnete Kosten " + data.actual_cost.toFixed(6) + " " + data.cost_currency + ". ";
        }
        if (data.sustainability) summary += "Tatsächliches CO₂e " + data.sustainability.co2_grams + " g. ";
        toast(summary + (data.sustainability_warning || ""));
      } catch (error) { toast(error.message); }
    }

    loadProviders().then(restoreState).catch(function (error) { toast(error.message); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
