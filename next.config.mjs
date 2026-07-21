/** @type {import('next').NextConfig} */
const nextConfig = {
  outputFileTracingIncludes: {
    "/*": [
      "./plugins/live-consultant/**/*",
      "./.live-consultant-public-export.json"
    ]
  }
};

export default nextConfig;
