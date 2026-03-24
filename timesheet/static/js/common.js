function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("show");
}

function openModal(url) {
    alert("sjnbjbfsjs");
    const modalUrl = url.includes('?') ? `${url}&modal=1` : `${url}?modal=1`;
    fetch(modalUrl, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.text())
    .then(html => {
        const modalContent = document.getElementById('modal-content');
        modalContent.innerHTML = html;
        document.getElementById('modal-container').classList.remove('hidden');
        document.body.classList.add('overflow-hidden');

        // Trigger a custom event so other scripts can attach behavior to the new content
        const event = new CustomEvent('modalContentLoaded', { detail: { url: url, content: modalContent } });
        document.dispatchEvent(event);
    });
}

function closeModal() {
    document.getElementById('modal-container').classList.add('hidden');
    document.body.classList.remove('overflow-hidden');
}

function openModal2(url) {
    const modalUrl = url.includes('?') ? `${url}&modal=1` : `${url}?modal=1`;
    fetch(modalUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(res => res.text())
    .then(html => {
        const modalContent2 = document.getElementById('modal-content-2');
        modalContent2.innerHTML = html;

        const modal2 = document.getElementById('modal-container-2');
        modal2.classList.remove('hidden');
        modal2.style.zIndex = 9999;
        document.body.classList.add('overflow-hidden');

        // Trigger a custom event for the second modal
        const event = new CustomEvent('modal2ContentLoaded', { detail: { url: url, content: modalContent2 } });
        document.dispatchEvent(event);
    });
}

function closeModal2() {
    document.getElementById('modal-container-2').classList.add('hidden');
    document.body.classList.remove('overflow-hidden');
}
