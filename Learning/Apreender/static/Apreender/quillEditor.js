window.initQuillEditor = function(editorId) {
  const editorDiv = document.getElementById(editorId);
  if (!editorDiv) return;

  const quill = new Quill('#' + editorId, {
    theme: 'snow'
  });

  const form = editorDiv.closest('form');
  if (form) {
    form.addEventListener('submit', function() {
      const hiddenInput = document.getElementById(editorId + 'Input');
      if (hiddenInput) hiddenInput.value = quill.root.innerHTML;
    });
  }
};

document.addEventListener('DOMContentLoaded', function() {
  const editorDivs = document.querySelectorAll('.quill-editor-container');
  
  editorDivs.forEach(function(editorDiv) {
    window.initQuillEditor(editorDiv.getAttribute('id'));
  });
});
