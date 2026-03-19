/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
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
      {
        protocol: "http",
        hostname: "localhost",
        port: "9100",
        pathname: "/uploads/**",
      },
      {
        protocol: "http",
        hostname: "localhost",
        port: "9100",
        pathname: "/media/**",
      },
    ],
  },
};

export default nextConfig;
