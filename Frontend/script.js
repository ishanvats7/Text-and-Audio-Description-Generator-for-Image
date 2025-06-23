const API_URL = 'http://127.0.0.1:5000';  // Change this to your deployed backend URL if needed

const dropbox = document.getElementById('dropbox');
const imageInput = document.getElementById('imageInput');
const captionBox = document.getElementById('caption');
const preview = document.getElementById('preview');

// Drag-and-drop support
dropbox.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropbox.classList.add('dragover');
});

dropbox.addEventListener('dragleave', () => {
  dropbox.classList.remove('dragover');
});

dropbox.addEventListener('drop', (e) => {
  e.preventDefault();
  dropbox.classList.remove('dragover');

  const files = e.dataTransfer.files;
  if (files.length > 0 && files[0].type.startsWith('image/')) {
    imageInput.files = files;
    previewImage(files[0]);
  } else {
    alert("Please drop a valid image file.");
  }
});

imageInput.addEventListener('change', () => {
  if (imageInput.files.length > 0) {
    previewImage(imageInput.files[0]);
  }
});

function previewImage(file) {
  const reader = new FileReader();
  reader.onload = function (e) {
    preview.src = e.target.result;
    preview.style.display = 'block';
  };
  reader.readAsDataURL(file);
}

async function uploadImage() {
  if (imageInput.files.length === 0) {
    alert("Please select an image first");
    return;
  }

  captionBox.value = "Generating caption...";

  const formData = new FormData();
  formData.append('image', imageInput.files[0]);

  try {
    const response = await fetch(`${API_URL}/generate-caption`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.caption) {
      captionBox.value = data.caption;
      playCaptionAudio(data.caption);
    } else {
      captionBox.value = "No caption returned from server.";
    }

  } catch (error) {
    captionBox.value = "Error generating caption: " + error.message;
  }
}

async function playCaptionAudio(caption) {
  try {
    const response = await fetch(`${API_URL}/speak-caption`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ caption }),
    });

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

    const audioBlob = await response.blob();
    const audioUrl = URL.createObjectURL(audioBlob);

    const audio = new Audio(audioUrl);
    audio.play();

  } catch (error) {
    console.error("Error playing audio:", error);
  }
}
