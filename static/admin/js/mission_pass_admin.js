document.addEventListener('DOMContentLoaded', function() {
  function initEditor(textarea) {
    if (!textarea || textarea.dataset.quillInit) return;
    textarea.dataset.quillInit = '1';

    // create container for quill
    var container = document.createElement('div');
    container.className = 'quill-container';
    textarea.style.display = 'none';
    textarea.parentNode.insertBefore(container, textarea.nextSibling);

    var quill = new Quill(container, {
      theme: 'snow',
      modules: {
        toolbar: [
          ['bold', 'italic', 'underline', 'strike'],
          ['blockquote', 'code-block'],
          [{ 'header': 1 }, { 'header': 2 }],
          [{ 'list': 'ordered'}, { 'list': 'bullet' }],
          ['link', 'image'],
        ],
        clipboard: {
          matchVisual: false,
        }
      }
    });

    // initialize from textarea
    try { quill.root.innerHTML = textarea.value || ''; } catch (e) { /* ignore */ }

    // sync on submit
    var form = textarea.closest('form');
    if (form) {
      form.addEventListener('submit', function() {
        textarea.value = quill.root.innerHTML;
      });
    }
  }

  function scan() {
    var t = document.querySelectorAll('textarea[name$="-content"], textarea[name="content"]');
    t.forEach(initEditor);
  }

  scan();

  // watch for dynamic inlines added by admin
  var observer = new MutationObserver(function() { scan(); });
  observer.observe(document.body, { childList: true, subtree: true });
});
