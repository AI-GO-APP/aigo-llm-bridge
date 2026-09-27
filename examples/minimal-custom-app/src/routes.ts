import { MessageSquare, Laptop } from "lucide-react";

export interface RouteItem {
  title: string;
  path: string;
  icon?: any;
  children?: RouteItem[];
}

export const routes: RouteItem[] = [
  { title: "對話", path: "/", icon: MessageSquare },
  { title: "連接我的電腦", path: "/connect", icon: Laptop },
];
