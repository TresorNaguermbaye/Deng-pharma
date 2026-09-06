"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";

export default function InvoiceVerificationPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"loading" | "valid" | "invalid">("loading");
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const verifyInvoice = async () => {
      try {
        const response = await fetch(`/api/sales/verify/${params.id}/?sign=${searchParams.get('sign')}`);
        const result = await response.json();
        setData(result);
        setStatus(result.valid ? "valid" : "invalid");
      } catch (error) {
        setStatus("invalid");
      }
    };
    verifyInvoice();
  }, [params.id, searchParams]);

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-[#0ABAB5] animate-spin mx-auto" />
          <p className="mt-4 text-slate-500 dark:text-slate-400">Vérification de la facture...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900 p-4">
      <Card className="max-w-md w-full border-0 shadow-xl">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            {status === "valid" ? (
              <CheckCircle className="w-16 h-16 text-green-500" />
            ) : (
              <XCircle className="w-16 h-16 text-red-500" />
            )}
          </div>
          <CardTitle className="text-2xl">
            {status === "valid" ? "✅ Facture authentique" : "❌ Facture invalide"}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {status === "valid" && data && (
            <>
              <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                <p className="text-green-700 dark:text-green-300 text-center">
                  Cette facture est authentique et provient de DENG PHARMA.
                </p>
              </div>
              <div className="border-t border-slate-200 dark:border-slate-700 pt-4 space-y-2">
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  <span className="font-medium">Numéro :</span> #{data.id}
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  <span className="font-medium">Date :</span> {new Date(data.date).toLocaleDateString('fr-FR')}
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  <span className="font-medium">Total :</span> {data.total.toLocaleString('fr-FR')} FCFA
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  <span className="font-medium">Client :</span> {data.customer}
                </p>
              </div>
            </>
          )}
          {status === "invalid" && (
            <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
              <p className="text-red-700 dark:text-red-300 text-center">
                Cette facture n'est pas authentique ou a été modifiée.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}