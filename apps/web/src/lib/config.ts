// Matches apps/api/app/core/config.py's Settings.demo_business_slug default,
// and apps/api/app/seed.py which seeds exactly this business.
export const DEMO_BUSINESS_SLUG = import.meta.env.VITE_DEMO_BUSINESS_SLUG ?? 'atelier'
