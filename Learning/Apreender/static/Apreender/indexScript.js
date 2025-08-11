document.addEventListener('DOMContentLoaded', function () {
    //get all checkboxes
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    
    checkboxes.forEach(checkbox => {
        //on change save state
        checkbox.addEventListener('change', () => {
            saveCheckBoxStateToCache(checkbox);
        });

        //on load set state
        checkbox.checked = localStorage.getItem(checkbox.id) === 'true';

    });
});

function saveCheckBoxStateToCache(checkBox)
{
    localStorage.setItem(checkBox.id, checkBox.checked);
}