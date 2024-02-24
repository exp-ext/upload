document.addEventListener('DOMContentLoaded', function () {
    const uploadButton = document.getElementById('upload-button');
    const fileInput = document.querySelector('input[type="file"]');
    const imageGrid = document.querySelector('.image-grid');

    fileInput.addEventListener('change', onFileChange);
    uploadButton.addEventListener('click', createProcess);

    let inputImages = [];

    async function createProcess() {
        const objectApp = uploadButton.dataset.app;
        const objectId = uploadButton.dataset.id;
        const imagesMeta = getImagesMeta();

        const json = {
            object_id: objectId,
            object_app: objectApp,
            images_meta: imagesMeta,
        };

        const csrfToken = document.querySelector("input[name='csrfmiddlewaretoken']").value;

        try {
            const response = await fetch('/upload/json/get-image-load-meta/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify(json),
            });

            const data = await response.json();

            if (data.success) {
                for (const image_data of data.images_response) {
                    const file = getFileByJsId(image_data.js_id);
                    if (file) {
                        await uploadFile(file, image_data, csrfToken);
                    }
                }
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    async function uploadFile(file, imageData, csrfToken) {
        const presignedUrl = imageData.url;

        try {
            const uploadResponse = await fetch(presignedUrl, {
                method: 'PUT',
                body: file,
            });

            if (uploadResponse.status === 200) {
                const json = {
                    presigned_url: imageData.url,
                    django_id: imageData.django_id,
                };

                const postResponse = await fetch('/upload/json/image-uploaded/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify(json),
                });

                if (postResponse.status === 204) {
                    changeFileStatus(imageData.js_id);
                }
            }
        } catch (error) {
            console.error('Error in uploadFile:', error);
        }
    }

    function getImagesMeta() {
        return inputImages
            .filter(image => image.file_name && !image.uploaded)
            .map(image => ({ js_id: image.js_id, file_name: image.file_name }));
    }

    function getFileByJsId(js_id) {
        const fileData = inputImages.find(image => image.js_id === js_id && !image.uploaded);
        return fileData ? fileData.file : null;
    }

    function changeFileStatus(js_id) {
        const image = inputImages.find(image => image.js_id === js_id);
        if (image) {
            image.uploaded = true;
        }
    }

    function generateUniqueId() {
        return Math.random().toString(36).substring(2, 11);
    }

    function onFileChange(e) {
        const files = e.target.files;

        for (const file of files) {
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    const img = document.createElement('img');
                    img.src = event.target.result;
                    img.className = 'preview grid-item';
                    imageGrid.appendChild(img);
                };
                reader.readAsDataURL(file);

                inputImages.push({
                    js_id: generateUniqueId(),
                    file_name: file.name,
                    file: file,
                    uploaded: false,
                });
            }
        }
    }
});
