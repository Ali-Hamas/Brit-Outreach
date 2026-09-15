import "./globals.css";
export const metadata = { title: "TalentBridge Workspace", description: "Secure workspace for employers & engineers" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 min-w-[1024px]">{children}</body>
    </html>
  );
}
