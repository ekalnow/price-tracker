# Deploying to Vercel

This guide explains how to deploy the E-commerce Price Monitor application to Vercel.

## Prerequisites

1. A [Vercel](https://vercel.com/) account
2. [Vercel CLI](https://vercel.com/docs/cli) installed (optional for local testing)

## Deployment Steps

### 1. Fork or Clone this Repository

Make sure you have a copy of this repository in your GitHub account.

### 2. Connect to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your GitHub repository
4. Configure the project:
   - Framework Preset: Other
   - Root Directory: `./`
   - Build Command: None (leave empty)
   - Output Directory: None (leave empty)

### 3. Environment Variables

Add the following environment variables in the Vercel project settings:

- `SECRET_KEY`: A secure random string for session encryption
- `DATABASE_URL`: If using an external database, add the connection string here
- `FLASK_ENV`: Set to `production`
- `LOG_LEVEL`: Set to `INFO` or `WARNING` for production

### 4. Deploy

Click "Deploy" and wait for the deployment to complete.

## Important Notes for Serverless Deployment

### Database Considerations

In a serverless environment like Vercel, you cannot reliably use a file-based SQLite database since the filesystem is ephemeral. Consider using:

1. An in-memory SQLite database (for testing only, data will be lost between invocations)
2. A managed database service like:
   - [Supabase PostgreSQL](https://supabase.io/)
   - [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - [AWS RDS](https://aws.amazon.com/rds/)
   
Update your `DATABASE_URL` environment variable accordingly.

### Scheduled Tasks

Vercel's serverless functions are stateless and don't support continuous background processes. For the price update scheduler:

1. Create a separate scheduled function using [Vercel Cron Jobs](https://vercel.com/docs/cron-jobs)
2. Or use a service like [GitHub Actions](https://github.com/features/actions) to periodically call your price update endpoint

### Static Files

Vercel handles static files differently. Make sure your templates reference static files correctly.

## Testing Locally

To test the Vercel deployment locally:

1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel dev` in the project directory

## Troubleshooting

If you encounter issues:

1. Check Vercel deployment logs in the dashboard
2. Ensure all dependencies are correctly listed in `api/requirements.txt`
3. Verify environment variables are set correctly
4. Try deploying a simpler Flask application first to ensure your setup is correct
