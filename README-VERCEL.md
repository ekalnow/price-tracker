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
- `DATABASE_URL`: Connection string for your database (if using an external database)
- `API_KEY`: A secure random string for authenticating API calls
- `FLASK_ENV`: Set to `production`
- `LOG_LEVEL`: Set to `INFO` (or `DEBUG` for troubleshooting)

## Python 3.12 Compatibility

This application has been optimized to work with Python 3.12 on Vercel. The following changes were made:

1. **Removed aiohttp dependency**: The `aiohttp` package has compatibility issues with Python 3.12, so it has been removed.
2. **Synchronous requests only**: All HTTP requests now use the synchronous `requests` library instead of `aiohttp`.
3. **Simplified background tasks**: The background task system has been modified to work in a serverless environment.
4. **Fixed werkzeug version**: Added a specific version of werkzeug (2.3.7) that is compatible with Flask-Login.
5. **Added email_validator**: Added the email_validator package required by Flask-WTF for form validation.

These changes ensure that the application can be deployed successfully on Vercel's serverless platform.

## Important Notes for Serverless Deployment

### Database Considerations

In a serverless environment like Vercel, you cannot reliably use a file-based SQLite database since the filesystem is ephemeral. Consider using:

1. An in-memory SQLite database (for testing only, data will be lost between invocations)
2. A managed database service like:
   - [Supabase PostgreSQL](https://supabase.io/) (recommended)
   - [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - [AWS RDS](https://aws.amazon.com/rds/)
   
Update your `DATABASE_URL` environment variable accordingly.

#### Supabase Setup

This application has been configured to work with Supabase PostgreSQL. To set up:

1. Create a Supabase account and project at [https://supabase.com](https://supabase.com)
2. Get your connection string from the Supabase dashboard
3. Set the `DATABASE_URL` environment variable in Vercel to your Supabase PostgreSQL connection string:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xkzlhjsvptjqpouaqqtx.supabase.co:5432/postgres
   ```
4. Replace `[YOUR-PASSWORD]` with your actual database password

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
