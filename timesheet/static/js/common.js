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

function handleModalFormSubmit(modalContent, url, closeFn, successCallback) {
    const form = modalContent.querySelector('form');
    if (!form) return;

    // Use a flag to avoid multiple listeners if re-attached
    if (form.dataset.ajaxAttached) return;
    form.dataset.ajaxAttached = "true";

    form.addEventListener('submit', function(e) {
        // If it's a full page view (no modal-container visible), let it submit normally
        const isModal = !!document.getElementById('modal-container').offsetParent;
        if (!isModal || form.getAttribute('data-ajax') === 'false') return;

        e.preventDefault();
        const formData = new FormData(form);
        const actionUrl = form.getAttribute('action') || url;

        fetch(actionUrl, {
            method: form.method || 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(res => {
            const contentType = res.headers.get('content-type');
            if (res.ok && contentType && contentType.includes('application/json')) {
                return res.json().then(data => ({ json: data, ok: res.ok }));
            }
            return res.text().then(text => ({ text: text, ok: res.ok }));
        })
        .then(result => {
            if (result.ok && result.json && result.json.success) {
                if (successCallback) {
                    successCallback(result.json);
                } else {
                    closeFn();
                    window.location.reload();
                }
            } else if (result.ok && result.text && !result.text.includes('invalid-feedback')) {
                // If it's HTML but doesn't have errors, assume success if not otherwise specified
                closeFn();
                window.location.reload();
            } else {
                // Re-render form with errors
                modalContent.innerHTML = result.text || "";
                handleModalFormSubmit(modalContent, url, closeFn, successCallback);

                // Re-dispatch event for dynamic field logic
                const eventName = modalContent.id === 'modal-content' ? 'modalContentLoaded' : 'modal2ContentLoaded';
                const event = new CustomEvent(eventName, { detail: { url: url, content: modalContent } });
                document.dispatchEvent(event);
            }
        })
        .catch(err => console.error("Modal submission error:", err));
    });
}

function openModal(url) {
    const modalUrl = url.includes('?') ? `${url}&modal=1` : `${url}?modal=1`;
    fetch(modalUrl, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.text())
    .then(html => {
        const modalContent = document.getElementById('modal-content');
        modalContent.innerHTML = html;
        document.getElementById('modal-container').classList.remove('hidden');
        document.body.classList.add('overflow-hidden');

        handleModalFormSubmit(modalContent, url, closeModal);

        const event = new CustomEvent('modalContentLoaded', { detail: { url: url, content: modalContent } });
        document.dispatchEvent(event);
    });
}

function closeModal() {
    document.getElementById('modal-container').classList.add('hidden');
    document.body.classList.remove('overflow-hidden');
}

function openModal2(url, successCallback) {
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

        handleModalFormSubmit(modalContent2, url, closeModal2, successCallback);

        const event = new CustomEvent('modal2ContentLoaded', { detail: { url: url, content: modalContent2 } });
        document.dispatchEvent(event);
    });
}

function closeModal2() {
    document.getElementById('modal-container-2').classList.add('hidden');
    document.body.classList.remove('overflow-hidden');
}
