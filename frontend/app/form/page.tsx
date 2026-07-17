"use client";
import { useRouter } from "next/navigation";
import Button from "@/components/ui/button";
import Form from "react-bootstrap/Form";
import Collapse from "react-bootstrap/Collapse";
import { useState, ChangeEvent } from "react";
import { uploadStepFile, uploadStlFile } from "@/lib/api/uploads";

type ItemObject = {
  length: number;
  width: number;
  height: number;
};

type UploadResult = {
  file_id: string;
  file_url: string;
  stl_file: string;
  item: ItemObject;
};

export default function FormPage() {
  const router = useRouter();

  const [formData, setFormData] = useState({
    itemQuantity: "",
    itemWeight: "1",
    layerRequired: false,
    layerType: "Keine",
    bulkGoods: false,
    scalable: false,
    scaled_length: "",
  });
  const [errors, setErrors] = useState({
    file: "",
    itemQuantity: "",
    itemWeight: "",
    scaled_length: "",
  });
  const [isBulkGood, setIsBulkGood] = useState<boolean>(false);
  const [cadFileUploaded, setCadFileUploaded] = useState(false);
  const [uploadedItem, setUploadedItem] = useState<ItemObject | null>(null);
  const [uploadedStlFile, setUploadedStlFile] = useState("");
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationError, setSimulationError] = useState("");

  const handleBulkGoodChange = (event: ChangeEvent<HTMLInputElement>) => {
    const checked = event.target.checked;

    setIsBulkGood(checked);

    setFormData((prev) => ({
      ...prev,
      bulkGoods: checked,
    }));
  };

  //Hochladen der CAD-Datei
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];

    if (!file) {
      setCadFileUploaded(false);
      setUploadedItem(null);
      setUploadedStlFile("");
      return;
    }

    //Validation
    const fileName = file.name.toLowerCase();
    const isValidFile =
      (fileName.endsWith(".stp") || fileName.endsWith(".stl")) &&
      fileName !== "";

    if (!isValidFile) {
      setCadFileUploaded(false);

      setErrors((prev) => ({
        ...prev,
        file: "Bitte laden Sie nur eine Datei im Step- oder STL-Format hoch!",
      }));

      return;
    }

    setErrors((prev) => ({
      ...prev,
      file: "",
    }));

    try {
      const uploadResult: UploadResult = fileName.endsWith(".stp")
        ? await uploadStepFile(file)
        : await uploadStlFile(file);

      setUploadedItem(uploadResult.item);
      setUploadedStlFile(uploadResult.stl_file);
      localStorage.setItem("convertedStlUrl", uploadResult.file_url);

      setCadFileUploaded(true);
    } catch (error) {
      setCadFileUploaded(false);
      setUploadedItem(null);
      setUploadedStlFile("");

      setErrors((prev) => ({
        ...prev,
        file: "Datei konnte nicht verarbeitet werden.",
      }));
    }
  };

  const runSimulation = async () => {
    if (!uploadedItem) {
      setSimulationError("Kein Artikelobjekt vorhanden.");
      return;
    }

    setIsSimulating(true);
    setSimulationError("");

    try {
      const item = {
        ...uploadedItem,
        length:
          formData.scalable && Number(formData.scaled_length) > 0
            ? Number(formData.scaled_length)
            : uploadedItem.length,
        // Gewicht in Gramm -- das Backend leitet die Masse (kg) daraus ab
        weight: Number(formData.itemWeight),
      };

      const payload = {
        item: item,
        item_quantity: Number(formData.itemQuantity),
        boxes:[],
        stl_file: uploadedStlFile,
        mesh_scale: [0.001, 0.001, 0.001],
      };

      const response = await fetch("http://localhost:8000/simulation/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);

        throw new Error(
          errorData?.detail ?? "Simulation konnte nicht durchgeführt werden."
        );
      }

      const result = await response.json();

      localStorage.setItem("simulationResult", JSON.stringify(result));

      router.push("/simulation-results");

      console.log(result);
    } catch (error) {
      setSimulationError(
        error instanceof Error
          ? error.message
          : "Simulation konnte nicht durchgeführt werden."
      );
    } finally {
      setIsSimulating(false);
    }
  };

  //Input Validations

  const validateForm = () => {
    const newErrors = {
      file: "",
      itemQuantity: "",
      itemWeight: "",
      scaled_length: "",
    };

    if (!cadFileUploaded) {
      newErrors.file = "Bitte laden Sie eine CAD-Datei hoch.";
    }

    if (!formData.itemQuantity || Number(formData.itemQuantity) <= 0) {
      newErrors.itemQuantity =
        "Bitte geben Sie eine gültige Anzahl an Artikeln an.";
    }
    if (!formData.itemWeight || Number(formData.itemWeight) <= 0) {
      newErrors.itemWeight = "Bitte geben Sie ein gültiges Gewicht an.";
    }

    if (
      formData.scalable &&
      (!formData.scaled_length || Number(formData.scaled_length) <= 0)
    ) {
      newErrors.scaled_length = "Bitte geben Sie eine gültige Länge an.";
    }

    setErrors(newErrors);

    //Fehler vorhanden entspricht false
    return !Object.values(newErrors).some(Boolean);
  };

  //Seite verlassen
  const handleRender = async () => {
    const isValid = validateForm();
    if (!isValid) return;

    localStorage.setItem("itemQuantity", formData.itemQuantity);
    localStorage.setItem("itemWeight", formData.itemWeight);
    localStorage.setItem("layerStorage", formData.layerType);
    localStorage.setItem("bulkGoods", String(formData.bulkGoods));
    localStorage.setItem("scaled_length", formData.scaled_length);

    if (formData.bulkGoods) {
      await runSimulation();
      return;
    }

    if (!isBulkGood) {
      router.push("/rendering");
    }
  };

  return (
    <main>
      <div>
        <h2>Bitte Artikel-Informationen eingeben:</h2>

        {/* CAD Datei hochladen */}
        <Form>
          <Form.Group controlId="cadFile" className="mb-3">
            <Form.Label>CAD-Datei hochladen:</Form.Label>
            <Form.Control
              type="file"
              accept=".step,.stp,.iges,.igs,.stl,.obj*"
              onChange={handleFileChange}
              style={{ width: "700px" }}
            />
          </Form.Group>
          {/*Validation der Datei*/}
          {errors.file && (
            <span
              style={{
                color: "#991b1b",
                backgroundColor: "#fee2e2",
                border: "1px solid #fca5a5",
                borderRadius: "9999px",
                padding: "6px 12px",
                fontSize: "14px",
                fontWeight: 600,
                marginTop: "6px",
                marginBottom: "6px",
              }}
            >
              {errors.file}
            </span>
          )}

          {/* Artikelanzahl definieren */}
          <Form.Group
            className="mb-3"
            controlId="itemQuantity"
            style={{ marginTop: "6px" }}
          >
            <Form.Label>Anzahl an Artikeln pro Verpackung</Form.Label>
            <div
              style={{
                display: "flex",
                alignItems: "center",
              }}
            >
              <Form.Control
                type="number"
                value={formData.itemQuantity}
                placeholder="1"
                style={{ width: "700px" }}
                onChange={(e) => {
                  const value = e.target.value;
                  setFormData((prev) => ({
                    ...prev,
                    itemQuantity: value,
                  }));
                }}
              />
              <span style={{ color: "#888", marginLeft: "5px" }}>
                pro Verpackung
              </span>
            </div>
          </Form.Group>
          {/*Validation der Artikelanzahl*/}
          {errors.itemQuantity && (
            <span
              style={{
                color: "#991b1b",
                backgroundColor: "#fee2e2",
                border: "1px solid #fca5a5",
                borderRadius: "9999px",
                padding: "6px 12px",
                fontSize: "14px",
                fontWeight: 600,
                marginTop: "6px",
                marginBottom: "6px",
              }}
            >
              {errors.itemQuantity}
            </span>
          )}

          {/* Artikelgewicht definieren */}
          <Form.Group
            className="mb-3"
            controlId="itemweight"
            style={{ marginTop: "12px" }}
          >
            <Form.Label>Artikelgewicht:</Form.Label>
            <div
              style={{
                display: "flex",
                alignItems: "center",
              }}
            >
              <Form.Control
                type="number"
                value={formData.itemWeight}
                style={{ width: "700px" }}
                onChange={(e) => {
                  const value = e.target.value;
                  setFormData((prev) => ({
                    ...prev,
                    itemWeight: value,
                  }));
                }}
              />
              <span style={{ color: "#888", marginLeft: "5px" }}>Gramm</span>
            </div>
          </Form.Group>
          {/*Validation des Artikelgewichts*/}
          {errors.itemWeight && (
            <span
              style={{
                color: "#991b1b",
                backgroundColor: "#fee2e2",
                border: "1px solid #fca5a5",
                borderRadius: "9999px",
                padding: "6px 12px",
                fontSize: "14px",
                fontWeight: 600,
                marginTop: "6px",
                marginBottom: "6px",
              }}
            >
              {errors.itemWeight}
            </span>
          )}

          {/* Zwischenlagen */}
          <Form.Group
            className="mb-3"
            controlId="seperationlayer"
            style={{ marginTop: "12px" }}
          >
            <Form.Label>
              Werden Papplagen zwischen den Artikellagen benötigt?
            </Form.Label>
            <Form.Check
              type="checkbox"
              id="default-checkbox"
              label="Zwischenlagen benötigt"
              onChange={(e) => {
                const checked = e.target.checked;
                setFormData((prev) => ({
                  ...prev,
                  layerRequired: checked,
                }));
                if (!checked) {
                  setFormData((prev) => ({
                    ...prev,
                    layerType: "Keine",
                  }));
                  localStorage.setItem("layerStorage", "Keine");
                }
              }}
            />
          </Form.Group>
          {/* Art der Zwischenlagen */}
          <Collapse in={formData.layerRequired}>
            <Form.Group className="mb-3" controlId="layerGroup">
              <div id="advanced-region">
                <Form.Select
                  value={formData.layerType}
                  style={{ width: "700px" }}
                  onChange={(e) => {
                    const val = e.target.value;
                    setFormData((prev) => ({
                      ...prev,
                      layerType: val,
                    }));
                    localStorage.setItem("layerStorage", val);
                  }}
                >
                  <option value="Keine">Keine Zwischenlage</option>
                  <option value="Pappe">Pappe</option>
                  <option value="Papier">Papier</option>
                  <option value="Sonstige">sonstiges</option>
                </Form.Select>
              </div>
            </Form.Group>
          </Collapse>

          {/*Schüttgut */}
          <Form.Group className="mb-3" controlId="bulkGoods">
            <Form.Label>
              Soll der Artikel als Schüttgut verpackt werden?
            </Form.Label>
            <Form.Check
              type="checkbox"
              id="bulkGoods-checkbox"
              label="Schüttgut"
              checked={formData.bulkGoods}
              onChange={handleBulkGoodChange}
            />
          </Form.Group>

          {/* Skalierung */}
          <Form.Group
            className="mb-3"
            controlId="scaling"
            style={{ marginTop: "12px" }}
          >
            <Form.Label>
              Hat der Artikel eine andere Polzahl als die CAD-Datei?
            </Form.Label>
            <Form.Check
              type="checkbox"
              id="scale-checkbox"
              label="Der Artikel hat eine andere Länge"
              onChange={(e) => {
                const checked = e.target.checked;
                setFormData((prev) => ({
                  ...prev,
                  scalable: checked,
                }));
                if (!checked) {
                  setFormData((prev) => ({
                    ...prev,
                    scaled_length: "0",
                  }));
                  localStorage.setItem("scaled_length", "0");
                }
              }}
            />
          </Form.Group>
          {/* Neue Länge des Artikel eingeben */}
          <Collapse in={formData.scalable}>
            <Form.Group className="mb-3" controlId="scaledLength">
              <div
                id="scale-region"
                style={{
                  alignItems: "center",
                  gap: "6px",
                  display: "flex",
                }}
              >
                <Form.Control
                  type="number"
                  value={formData.scaled_length}
                  style={{
                    width: "700px",
                  }}
                  onChange={(e) => {
                    const val = e.target.value;
                    setFormData((prev) => ({
                      ...prev,
                      scaled_length: val,
                    }));

                    localStorage.setItem("scaled_length", val);
                    validateForm();
                  }}
                />
                <span style={{ color: "#888" }}>mm</span>
              </div>
            </Form.Group>
          </Collapse>
        </Form>
        <br></br>
        <Button variant="primary" onClick={handleRender} disabled={isSimulating}>
          {isSimulating ? (
            <>
              <span
                className="spinner-border spinner-border-sm"
                role="status"
                aria-hidden="true"
                style={{ marginRight: "8px" }}
              />
              Simulation läuft...
            </>
          ) : (
            "Rendern"
          )}
        </Button>
        {simulationError && (
          <p
            style={{
              color: "#991b1b",
              backgroundColor: "#fee2e2",
              border: "1px solid #fca5a5",
              borderRadius: "8px",
              padding: "8px 12px",
              marginTop: "12px",
              fontWeight: 600,
            }}
          >
            {simulationError}
          </p>
        )}
      </div>
    </main>
  );
}
