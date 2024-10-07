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
            <textarea id="paragraph-${contentCount}" name="paragraph-${contentCount}" maxlength="15000" rows="4" required></textarea>
            <input type="hidden" name="order-paragraph-${contentCount}" value="${contentCount}">
            <button type="button" class="btn-remove" onclick="this.parentElement.remove()">Remover</button>
        `;
        dynamicContentDiv.appendChild(paragraphGroup);
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