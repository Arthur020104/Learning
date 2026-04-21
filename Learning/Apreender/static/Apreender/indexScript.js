document.addEventListener('DOMContentLoaded', function () {
    //get all checkboxes
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    
    checkboxes.forEach(checkbox => {
        //on change save state
        checkbox.addEventListener('change', () => {
            saveCheckBoxStateToCache(checkbox);
        });

        //on load set state
        const checkboxState = localStorage.getItem(checkbox.id);
        if (checkboxState) {
            const { checked, validUntil } = JSON.parse(checkboxState);
            if (Date.now() < validUntil)
                checkbox.checked = checked;
            else 
                localStorage.removeItem(checkbox.id);
        }

    });
});

function saveCheckBoxStateToCache(checkBox)
{
    localStorage.setItem(checkBox.id, JSON.stringify({checked: checkBox.checked, validUntil: Date.now() + 24 * 60 * 60 * 1000})); 
}