export const uploadStlFile = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("http://localhost:8000/upload-stl", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("STL-Upload fehlgeschlagen");
  }

  return response.json();
};

export const uploadStepFile = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("http://localhost:8000/convert-stp-to-stl", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Konvertierung fehlgeschlagen");
  }

  return response.json();
};
