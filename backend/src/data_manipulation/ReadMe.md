# 🚜 MPC-Plus ETL & Analysis Engine

The **ETL (Extract, Transform, Load)** layer is a core component of MPC-Plus, responsible for the automated ingestion and scientific analysis of medical physics data.

---

## 🛠 Functional Overview

This layer performs several critical tasks in a continuous, automated loop:

1.  **File Watchdog**: Monitors a specified directory (e.g., `iDrive` mount) for incoming MPC output files.
2.  **Format Agnostic Extraction**: Dynamically detects whether machine data is provided in legacy **CSV** or modern **XML** format.
3.  **Scientific Analysis**: Uses **pylinac** to process `.xim` images, performing field analysis to calculate:
    -   Flatness
    -   Symmetry
    -   Geometric offsets
4.  **Flood-Field Correction**: Applies correction algorithms to raw images, leveraging historical flood data to ensure high-fidelity analysis.
5.  **Database Synchronization**: Maps machine-generated results to the PostgreSQL schema and handles local-to-UTC timestamp normalization based on the facility's timezone settings.

---

## 📁 Project Structure

-   `file_monitoring/`: Contains the logic for the watchdog system that triggers ingestion.
-   `ETL/`: The core transformation engine.
    -   `DataProcessor.py`: The primary dispatcher for all incoming data.
    -   `image/`: Specialized logic for handling medical images via `pylinac`.
    -   `extractors/`: Modular code for parsing various file formats (CSV, XML).
-   `models/`: Python-side DTOs that mirror the medical data structure for each beam type (x-ray, electron, geometry).

---

## 🔬 Tech Stack

-   **Python 3.13**
-   **pylinac**: The industry standard for automated QA in medical physics.
-   **NumPy / SciPy / Matplotlib**: Powering the scientific computation and data visualization.
-   **PostgreSQL**: (via `psycopg2` or `SQLAlchemy`) for data persistence.

---

## 🚀 Running the ETL Layer

This service is designed to run as a background worker. In a Docker environment, it runs in its own dedicated container. 

To run it standalone:
1.  Ensure Python 3.13 is installed.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure environment variables in a root `.env` file.
4.  Launch the watchdog:
    ```bash
    # (Example entry point)
    python src/data_manipulation/main.py 
    ```

---

## ⚠️ Important Considerations

-   **Timezone Calibration**: Ensure the timezone is set correctly in the MPC-Plus web dashboard before ingesting data. This is crucial for accurate QA reporting.
-   **Storage Mounts**: The `iDrive` directory must be correctly mounted for the watchdog to detect and process incoming data.
