# 🎨 MPC-Plus Frontend Dashboard

The user-facing dashboard for **MPC-Plus**, providing medical physicists with a modern, intuitive interface for monitoring machine performance and generating compliance reports.

---

## 🚀 Key Features

-   **Real-Time Monitoring**: At-a-glance status of all linear accelerators in the facility.
-   **Visual Analytics**: Interactive trend analysis powered by **Recharts**, allowing physicists to spot drift before it exceeds clinical thresholds.
-   **Threshold Management**: Granular control over passing, warning, and failing limits for every energy variant.
-   **Professional Reporting**: Integrated PDF export workflow for monthly and annual QA reviews.
-   **Machine Administration**: Easy configuration of machine properties, energy variants, and facility-wide settings (like Timezone).

---

## 🛠 Tech Stack & Patterns

### 1. Modern Foundation
-   **Framework**: **Next.js 16** (utilizing the latest **App Router** features).
-   **Library**: **React 19** (concurrent rendering, server components).
-   **Language**: **TypeScript** for end-to-end type safety.

### 2. Design System
-   **Styling**: **Tailwind CSS 4.0** for a high-performance, utility-first UI.
-   **Primitives**: **Radix UI** for accessible, headless components (Dialogs, Selects, Popovers).
-   **Icons**: **Lucide React** for a clean, consistent medical aesthetic.

### 3. Data Integration
-   **API Client**: A centralized `lib/api.ts` handles all communication with the .NET backend.
-   **Normalization**: The frontend implements a transformation layer to handle the mapping between PostgreSQL's `snake_case` and the frontend's `camelCase` conventions.
-   **Optimization**: Implements aggressive caching strategies and "no-store" fetches where real-time accuracy is paramount.

---

## 🚀 Getting Started (Development)

While we recommend running the full stack via **Docker Compose** from the root directory, you can also run the frontend independently for development.

### Prerequisites
-   [Node.js 20+](https://nodejs.org/)
-   `npm` or `yarn`

### Installation
1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Configure your environment variables in a `.env` file (see the root `.env.example`).
4.  Launch the development server:
    ```bash
    npm run dev
    ```
The dashboard will be available at `http://localhost:3000`.

---

## 📁 Directory Structure

-   `app/`: Next.js App Router pages and layouts.
-   `components/`: Reusable UI components (buttons, cards, charts).
-   `lib/`: Core utilities, API clients, and data transformers.
-   `models/`: TypeScript interfaces mirroring the backend data structures.
-   `constants/`: Global application constants and configuration values.

---

## ⚖️ License

MPC-Plus is open-source software. Please refer to the LICENSE file in the project root for details.
