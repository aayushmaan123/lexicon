import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Sidebar() {
  return (
    <aside className="sticky top-16 h-[calc(100vh-4rem)] w-64 border-r bg-muted/40 p-6">
      <nav className="space-y-2">
        <Link href="/dashboard">
          <Button variant="ghost" className="w-full justify-start">
            Dashboard
          </Button>
        </Link>
        <Link href="/dashboard/search">
          <Button variant="ghost" className="w-full justify-start">
            Search
          </Button>
        </Link>
        <Link href="/dashboard/saved">
          <Button variant="ghost" className="w-full justify-start">
            Saved Documents
          </Button>
        </Link>
        <Link href="/dashboard/history">
          <Button variant="ghost" className="w-full justify-start">
            Search History
          </Button>
        </Link>
        <div className="my-4 border-t" />
        <Link href="/dashboard/settings">
          <Button variant="ghost" className="w-full justify-start">
            Settings
          </Button>
        </Link>
      </nav>
    </aside>
  );
}
