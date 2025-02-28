# Deploying the E-commerce Price Monitor on Vercel

This guide provides detailed step-by-step instructions for deploying the E-commerce Price Monitor application on Vercel.

## Prerequisites

1. [Vercel](https://vercel.com/) account
2. [GitHub](https://github.com/) account
3. Your project code pushed to a GitHub repository

## Steps for Deployment

### 1. Prepare Your Project

The project has already been prepared for Vercel deployment with:
- `vercel.json` configuration file
- `api/index.py` serverless entry point
- Modified app.py to handle serverless environments

### 2. Set Up Vercel

1. Log in to your [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Add New** > **Project**
3. Import your GitHub repository containing the E-commerce Price Monitor code
4. Configure your project settings:
   - **Framework Preset**: Other
   - Leave other settings at their defaults

### 3. Configure Environment Variables

Click on **Environment Variables** and add the following:

| Name | Value | Description |
|------|-------|-------------|
| `SECRET_KEY` | `[generate a random string]` | Used for session security |
| `DATABASE_URL` | `[your database connection string]` | If using an external database |
| `API_KEY` | `[generate a random API key]` | For authenticating scheduled API calls |
| `FLASK_ENV` | `production` | Set to production mode |
| `LOG_LEVEL` | `INFO` | Logging level |

### 4. Deploy Your Project

Click **Deploy** and wait for the build to complete.

## Setting Up Scheduled Updates (Price Monitoring)

Since Vercel doesn't support persistent background tasks, we need to set up external scheduled calls to update prices.

### Option 1: GitHub Actions (Recommended)

The repository already includes a GitHub Action workflow file at `.github/workflows/update-prices.yml`.

1. Go to your GitHub repository
2. Click on **Settings** > **Secrets and variables** > **Actions**
3. Add the following repository secrets:
   - `API_KEY`: The same API key you set in Vercel
   - `APP_URL`: Your Vercel deployment URL (e.g., `https://your-app.vercel.app`)

This will run the price update job every 12 hours.

### Option 2: Vercel Cron Jobs (Alternative)

Vercel now offers [cron jobs](https://vercel.com/docs/cron-jobs) for scheduled functions.

1. Create a file `api/cron.js` in your project
2. Add your API call logic
3. Configure the cron job in your Vercel dashboard

## Database Considerations

### Option 1: In-memory SQLite (Development Only)

This works for testing but **data will be lost** after each function invocation.

### Option 2: External Database (Recommended)

For production, use a managed database service:

1. [Supabase Postgres](https://supabase.com/database)
2. [PlanetScale MySQL](https://planetscale.com/)
3. [MongoDB Atlas](https://www.mongodb.com/atlas/database)

Then update your `DATABASE_URL` environment variable to point to your database.

## Testing Your Deployment

1. Visit your deployed application URL
2. Register a new account and log in
3. Add a product URL to track
4. Check that the application is working correctly

## Common Issues and Troubleshooting

### Cold Starts

Serverless functions have "cold starts" which may cause the first request to be slow. Subsequent requests will be faster.

### Database Connection Issues

If using an external database, ensure:
1. The connection string is correct
2. Network access is properly configured
3. Required SSL certificates are in place if needed

### Static Files Access

If you encounter issues with static files:
1. Make sure your templates reference them with the correct paths
2. Check that Vercel is properly serving your static files

## Monitoring and Logs

1. In your Vercel dashboard, go to the **Deployments** tab
2. Click on your latest deployment
3. Select **Functions** to see your serverless function performance
4. Click **View Logs** to see application logs for debugging

## Scaling Considerations

For higher traffic applications, consider:
1. Adding caching (e.g., Redis or Vercel Edge Caching)
2. Optimizing database queries
3. Implementing rate limiting for scraping to avoid IP bans
