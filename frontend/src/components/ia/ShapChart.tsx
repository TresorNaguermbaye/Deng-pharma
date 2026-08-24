"use client";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

interface ShapData {
  features?: { name: string; importance: number }[];
}

export default function ShapChart({ data }: { data: ShapData | null }) {
  if (!data) return <p className="text-muted-foreground">Aucune donnée SHAP disponible.</p>;
  if (data.error) return <p className="text-red-500">Erreur : {data.error}</p>;
  if (!data.features || data.features.length === 0) return <p className="text-muted-foreground">Aucune donnée SHAP disponible.</p>;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data.features} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" />
        <YAxis dataKey="name" type="category" width={150} />
        <Tooltip />
        <Legend />
        <Bar dataKey="importance" fill="#0F1A2C" />
      </BarChart>
    </ResponsiveContainer>
  );
}
