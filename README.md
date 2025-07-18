# Analytics AI Dashboard

A full-stack analytics dashboard built with Next.js 15.3, React 19, Tailwind CSS, and FastAPI. Features TailAdmin-inspired design with real-time charts and Pipedream integration for business optimization.

## Features

- **📊 Interactive Charts**: Revenue over time (line chart) and expenses by category (bar chart)
- **💰 Financial Analytics**: Real-time revenue, expenses, and profit calculations
- **🏢 Office Optimization**: AI-powered office space recommendations via Pipedream integration
- **🎨 Modern UI**: TailAdmin-inspired design with Tailwind CSS
- **📱 Responsive Design**: Works seamlessly on desktop and mobile devices
- **⚡ Real-time Data**: Live updates and interactive dashboard components
- **🚀 Next.js 15.3**: Latest features including Turbopack builds and performance optimizations
- **⚛️ React 19**: Modern React features and improved performance

## Tech Stack

### Frontend

- **Next.js 15.3** - React framework with Turbopack support
- **React 19** - JavaScript library for user interfaces
- **Tailwind CSS** - Utility-first CSS framework
- **ApexCharts** - Professional charting library
- **Axios** - Promise-based HTTP client
- **Lucide React** - Beautiful SVG icons
- **TypeScript** - Type-safe JavaScript

### Backend

- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation using Python type hints
- **HTTPX** - Async HTTP client for Python
- **Uvicorn** - ASGI server for FastAPI

### Integrations

- **Pipedream** - Serverless integration platform for business automation
- **TailAdmin** - Premium Tailwind CSS admin template design system

## Project Structure

```
Analytics_AI_Dashboard/
├── frontend/
│   ├── components/
│   │   └── analytics/
│   │       ├── StatsCard.tsx       # Modular stats card component
│   │       ├── RevenueChart.tsx    # Revenue chart component
│   │       ├── ExpensesChart.tsx   # Expenses chart component
│   │       ├── BusinessOptimization.tsx # Business optimization module
│   │       └── index.ts            # Component exports
│   ├── examples/
│   │   └── analytics-modules-usage.tsx # Usage examples
│   ├── pages/
│   │   ├── _app.tsx                # Next.js app configuration
│   │   └── index.tsx               # Main dashboard page
│   ├── styles/
│   │   └── globals.css             # Global styles with Tailwind
│   ├── package.json                # Frontend dependencies
│   ├── next.config.js              # Next.js 15.3 configuration
│   ├── tailwind.config.js          # Tailwind CSS configuration
│   ├── tsconfig.json               # TypeScript configuration
│   ├── eslint.config.js            # ESLint configuration
│   └── postcss.config.js           # PostCSS configuration
├── backend/
│   ├── app.py                      # FastAPI backend server
│   ├── requirements.txt            # Python dependencies
│   └── .env.example                # Environment variables example
└── README.md                       # This file
```

## Installation & Setup

### Prerequisites

- Node.js (v18 or higher)
- Python (v3.8 or higher)
- npm or yarn

### Frontend Setup

1. **Navigate to frontend directory**:

   ```bash
   cd frontend
   ```

2. **Install dependencies**:

   ```bash
   npm install
   ```

3. **Start the development server**:

   ```bash
   npm run dev
   ```

4. **Or start with Turbopack (faster)**:

   ```bash
   npx next dev --turbo
   ```

5. **Access the application**:
   Open [http://localhost:3000](http://localhost:3000) in your browser

### Backend Setup

1. **Navigate to backend directory**:

   ```bash
   cd backend
   ```

2. **Install Python dependencies**:

   ```bash
   pip install fastapi uvicorn httpx pydantic python-dotenv
   ```

   Or install from requirements.txt:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables** (optional):

   ```bash
   cp .env.example .env
   # Edit .env and add your Pipedream webhook URL
   ```

4. **Start the FastAPI server**:

   ```bash
   uvicorn app:app --reload
   ```

5. **Access the API**:
   - API: [http://localhost:8000](http://localhost:8000)
   - API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Quick Start Commands

### Frontend:

```bash
cd frontend
npm install && npm run dev
```

### Frontend with Turbopack (Faster):

```bash
cd frontend
npm install && npx next dev --turbo
```

### Backend:

```bash
cd backend
pip install fastapi uvicorn && uvicorn app:app --reload
```

## Next.js 15.3 Features

### 🚀 Turbopack Support

- **Development**: Use `npx next dev --turbo` for faster compilation
- **Builds**: Use `npx next build --turbo` for faster production builds (alpha)
- **Performance**: Up to 60% faster builds with multi-core scaling

### ⚡ Performance Optimizations

- **Package Optimization**: Automatic optimization for `lucide-react` and chart libraries
- **Image Optimization**: WebP and AVIF support with intelligent caching
- **Bundle Optimization**: Improved code splitting and tree shaking

### 🎯 Developer Experience

- **TypeScript Plugin**: 60% faster IDE performance for large codebases
- **ESLint Integration**: Enhanced linting with Next.js 15.3 rules
- **Error Handling**: Improved error messages and debugging

## API Endpoints

### GET `/api/data`

Returns dummy financial data for dashboard visualization.

**Response:**

```json
{
  "revenue": [
    {"month": "Jan", "revenue": 45000},
    {"month": "Feb", "revenue": 52000},
    ...
  ],
  "expenses": [
    {"category": "Office Rent", "amount": 25000},
    {"category": "Marketing", "amount": 15000},
    ...
  ]
}
```

### POST `/api/find-office`

Forwards office search requests to Pipedream webhook for processing.

**Request:**

```json
{
  "currentExpenses": [...],
  "budget": 50000,
  "location": "downtown"
}
```

**Response:**

```json
{
  "message": "Found 3 cheaper office options in downtown area",
  "results": [...],
  "totalSavings": 15000,
  "status": "success"
}
```

## Modular Analytics Components

### Import Individual Components

```typescript
import { StatsCard } from "../components/analytics";
import { RevenueChart } from "../components/analytics";
import { ExpensesChart } from "../components/analytics";
import { BusinessOptimization } from "../components/analytics";
```

### Or Import All at Once

```typescript
import {
	StatsCard,
	RevenueChart,
	ExpensesChart,
	BusinessOptimization,
} from "../components/analytics";
```

## Pipedream Integration

### Setup Pipedream Webhook

1. **Create a Pipedream account** at [pipedream.com](https://pipedream.com)
2. **Create a new HTTP trigger workflow**
3. **Copy the webhook URL** from your Pipedream workflow
4. **Set the environment variable** in `backend/.env`:
   ```bash
   PIPEDREAM_WEBHOOK_URL="https://your-webhook-url.m.pipedream.net"
   ```

### Sample Pipedream Workflow

The `/api/find-office` endpoint sends structured data to Pipedream, which can:

- Process office search requests
- Integrate with real estate APIs
- Send notifications via email/Slack
- Store results in databases
- Trigger other automation workflows

## Development

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Start with Turbopack (faster)
npx next dev --turbo

# Build for production
npm run build

# Build with Turbopack (faster)
npx next build --turbo

# Start production server
npm start
```

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Start development server with auto-reload
uvicorn app:app --reload

# Run with custom host/port
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Features Overview

### 📊 Dashboard Analytics

- **Revenue Tracking**: Monthly revenue visualization with trend analysis
- **Expense Management**: Categorical expense breakdown and analysis
- **Profit Calculation**: Real-time profit/loss calculations
- **Interactive Charts**: Hover effects, tooltips, and responsive design

### 🏢 Office Optimization

- **Smart Search**: AI-powered office space recommendations
- **Cost Analysis**: Automatic savings calculations
- **Location Filtering**: Search by preferred locations
- **Budget Management**: Find options within budget constraints

### 🎨 UI/UX Features

- **TailAdmin Design**: Premium dashboard aesthetics
- **Dark/Light Mode**: Consistent color scheme
- **Responsive Layout**: Mobile-first design approach
- **Loading States**: Smooth user experience with loading indicators
- **Error Handling**: Graceful error messages and retry options

## Customization

### Adding New Charts

1. Import chart components from `apexcharts`
2. Add data processing logic in `frontend/components/analytics/`
3. Style with Tailwind CSS classes
4. Update API endpoints if needed

### Modifying Styles

1. Edit `frontend/tailwind.config.js` for theme customization
2. Update `frontend/styles/globals.css` for global styles
3. Use TailAdmin color palette for consistency

### Extending API

1. Add new routes in `backend/app.py`
2. Create Pydantic models for data validation
3. Update frontend API calls accordingly

## Deployment

### Frontend (Vercel)

```bash
cd frontend
npm run build
# Deploy to Vercel or similar platform
```

### Backend (Railway/Heroku)

```bash
cd backend
# Create Procfile
echo "web: uvicorn app:app --host 0.0.0.0 --port \$PORT" > Procfile
# Deploy to Railway, Heroku, or similar platform
```

## Performance

### Next.js 15.3 Optimizations

- **Turbopack**: Up to 60% faster builds
- **React 19**: Improved rendering performance
- **Image Optimization**: WebP/AVIF support
- **Bundle Splitting**: Optimized code delivery

### TailAdmin Performance

- **Modular Components**: Load only what you need
- **ApexCharts**: High-performance data visualization
- **Lazy Loading**: Components load on demand
- **Caching**: Intelligent data and asset caching

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the development team.

---

**Built with ❤️ using Next.js 15.3, React 19, FastAPI, and TailAdmin**
