import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { AlertTriangle } from 'lucide-react';
import EvidenceViewer from '../components/EvidenceViewer';
import clsx from 'clsx';

const TYPES = ['CORROBORATES', 'CONTRADICTS', 'RECONCILED', 'NEW_FACT'];

export default function RelationshipExplorer() {
  const [activeType, setActiveType] = useState('CORROBORATES');
  const [selectedFact, setSelectedFact] = useState<any>(null);

  const { data: relationships = [], isLoading } = useQuery({
    queryKey: ['relationships', activeType],
    queryFn: async () => {
      const res = await axios.get(`http://localhost:8000/relationships`, { params: { rel_type: activeType } });
      return res.data;
    }
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 bg-white p-2 rounded-lg shadow-sm border border-gray-100">
        {TYPES.map(type => (
          <button
            key={type}
            onClick={() => setActiveType(type)}
            className={clsx(
              "px-4 py-2 rounded-md font-medium text-sm transition-colors flex-1 text-center",
              activeType === type ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100"
            )}
          >
            {type}
          </button>
        ))}
      </div>

      <div className="space-y-6">
        {isLoading ? (
          <div className="text-center py-12 text-gray-500">Loading relationships...</div>
        ) : relationships.length === 0 ? (
          <div className="bg-white p-12 text-center rounded-xl border border-gray-100 text-gray-500">
            No relationships found for type {activeType}.
          </div>
        ) : (
          relationships.map((rel: any) => (
            <div key={rel.id} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-2">
                  <span className={clsx(
                    "px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider",
                    rel.relationship_type === 'CORROBORATES' && "bg-green-100 text-green-700",
                    rel.relationship_type === 'CONTRADICTS' && "bg-red-100 text-red-700",
                    rel.relationship_type === 'RECONCILED' && "bg-yellow-100 text-yellow-700",
                    rel.relationship_type === 'NEW_FACT' && "bg-blue-100 text-blue-700",
                  )}>
                    {rel.relationship_type}
                  </span>
                  {rel.requires_human_review && (
                    <span className="flex items-center gap-1 text-orange-600 text-sm font-medium bg-orange-50 px-2 py-1 rounded">
                      <AlertTriangle size={14} /> Needs Review (Conf: {(rel.confidence * 100).toFixed(0)}%)
                    </span>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                {/* Fact A */}
                <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                  <div className="text-xs text-gray-400 mb-2">{rel.fact_a.document_title}</div>
                  <div className="font-medium text-gray-900 mb-1">{rel.fact_a.subject}</div>
                  <div className="text-sm font-mono text-gray-600 mb-2">{rel.fact_a.predicate}</div>
                  <div className="text-lg font-bold text-gray-900 mb-4">{rel.fact_a.raw_value}</div>
                  <button 
                    onClick={() => setSelectedFact(rel.fact_a)}
                    className="text-blue-600 hover:underline text-sm font-medium"
                  >
                    View Evidence
                  </button>
                </div>

                {/* Fact B */}
                <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                  <div className="text-xs text-gray-400 mb-2">{rel.fact_b.document_title}</div>
                  <div className="font-medium text-gray-900 mb-1">{rel.fact_b.subject}</div>
                  <div className="text-sm font-mono text-gray-600 mb-2">{rel.fact_b.predicate}</div>
                  <div className="text-lg font-bold text-gray-900 mb-4">{rel.fact_b.raw_value}</div>
                  <button 
                    onClick={() => setSelectedFact(rel.fact_b)}
                    className="text-blue-600 hover:underline text-sm font-medium"
                  >
                    View Evidence
                  </button>
                </div>
              </div>

              {rel.reasoning && (
                <div className="mt-4 p-4 bg-blue-50 border border-blue-100 rounded-lg text-sm text-blue-900">
                  <strong className="block mb-1">AI Reasoning:</strong>
                  {rel.reasoning}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {selectedFact && <EvidenceViewer fact={selectedFact} onClose={() => setSelectedFact(null)} />}
    </div>
  );
}
