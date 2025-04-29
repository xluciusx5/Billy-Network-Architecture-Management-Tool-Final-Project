document.addEventListener("DOMContentLoaded", function () {
    let dropArea = document.getElementById("drop-area");
    let fileElem = document.getElementById("fileElem");
    let fileLabel = document.getElementById("fileLabel");
    let fileInput = document.getElementById("fileInput");
    let uploadButton = document.getElementById("upload-button");
    let progressContainer = document.getElementById("progress-container");
    let progressBar = document.getElementById("progress-bar");

    // Drag & Drop Events
    dropArea.addEventListener("dragover", (event) => {
        event.preventDefault();
        dropArea.style.background = "rgba(255, 255, 255, 0.2)";
    });

    dropArea.addEventListener("dragleave", () => {
        dropArea.style.background = "transparent";
    });

    dropArea.addEventListener("drop", (event) => {
        event.preventDefault();
        dropArea.style.background = "transparent";

        let file = event.dataTransfer.files[0];
        handleFile(file);
    });

    // Click Upload Event
    dropArea.addEventListener("click", () => {
        fileElem.click();
    });

    fileElem.addEventListener("change", (event) => {
        let file = event.target.files[0];
        handleFile(file);
    });

    // Enable Upload Button when a file is selected
    function handleFile(file) {
        if (file) {
            fileLabel.innerHTML = `📄 ${file.name}`;
            fileInput.files = fileElem.files;
            uploadButton.disabled = false;
        }
    }

    // Simulate Progress Bar on Upload
    document.getElementById("upload-form").addEventListener("submit", (event) => {
        event.preventDefault();

        progressContainer.classList.remove("hidden");
        progressBar.style.width = "0%";

        let formData = new FormData(event.target);

        let xhr = new XMLHttpRequest();
        xhr.open("POST", "/", true);

        xhr.upload.onprogress = function (event) {
            let percent = (event.loaded / event.total) * 100;
            progressBar.style.width = percent + "%";
        };

        xhr.onload = function () {
            if (xhr.status === 200) {
                window.location.href = xhr.responseURL;
            }
        };

        xhr.send(formData);
    });
});
