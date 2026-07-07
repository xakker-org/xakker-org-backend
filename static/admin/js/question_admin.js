(function () {
  function setFieldsetVisible(className, visible) {
    var nodes = document.querySelectorAll("fieldset." + className);
    nodes.forEach(function (node) {
      node.style.display = visible ? "" : "none";
    });
  }

  function updateQuestionForm() {
    var typeField = document.getElementById("id_question_type");
    if (!typeField) return;

    var value = typeField.value;
    var isClosed = value === "closed";
    var isTerminal = value === "terminal";
    var isOpen = value === "open";

    setFieldsetVisible("question-section-closed", isClosed);
    setFieldsetVisible("question-section-openterminal", isOpen || isTerminal);
    setFieldsetVisible("question-section-terminal", isTerminal);
  }

  function init() {
    var typeField = document.getElementById("id_question_type");
    if (!typeField) return;
    updateQuestionForm();
    typeField.addEventListener("change", updateQuestionForm);
    setTimeout(updateQuestionForm, 100);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
