# MPC Plus - Frontend

The web interface for **MPC Plus**, a Machine Performance Check system designed for radiation therapy quality assurance. This project is an open-source initiative by **TCU Computer Science** students in collaboration with **The Center for Cancer and Blood Disorders**.

## Overview

MPC Plus provides a modern, intuitive dashboard for medical physicists to monitor the performance of linear accelerators. It visualizes daily check results, highlights anomalies, and generates compliance reports.

## 🚀 Key Features

*   **Dashboard**: At-a-glance view of machine status and latest updates.
*   **Visual Analytics**: Interactive graphs and charts (powered by **Recharts**) to track performance trends over time.
*   **Machine Management**: Configure machine details and settings.
*   **Detailed Results**: Drill down into specific beam metrics (Output, Uniformity, Symmetry).
*   **Report Generation**: Request and download PDF compliance reports.

## 🛠️ Technology Stack

*   **Framework**: [Next.js 16](https://nextjs.org/) (App Router)
*   **Language**: TypeScript
*   **Styling**: [Tailwind CSS](https://tailwindcss.com/)
*   **UI Components**: [Radix UI](https://www.radix-ui.com/) / [Lucide React](https://lucide.dev/)
*   **Charts**: [Recharts](https://recharts.org/)

## � Database Schema

For detailed database schema documentation, see the [Backend Schema](../../backend/MPC-Plus/DATABASE_SCHEMA.md).

## �📦 Getting Started

For full local deployment instructions, please refer to the [DEPLOYMENT.md](../../DEPLOYMENT.md) guide in the root directory.

### Prerequisites

*   Node.js 18+
*   npm / yarn / pnpm

### Configuration

Copy `.env.local.example` to `.env.local`:

```bash
cp .env.local.example .env.local
```

### Running Locally

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser.

## 👥 Contributors

**Frontend / Full Stack Team:**
*   **Sameep Shah**
*   **Alex Morales**

**Backend Team:**
*   **Brae Ogle**
*   **Alex Lee**
*   **Madhavam Shahi**
*   **Tristan Gonzales**

## 📄 License

This project is open source.
