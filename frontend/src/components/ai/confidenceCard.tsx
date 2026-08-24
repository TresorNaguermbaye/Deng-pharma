"use client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface MetricSet {
  mae?: number;
  rmse?: number;
  mape?: number;
  r2?: number;
}

interface ModelPerformance {
  test?: MetricSet;
  validation?: MetricSet;
  model_version?: string;
  trained_at?: string;
  n_train?: number;
  n_val?: number;
  n_test?: number;
}

export default function ConfidenceCard({ data }: { data: ModelPerformance | null }) {
  if (!data) return <p>Chargement...</p>;

  const renderMetrics = (metrics: MetricSet) => (
    <div className="space-y-2">
      <p>MAE : {metrics.mae?.toFixed(2)}</p>
      <p>RMSE : {metrics.rmse?.toFixed(2)}</p>
      <p>MAPE : {metrics.mape?.toFixed(2)}%</p>
      <p>R² : {metrics.r2?.toFixed(3)}</p>
    </div>
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Indice de confiance</CardTitle>
        <CardDescription>Performances du modèle (version {data.model_version})</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="test">
          <TabsList>
            <TabsTrigger value="test">Test</TabsTrigger>
            <TabsTrigger value="validation">Validation</TabsTrigger>
          </TabsList>
          <TabsContent value="test">
            {data.test ? renderMetrics(data.test) : <p>Pas de métriques test.</p>}
          </TabsContent>
          <TabsContent value="validation">
            {data.validation ? renderMetrics(data.validation) : <p>Pas de métriques validation.</p>}
          </TabsContent>
        </Tabs>
        <div className="mt-4 text-xs text-slate-500">
          <p>Entraîné le : {data.trained_at}</p>
          <p>Données : {data.n_train} train / {data.n_val} val / {data.n_test} test</p>
        </div>
      </CardContent>
    </Card>
  );
}