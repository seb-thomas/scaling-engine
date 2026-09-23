// Server-side rendering errors → PostHog error tracking. Called from the 500
// page, which Astro renders with the error for any exception thrown while
// rendering. Server-only: nothing here reaches the browser.
import { PostHog } from 'posthog-node'
import { POSTHOG_KEY } from './analytics'

let client: PostHog | undefined

export async function reportServerError(error: unknown, url: URL) {
  if (!import.meta.env.PROD || !POSTHOG_KEY) return
  client ??= new PostHog(POSTHOG_KEY, { host: 'https://eu.i.posthog.com', flushAt: 1, flushInterval: 0 })
  // Don't hold the error page up for long if PostHog is slow
  const timeout = new Promise((resolve) => setTimeout(resolve, 2000))
  try {
    await Promise.race([
      client.captureExceptionImmediate(error, undefined, {
        service: 'frontend',
        $current_url: url.href,
        $pathname: url.pathname,
        $process_person_profile: false,
      }),
      timeout,
    ])
  } catch {
    // Reporting must never break the error page
  }
}
