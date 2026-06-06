/** @type {import('next').NextConfig} */
const nextConfig = {
  // Skip type checking and linting during build — handled in CI separately
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  },
  reactStrictMode: true,
};

export default nextConfig;
