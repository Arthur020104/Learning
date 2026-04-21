document.addEventListener('DOMContentLoaded', function () {
    const dynamicContentDiv = document.getElementById('dynamic-content');
    const addParagraphButton = document.getElementById('add-paragraph');
    const addImageButton = document.getElementById('add-image');
    let contentCount = 0;

    // Função para adicionar um parágrafo
    addParagraphButton.addEventListener('click', function () {
        contentCount++;
        const paragraphGroup = document.createElement('div');
        paragraphGroup.classList.add('input-group');
        paragraphGroup.innerHTML = `
            <label for="paragraph-${contentCount}">Parágrafo</label>
            <input type="hidden" name="paragraph-${contentCount}" id="paragraph-${contentCount}Input">
            <div id="paragraph-${contentCount}" class="quill-editor-container" rows="8"></div>
            <input type="hidden" name="order-paragraph-${contentCount}" value="${contentCount}">
            <button type="button" class="btn-remove" onclick="this.parentElement.remove()">Remover</button>
        `;
        dynamicContentDiv.appendChild(paragraphGroup);
        
        // Initialize Quill editor for the new paragraph
        if (window.initQuillEditor) {
            window.initQuillEditor("paragraph-" + contentCount);
        }
    });

    // Função para adicionar uma imagem
    addImageButton.addEventListener('click', function () {
        contentCount++;
        const imageGroup = document.createElement('div');
        imageGroup.classList.add('input-group');
        imageGroup.innerHTML = `
            <label for="image-${contentCount}">Imagem</label>
            <input type="file" id="image-${contentCount}" name="image-${contentCount}" accept=".jpg, .jpeg, .png" required>
            <input type="hidden" name="order-image-${contentCount}" value="${contentCount}">
            <button type="button" class="btn-remove" onclick="this.parentElement.remove()">Remover</button>
        `;
        dynamicContentDiv.appendChild(imageGroup);
    });
});