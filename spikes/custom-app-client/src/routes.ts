import { Activity } from "lucide-react";

export interface RouteItem {
  title: string;
  path: string;
  icon?: any;
  children?: RouteItem[];
}

export const routes: RouteItem[] = [{ title: "P1 實測", path: "/", icon: Activity }];
