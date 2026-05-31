import "./globals.css";

export const metadata = {
  title: "GenPark Social Shopping Agent",
  description:
    "A social shopping operator that turns intent into a saved shortlist and an approval-gated community post.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
