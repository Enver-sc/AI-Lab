(function () {
  "use strict";

  function applyPreset() {
    var type = document.querySelector("#provider-type");
    var model = document.querySelector("#model-name");
    var modelField = document.querySelector("#model-name-field");
    if (!type || !model || !modelField) return;

    modelField.style.display = type.value === "anthropic" ? "none" : "";
    if (type.value !== "anthropic") return;

    document.querySelector("#base-url").value = "https://api.anthropic.com";
    document.querySelector("#hosting-region").value = "Global";
    document.querySelector("#eco-provider").value = "anthropic";
    model.value = "claude-haiku-4-5-20251001";
    document.querySelector("#input-cost").value = "1";
    document.querySelector("#output-cost").value = "5";
    document.querySelector("#context-window").value = "200000";
  }

  document.querySelector("#provider-type").addEventListener("change", applyPreset);
  document.querySelector("#provider-form").addEventListener("reset", function () {
    window.setTimeout(applyPreset, 0);
  });
  document.querySelector("#provider-list").addEventListener("click", function () {
    window.setTimeout(applyPreset, 0);
  });
  applyPreset();
})();
