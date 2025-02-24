/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  // Suppress specific warnings
  onDemandEntries: {
    // Keep pages in memory for longer during development
    maxInactiveAge: 25 * 1000,
    // Number of pages to keep in memory
    pagesBufferLength: 2,
  },
  // Disable static generation warnings
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  devIndicators: {
    buildActivity: false,
    buildActivityPosition: "bottom-right",
  },
}

module.exports = nextConfig