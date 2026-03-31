/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    formats: ["image/avif", "image/webp"],
    remotePatterns: [
      {
        protocol: "https",
        hostname: "uniforma.livosys.se",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "api.uniforma.livosys.se",
        pathname: "/uploads/**",
      },
      {
        protocol: "https",
        hostname: "api.uniforma.livosys.se",
        pathname: "/media/**",
      },
      {
        protocol: "https",
        hostname: "image-pim.cottongroup.org",
        pathname: "/**",
      },
      {
        protocol: "http",
        hostname: "image-pim.cottongroup.org",
        pathname: "/**",
      },
    ],
  },
};

module.exports = nextConfig;
